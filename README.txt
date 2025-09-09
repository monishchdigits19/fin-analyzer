# Automated Financial Statement Analyzer (Ready-to-run)

What you get: a ready-made project that extracts financial numbers from a text or text-based PDF and computes basic financial ratios. It produces JSON, CSV and HTML reports.

Files included:
- analyzer.py : main program (double-click or run with Python)
- complex_statement.txt : realistic sample input (in thousands)
- statement.txt : very simple sample input
- README.md : this file
- run.bat (Windows double-click launcher)
- run.sh (Mac/Linux launcher)

Super-easy steps to run (2 options)

Option A — Double-click (Windows):
1. Make sure Python is installed.
2. (Optional) Install PDF support if you want to analyze PDFs: pip install pdfplumber
3. Double-click run.bat in this folder. A terminal will open and run the analyzer on the default sample file (complex_statement.txt). Press any key to close when finished.

Option B — Terminal (recommended, works on all OS):
1. Open terminal in this folder (Shift+Right-click → 'Open PowerShell window here' on Windows)
2. (Optional) Install PDF support: pip install pdfplumber
3. Run: python analyzer.py and press Enter to use the included complex_statement.txt or type any filename (e.g., yourfile.pdf or yourfile.txt)

What it detects
- Revenue, Net Income, Gross Profit, Operating Income, Total Assets, Total Liabilities, Equity, Cash, Current Assets, Current Liabilities, Inventory, Short/Long term debt (via alias matching).
- Detects notes like "in thousands" and scales numbers accordingly.
- Computes ratios: gross/operating/net margin, current ratio, debt-to-equity, ROE, ROA.
- Writes report_YYYYMMDD_HHMMSS.json, .csv, and .html in the same folder.

Demo script (90s)
1. Run python analyzer.py (or double-click run.bat) and press Enter to analyze complex_statement.txt.
2. Show the console output: the extracted items and ratios. Point to Net Income and Revenue and the Profit Margin shown.
3. Open report_*.csv in Excel to show the structured output. Open report_*.html for a quick readable report in browser.

How to add to GitHub
1. Create a new repo (example: fin-analyzer) on GitHub.
2. Upload all files in this folder (drag & drop or use git commands shown below).
3. Commit and push. Make sure README.md is visible at the top of the repo.

Example git commands (copy-paste):
git init
git add .
git commit -m "Initial commit - Automated Financial Statement Analyzer"
git branch -M main
git remote add origin https://github.com/yourusername/fin-analyzer.git
git push -u origin main

CV bullet (copy-paste)
Automated Financial Statement Analyzer (Python) — Built a Python tool that extracts financial line items from text/PDF statements, computes key ratios (profit margin, debt-to-equity, ROE), and generates JSON/CSV/HTML reports for fast analyst review. Tech: Python, (optional) pdfplumber.
