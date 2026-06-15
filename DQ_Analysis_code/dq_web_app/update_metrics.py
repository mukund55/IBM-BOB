"""Update metrics for existing DQ run"""
from app import create_app
from models.models import db, DQRun
import pandas as pd
import os

app = create_app()

with app.app_context():
    # Get the run
    run = DQRun.query.filter_by(run_id='fdf3495b').first()
    if run:
        # Read summary file
        summary_file = os.path.join('reports', 'fdf3495b', 'dq_summary.csv')
        if os.path.exists(summary_file):
            summary_df = pd.read_csv(summary_file)
            metrics = dict(zip(summary_df['metric'], summary_df['value']))
            
            # Update run
            run.dq_score = float(metrics.get('quality_score', 0))
            run.total_records = int(metrics.get('row_count', 0))
            run.total_columns = int(metrics.get('column_count', 0))
            
            db.session.commit()
            print(f'Updated run {run.run_id}:')
            print(f'  DQ Score: {run.dq_score}')
            print(f'  Total Records: {run.total_records}')
            print(f'  Total Columns: {run.total_columns}')
        else:
            print('Summary file not found')
    else:
        print('Run not found')

# Made with Bob
