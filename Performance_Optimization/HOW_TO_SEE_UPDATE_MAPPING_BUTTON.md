# How to See the "Update Mapping" Button

## 📍 Button Location

The **"🔄 Update Mapping"** button appears in the **Results Section** after you upload and analyze a file.

## 🔍 Step-by-Step Guide to See the Button

### Step 1: Start the Application
```bash
cd Performance_Optimization
start_web_analyzer.bat
```

### Step 2: Open Browser
Navigate to: `http://localhost:5000`

### Step 3: Upload a File
1. Drag and drop an Ab Initio file (.mp or .plan) onto the upload area
2. OR click the upload area to browse and select a file
3. Click the **"Analyze File"** button

### Step 4: Wait for Analysis
- The system will analyze your code
- A loading spinner will appear
- This takes a few seconds

### Step 5: View Results
After analysis completes, you'll see:
- **Optimization Score** (e.g., 75/100)
- **Graph Name**
- **Issue Summary** (Critical, High, Medium, Low, Info counts)

### Step 6: Find the Button
Scroll down to the **Action Buttons** section. You'll see:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  [View Dashboard]  [🔄 Update Mapping]                 │
│                                                         │
│  [Download Optimized Code]  [Download Report]          │
│                                                         │
│  [Analyze Another File]                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The **"🔄 Update Mapping"** button will be:
- **GREEN** colored (different from other buttons)
- Located between "View Dashboard" and "Download Optimized Code"
- Only visible if optimizations are available

## ⚠️ Why You Might Not See It

### Reason 1: No File Uploaded Yet
**Solution:** Upload and analyze a file first

### Reason 2: Analysis Not Complete
**Solution:** Wait for the analysis to finish (loading spinner disappears)

### Reason 3: No Optimizations Available
**Solution:** The code might already be optimized. Check the analysis results.

### Reason 4: File Type Not Supported
**Solution:** Only .mp and .plan files support optimization (not .log files)

## 🎯 Visual Guide

### Before Upload:
```
┌──────────────────────────────────┐
│   📁 Drop your file here         │
│   or click to browse             │
│                                  │
│   [Analyze File] (disabled)      │
└──────────────────────────────────┘
```

### After Upload & Analysis:
```
┌──────────────────────────────────────────────────┐
│  Graph Name: inmemory_total_sales_by_store       │
│  Score: 75/100                                   │
│                                                  │
│  Critical: 0  High: 2  Medium: 3  Low: 1        │
│                                                  │
│  ┌────────────────┐  ┌──────────────────────┐  │
│  │ View Dashboard │  │ 🔄 Update Mapping    │  │ ← HERE!
│  └────────────────┘  └──────────────────────┘  │
│                                                  │
│  ┌──────────────────────┐  ┌─────────────────┐ │
│  │ Download Optimized   │  │ Download Report │ │
│  └──────────────────────┘  └─────────────────┘ │
│                                                  │
│  ┌──────────────────────┐                       │
│  │ Analyze Another File │                       │
│  └──────────────────────┘                       │
└──────────────────────────────────────────────────┘
```

## 🧪 Test with Sample File

Try with an existing file:
```bash
# Use one of these sample files
Performance_Optimization/Abinitio_code/inmemory_total_sales_by_store.mp
Performance_Optimization/Abinitio_code/casting_join_keys.mp
Performance_Optimization/Abinitio_code/sample_customer.plan
```

## 🔧 Troubleshooting

### Button Still Not Visible?

1. **Check Browser Console** (F12):
   - Look for JavaScript errors
   - Check if `optimizedFile` variable is set

2. **Verify File Upload**:
   - Check if file appears in `Performance_Optimization/Abinitio_code/`
   - Check if analysis JSON was created

3. **Check Analysis Results**:
   - Look for `*_analysis.json` file
   - Verify it contains `optimized_file` field

4. **Restart Application**:
   ```bash
   # Stop the server (Ctrl+C)
   # Start again
   start_web_analyzer.bat
   ```

5. **Clear Browser Cache**:
   - Press Ctrl+Shift+R (hard refresh)
   - Or clear browser cache completely

## 📸 Screenshot Reference

The button should look like this:

```
╔═══════════════════════════════════╗
║  🔄 Update Mapping                ║  ← Green button
╚═══════════════════════════════════╝
```

**Color:** Green gradient background
**Icon:** 🔄 (refresh/update icon)
**Text:** "Update Mapping"
**Position:** Second button in the action buttons row

## 💡 Quick Test

Run this in browser console (F12) after analysis:
```javascript
// Check if button exists
console.log(document.getElementById('updateMapping'));

// Check if optimized file is set
console.log(optimizedFile);

// Manually show button (for testing)
document.getElementById('updateMapping').style.display = 'inline-block';
```

## 📞 Still Having Issues?

If you still can't see the button:

1. **Check the HTML file** is updated:
   - Open `Performance_Optimization/templates/index.html`
   - Search for "updateMapping"
   - Should find the button definition

2. **Check the Python file** is updated:
   - Open `Performance_Optimization/web_analyzer_app.py`
   - Search for "update-mapping"
   - Should find the API endpoint

3. **Verify files were saved**:
   - Both files should have recent modification dates
   - Restart the web server after any changes

## ✅ Success Indicators

You'll know it's working when:
1. ✓ File uploads successfully
2. ✓ Analysis completes (score appears)
3. ✓ Green "🔄 Update Mapping" button appears
4. ✓ Clicking it shows confirmation dialog
5. ✓ After confirming, success message appears

---

**Remember:** The button only appears AFTER uploading and analyzing a file that has optimization opportunities!