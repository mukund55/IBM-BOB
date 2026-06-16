# Ab Initio Code Analyzer - Web Application

A user-friendly web interface for analyzing Ab Initio code files (.mp, .plan, .log) with automatic dashboard generation.

## Features

- 🎯 **Drag & Drop Interface**: Simply drag and drop your Ab Initio files
- 📊 **Instant Analysis**: Automated code analysis based on 60-point checklist
- 🎨 **Interactive Dashboards**: Beautiful HTML dashboards with detailed insights
- 📁 **File Management**: Automatic file organization and storage
- 🔍 **Recent Dashboards**: Quick access to previously analyzed files
- 💯 **Optimization Scores**: Get immediate feedback on code quality

## Supported File Types

- `.mp` - Ab Initio Metadata (MP) files
- `.plan` - Ab Initio Plan files
- `.log` - Ab Initio Log files

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Navigate to the Performance_Optimization directory:
```bash
cd Performance_Optimization
```

2. Install required dependencies:
```bash
pip install -r requirements_web.txt
```

## Starting the Application

### Windows (Command Prompt)

Double-click `start_web_analyzer.bat` or run:
```cmd
start_web_analyzer.bat
```

### Windows (PowerShell)

Run:
```powershell
.\start_web_analyzer.ps1
```

### Manual Start

```bash
python web_analyzer_app.py
```

## Using the Application

1. **Start the Server**: Run one of the startup scripts above
2. **Open Browser**: Navigate to `http://localhost:5000`
3. **Upload File**: 
   - Drag and drop your Ab Initio file onto the upload area, OR
   - Click the upload area to browse and select a file
4. **Analyze**: Click the "Analyze File" button
5. **View Results**: 
   - See optimization score and issue summary
   - Click "View Dashboard" to open the detailed analysis
6. **Access History**: Scroll down to see all previously generated dashboards

## Application Structure

```
Performance_Optimization/
├── web_analyzer_app.py          # Flask web application
├── templates/
│   └── index.html               # Web UI template
├── Abinitio_code/               # Uploaded files stored here
├── Dashboards/                  # Generated dashboards
├── Agents/                      # Analysis scripts
│   ├── abinitio_mp_analyzer_enhanced.py
│   ├── abinitio_plan_analyzer.py
│   ├── abinitio_log_analyzer.py
│   └── generate_dashboard.py
├── requirements_web.txt         # Python dependencies
├── start_web_analyzer.bat       # Windows batch startup
└── start_web_analyzer.ps1       # PowerShell startup
```

## How It Works

1. **File Upload**: User uploads an Ab Initio file through the web interface
2. **Storage**: File is saved to `Abinitio_code/` directory
3. **Analysis**: Appropriate analyzer script runs based on file type:
   - `.mp` files → `abinitio_mp_analyzer_enhanced.py`
   - `.plan` files → `abinitio_plan_analyzer.py`
   - `.log` files → `abinitio_log_analyzer.py`
4. **JSON Generation**: Analysis results saved as JSON
5. **Dashboard Creation**: `generate_dashboard.py` creates interactive HTML dashboard
6. **Display**: Results shown in web UI with link to full dashboard

## Analysis Features

### For MP Files (60-Point Checklist)
- Graph Architecture & Design
- Metadata & DML Standards
- Partitioning Strategy
- Sort Optimization
- Join Optimization
- Rollup & Aggregation
- Transform & PDL Coding
- Memory & Resource Usage
- File Handling
- Error Handling & Recovery
- Production Readiness

### For Plan Files
- Naming Conventions
- Hardcoded Paths Detection
- Partition Configuration
- Sort Optimization
- Join Optimization
- Component Type Validation
- DML References
- Flow Efficiency
- Error Handling
- Documentation Quality

### For Log Files
- Error Detection & Analysis
- Root Cause Identification
- Failed Component Analysis
- Performance Metrics
- Validation Issues

## Dashboard Features

Each generated dashboard includes:
- **Optimization Score**: 0-100 rating
- **Component Analysis**: Detailed breakdown of all components
- **Issue Categorization**: Critical, High, Medium, Low, Info
- **Filterable Views**: Filter issues by severity
- **Actionable Recommendations**: Specific guidance for improvements
- **Visual Analytics**: Charts and graphs for quick insights

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify `web_analyzer_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Flask Not Found
Install Flask manually:
```bash
pip install Flask==3.0.0 Werkzeug==3.0.1
```

### File Upload Fails
- Check file size (max 16MB)
- Verify file extension (.mp, .plan, or .log)
- Ensure write permissions in Abinitio_code directory

### Analysis Fails
- Verify Python is in system PATH
- Check that all analyzer scripts are present in Agents/ directory
- Review console output for specific error messages

## Configuration

### Change Upload Size Limit
Edit `web_analyzer_app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
```

### Change Server Port
Edit `web_analyzer_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Custom port
```

### Enable External Access
To allow access from other machines on your network:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```
Then access via: `http://YOUR_IP_ADDRESS:5000`

## Security Notes

- This application is designed for **local use only**
- Do not expose to the internet without proper security measures
- File uploads are not validated beyond extension checking
- Consider adding authentication for production use

## API Endpoints

### POST /upload
Upload and analyze a file
- **Body**: multipart/form-data with 'file' field
- **Returns**: JSON with analysis results

### GET /dashboard/<filename>
View a generated dashboard
- **Returns**: HTML dashboard

### GET /list-dashboards
List all available dashboards
- **Returns**: JSON array of dashboard metadata

## Tips for Best Results

1. **File Naming**: Use descriptive names for uploaded files
2. **Regular Analysis**: Analyze code during development, not just at the end
3. **Review Dashboards**: Take time to review all recommendations
4. **Track Progress**: Use the dashboard history to track improvements
5. **Share Results**: Dashboards can be shared with team members

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review console output for error messages
3. Verify all dependencies are installed
4. Ensure file permissions are correct

## Version History

- **v1.0** - Initial release with drag-drop UI, automatic analysis, and dashboard generation

---

**Made with Bob** 🤖