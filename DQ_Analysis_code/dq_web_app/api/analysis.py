"""
Enterprise Data Quality Platform - Analysis API
Integrates with data_quality_analysis.py script
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import sys
import uuid
import subprocess
import json
from datetime import datetime

# Add parent directory to path to import data_quality_analysis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.models import db, DQRun, DQMetric, DQAnomaly

analysis_bp = Blueprint('analysis', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt', 'dat'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@analysis_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload and trigger DQ analysis"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: CSV, XLSX, XLS, TXT, DAT'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        run_id = str(uuid.uuid4())[:8]
        
        # Save file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, f"{run_id}_{filename}")
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Create DQ run record
        dq_run = DQRun(
            run_id=run_id,
            user_id=current_user.id,
            dataset_name=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            status='running'
        )
        db.session.add(dq_run)
        db.session.commit()
        
        # Run DQ analysis
        output_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Path to data_quality_analysis.py
        dq_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data_quality_analysis.py'
        )
        
        # Run the analysis script with automatic data cleansing
        cmd = [
            sys.executable,
            dq_script,
            '--input', file_path,
            '--output-dir', output_dir,
            '--cleanse-data'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Parse results
            summary_file = os.path.join(output_dir, 'dq_summary.csv')
            dashboard_file = os.path.join(output_dir, 'dq_executive_dashboard.html')
            
            # Read DQ score from summary
            dq_score = None
            total_records = None
            total_columns = None
            
            if os.path.exists(summary_file):
                import pandas as pd
                summary_df = pd.read_csv(summary_file)
                if not summary_df.empty:
                    # Parse the metric-value format
                    metrics = dict(zip(summary_df['metric'], summary_df['value']))
                    dq_score = float(metrics.get('quality_score', 0))
                    total_records = int(metrics.get('row_count', 0))
                    total_columns = int(metrics.get('column_count', 0))
            
            # Update run record
            dq_run.status = 'completed'
            dq_run.completed_at = datetime.utcnow()
            dq_run.dq_score = dq_score
            dq_run.total_records = total_records
            dq_run.total_columns = total_columns
            dq_run.execution_time = (dq_run.completed_at - dq_run.started_at).total_seconds()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'run_id': run_id,
                'dq_score': float(dq_score) if dq_score else None,
                'total_records': int(total_records) if total_records else None,
                'dashboard_url': url_for('analysis.view_results', run_id=run_id)
            })
        else:
            # Analysis failed
            dq_run.status = 'failed'
            dq_run.error_message = result.stderr
            dq_run.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'error': 'Analysis failed',
                'details': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/results/<run_id>')
@login_required
def view_results(run_id):
    """View DQ analysis results"""
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'danger')
        return redirect(url_for('upload'))
    
    # Check permissions
    if dq_run.user_id != current_user.id and not current_user.has_permission('view_all'):
        flash('Access denied', 'danger')
        return redirect(url_for('upload'))
    
    # Get dashboard HTML
    dashboard_file = os.path.join(
        current_app.config['REPORTS_FOLDER'],
        run_id,
        'dq_executive_dashboard.html'
    )
    
    dashboard_html = None
    if os.path.exists(dashboard_file):
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()
    
    return render_template('results.html',
                         run=dq_run,
                         dashboard_html=dashboard_html)


@analysis_bp.route('/list')
@login_required
def list_analyses():
    """List all DQ analyses"""
    if current_user.has_permission('view_all'):
        runs = DQRun.query.order_by(DQRun.started_at.desc()).all()
    else:
        runs = DQRun.query.filter_by(user_id=current_user.id).order_by(DQRun.started_at.desc()).all()
    
    return jsonify([run.to_dict() for run in runs])


@analysis_bp.route('/status/<run_id>')
@login_required
def get_status(run_id):
    """Get analysis status"""
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        return jsonify({'error': 'Analysis not found'}), 404
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('view_all'):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(dq_run.to_dict())


@analysis_bp.route('/delete/<run_id>', methods=['DELETE'])
@login_required
def delete_analysis(run_id):
    """Delete analysis"""
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        return jsonify({'error': 'Analysis not found'}), 404
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete files

@analysis_bp.route('/recommendations/<run_id>')
@login_required
def view_recommendations(run_id):
    """View only recommendations for a specific analysis"""
    import pandas as pd
    
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Read recommendations CSV
    report_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    recommendations_file = os.path.join(report_dir, 'dq_recommendations.csv')
    
    recommendations = []
    if os.path.exists(recommendations_file):
        df = pd.read_csv(recommendations_file)
        # Filter only rows with count > 0
        df_filtered = df[df['count'] > 0]
        recommendations = df_filtered.to_dict('records')
    
    return render_template('recommendations.html', 
                         run=dq_run, 
                         recommendations=recommendations)


@analysis_bp.route('/visual-reports/<run_id>')
@login_required
def view_visual_reports(run_id):
    """View only visual reports/charts for a specific analysis"""
    import pandas as pd
    
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Read anomaly summary for charts
    report_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    anomaly_file = os.path.join(report_dir, 'dq_anomaly_summary.csv')
    
    anomalies = []
    if os.path.exists(anomaly_file):
        df = pd.read_csv(anomaly_file)
        # Filter only rows with count > 0
        df_filtered = df[df['count'] > 0]
        anomalies = df_filtered.to_dict('records')
    
    return render_template('visual_reports.html', 
                         run=dq_run, 
                         anomalies=anomalies)


@analysis_bp.route('/anomaly-report/<run_id>')
@login_required
def view_anomaly_report(run_id):
    """View only anomaly/data quality issues for a specific analysis"""
    import pandas as pd
    
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'error')
        return redirect(url_for('dashboard'))
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    # Read anomaly summary
    report_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    anomaly_file = os.path.join(report_dir, 'dq_anomaly_summary.csv')
    
    anomalies = []
    total_issues = 0
    if os.path.exists(anomaly_file):
        df = pd.read_csv(anomaly_file)
        # Filter only rows with count > 0
        df_filtered = df[df['count'] > 0].copy()
        
        # Calculate percentage and severity
        total_records = dq_run.total_records if dq_run.total_records else 1
        df_filtered['percentage'] = (df_filtered['count'] / total_records) * 100
        
        # Assign severity based on percentage
        def get_severity(pct):
            if pct >= 10:
                return 'HIGH'
            elif pct >= 5:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        df_filtered['severity'] = df_filtered['percentage'].apply(get_severity)
        df_filtered['issue_type'] = df_filtered['column_name']
        
        anomalies = df_filtered.to_dict('records')
        total_issues = int(df_filtered['count'].sum())
    
    return render_template('anomaly_report.html',
                         run=dq_run,
                         anomalies=anomalies,
                         total_issues=total_issues)


@analysis_bp.route('/cleansed-data/<run_id>')
@login_required
def view_cleansed_data(run_id):
    """View cleansed/good records for a specific analysis"""
    import pandas as pd
    
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Read good records CSV
    report_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    good_records_file = os.path.join(report_dir, 'good_records.csv')
    
    records = []
    columns = []
    total_records = 0
    
    if os.path.exists(good_records_file):
        df = pd.read_csv(good_records_file)
        total_records = len(df)
        columns = df.columns.tolist()
        # Show first 100 records
        records = df.head(100).to_dict('records')
    
    return render_template('cleansed_data.html', 
                         run=dq_run, 
                         records=records,
                         columns=columns,
                         total_records=total_records)


@analysis_bp.route('/download-cleansed/<run_id>')
@login_required
def download_cleansed_data(run_id):
    """Download cleansed data CSV"""
    from flask import send_file
    
    dq_run = DQRun.query.filter_by(run_id=run_id).first()
    
    if not dq_run:
        flash('Analysis not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    if dq_run.user_id != current_user.id and not current_user.has_permission('all'):
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    report_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    good_records_file = os.path.join(report_dir, 'good_records.csv')
    
    if not os.path.exists(good_records_file):
        flash('Cleansed data file not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    return send_file(good_records_file, 
                    as_attachment=True, 
                    download_name=f'cleansed_data_{run_id}.csv')

    if dq_run.file_path and os.path.exists(dq_run.file_path):
        os.remove(dq_run.file_path)
    
    output_dir = os.path.join(current_app.config['REPORTS_FOLDER'], run_id)
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    
    # Delete database record
    db.session.delete(dq_run)
    db.session.commit()
    
    return jsonify({'success': True})

# Made with Bob
