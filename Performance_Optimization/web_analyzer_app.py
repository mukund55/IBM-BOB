#!/usr/bin/env python3
"""
Ab Initio Code Analyzer Web Application
A Flask-based web UI for uploading and analyzing Ab Initio code files
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'Abinitio_code'
app.config['DASHBOARD_FOLDER'] = 'Dashboards'

ALLOWED_EXTENSIONS = {'.mp', '.plan', '.log'}

def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def get_analyzer_script(ext):
    if ext == '.mp':
        return 'Agents/abinitio_mp_analyzer_enhanced.py'
    elif ext == '.plan':
        return 'Agents/abinitio_plan_analyzer.py'
    elif ext == '.log':
        return 'Agents/abinitio_log_analyzer.py'
    return None

def run_analysis(file_path, ext):
    analyzer = get_analyzer_script(ext)
    if not analyzer:
        return None, "Unsupported file type"
    
    base_name = Path(file_path).stem
    output = f"{base_name}_analysis.json"
    
    try:
        cmd = ['python', analyzer, file_path, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        return output, None
    except Exception as e:
        return None, str(e)

def generate_dashboard(analysis_path):
    base = Path(analysis_path).stem.replace('_analysis', '')
    output = f"{base}_dashboard.html"
    dash_path = os.path.join(app.config['DASHBOARD_FOLDER'], output)
    
    try:
        cmd = ['python', 'Agents/generate_dashboard.py', analysis_path, '-o', dash_path]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return dash_path, None
    except Exception as e:
        return None, str(e)

def optimize_code(original_file, analysis_file):
    """Generate optimized version of the code"""
    try:
        cmd = ['python', 'Agents/abinitio_code_optimizer.py', original_file, analysis_file, '--report']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Get optimized file path
        base_name = Path(original_file).stem
        ext = Path(original_file).suffix
        optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_optimized{ext}")
        report_path = optimized_path.replace(ext, '.optimization_report.txt')
        
        return optimized_path, report_path, None
    except Exception as e:
        return None, None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    try:
        filename = secure_filename(file.filename)
        ext = Path(filename).suffix.lower()
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Clean up previous intermediate files for this filename
        base_name = Path(filename).stem
        cleanup_patterns = [
            f"{base_name}_analysis.json",
            f"{base_name}_optimized{ext}",
            f"{base_name}.optimization_report.txt"
        ]
        for pattern in cleanup_patterns:
            cleanup_path = os.path.join(app.config['UPLOAD_FOLDER'], pattern)
            if os.path.exists(cleanup_path):
                os.remove(cleanup_path)
        
        file.save(upload_path)
        
        analysis_path, error = run_analysis(upload_path, ext)
        if error:
            return jsonify({'error': error}), 500
        
        dashboard_path, error = generate_dashboard(analysis_path)
        if error:
            return jsonify({'error': error}), 500
        
        # Generate optimized code
        optimized_path, report_path, opt_error = optimize_code(upload_path, analysis_path)
        
        with open(analysis_path, 'r') as f:
            data = json.load(f)
        
        response_data = {
            'success': True,
            'filename': filename,
            'dashboard_file': os.path.basename(dashboard_path),
            'optimization_score': data.get('optimization_score', 0),
            'graph_name': data.get('graph_name', 'Unknown'),
            'summary': data.get('summary', {})
        }
        
        # Add optimization info if successful
        if optimized_path and os.path.exists(optimized_path):
            response_data['optimized_file'] = os.path.basename(optimized_path)
            response_data['optimization_report'] = os.path.basename(report_path) if report_path else None
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download optimized code or reports"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/update-mapping', methods=['POST'])
def update_mapping():
    """Apply optimizations and create a new versioned file"""
    data = request.get_json()
    original_filename = data.get('filename')
    
    if not original_filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    try:
        import shutil
        from datetime import datetime
        
        # Get file paths
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        base_name = Path(original_filename).stem
        ext = Path(original_filename).suffix
        analysis_path = f"{base_name}_analysis.json"
        
        if not os.path.exists(original_path):
            return jsonify({'error': 'Original file not found'}), 404
        
        if not os.path.exists(analysis_path):
            return jsonify({'error': 'Analysis file not found'}), 404
        
        # Find next version number
        version = 1
        while True:
            versioned_name = f"{base_name}_v{version}{ext}"
            versioned_path = os.path.join(app.config['UPLOAD_FOLDER'], versioned_name)
            if not os.path.exists(versioned_path):
                break
            version += 1
        
        # Run optimizer and get optimized content
        cmd = ['python', 'Agents/abinitio_code_optimizer.py',
               original_path, analysis_path, '--report']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Get the optimized file path
        optimized_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                     f"{base_name}_optimized{ext}")
        
        # Create versioned file instead of overwriting
        if os.path.exists(optimized_path):
            shutil.copy2(optimized_path, versioned_path)
            
            # Clean up intermediate optimized file (keep only versioned file)
            os.remove(optimized_path)
            
            # Read optimization report
            report_path = optimized_path.replace(ext, '.optimization_report.txt')
            optimizations_count = 0
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                    optimizations_count = report_content.count('[SUCCESS]')
            
            # Re-analyze the versioned file to get updated score
            versioned_base = Path(versioned_name).stem
            versioned_analysis_path = f"{versioned_base}_analysis.json"
            versioned_dashboard_path = None
            
            try:
                # Run analysis on versioned file
                if ext == '.mp':
                    analyze_cmd = ['python', 'Agents/abinitio_mp_analyzer_enhanced.py', versioned_path]
                elif ext == '.plan':
                    analyze_cmd = ['python', 'Agents/abinitio_plan_analyzer.py', versioned_path]
                else:
                    analyze_cmd = None
                
                if analyze_cmd:
                    subprocess.run(analyze_cmd, capture_output=True, text=True, check=True)
                    
                    # Generate new dashboard for versioned file
                    dashboard_cmd = ['python', 'Agents/generate_dashboard.py',
                                   versioned_analysis_path,
                                   '--output', app.config['DASHBOARD_FOLDER']]
                    subprocess.run(dashboard_cmd, capture_output=True, text=True, check=True)
                    
                    # Find the generated dashboard
                    versioned_dashboard_path = os.path.join(app.config['DASHBOARD_FOLDER'],
                                                           f"{versioned_base}_dashboard.html")
                    
                    # Read updated score
                    if os.path.exists(versioned_analysis_path):
                        with open(versioned_analysis_path, 'r') as f:
                            analysis_data = json.load(f)
                            updated_score = analysis_data.get('optimization_score', 0)
                    else:
                        updated_score = None
            except Exception as e:
                print(f"Re-analysis failed: {e}")
                updated_score = None
                versioned_dashboard_path = None
            
            return jsonify({
                'success': True,
                'message': f'Created optimized version with {optimizations_count} optimizations',
                'versioned_file': versioned_name,
                'version': version,
                'optimizations_applied': optimizations_count,
                'updated_score': updated_score,
                'dashboard_file': os.path.basename(versioned_dashboard_path) if versioned_dashboard_path else None
            })
        else:
            return jsonify({'error': 'Optimization failed to generate file'}), 500
            
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Optimization failed: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500

@app.route('/dashboard/<filename>')
def view_dashboard(filename):
    path = os.path.join(app.config['DASHBOARD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return jsonify({'error': 'Not found'}), 404

@app.route('/list-dashboards')
def list_dashboards():
    try:
        dashboards = []
        for file in Path(app.config['DASHBOARD_FOLDER']).glob('*.html'):
            stat = file.stat()
            dashboards.append({
                'name': file.name,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify({'dashboards': dashboards})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DASHBOARD_FOLDER'], exist_ok=True)
    print("Starting Ab Initio Code Analyzer Web App on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made with Bob
