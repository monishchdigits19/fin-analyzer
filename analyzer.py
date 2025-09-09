#!/usr/bin/env python3
"""
Automated Financial Statement Analyzer 

What this does:
- Reads a text file (.txt) or text-based PDF (.pdf) containing financial statements.
- Extracts core items (Revenue, Net Income, Total Assets, Liabilities, Equity, Cash, etc.) based on alias matching.
- Parses numbers (handles commas, $ symbol, parentheses for negatives).
- Detects "in thousands" note and scales numbers accordingly (optional).
- Computes basic ratios: gross margin, operating margin, net margin, current ratio, debt-to-equity, ROE, ROA.
- Writes outputs: report.json, report.csv, report.html in the same folder.
- Minimal setup: Python 3.9+. For PDF support optionally install pdfplumber: pip install pdfplumber

Usage:
    python analyzer.py [filename]
If no filename is provided, the script will look for 'complex_statement.txt' or 'statement.txt' in the same folder.
If run without a terminal (double-click), the script will still prompt in a small GUI file chooser (if tkinter available).
"""

import os, sys, re, json, csv, argparse, datetime

# Try optional dependencies
try:
    import pdfplumber
    HAVE_PDFPLUMBER = True
except Exception:
    HAVE_PDFPLUMBER = False

# Try tkinter for file dialog if no filename provided
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAVE_TK = True
except Exception:
    HAVE_TK = False

# --- helpers ---
number_re = re.compile(r'\(?-?\$?[\d,]+(?:\.\d+)?\)?')

def parse_number_str(s, scale=1.0):
    if s is None:
        return None
    s = str(s).strip()
    if s in ['', '—', '-', 'N/A', 'na', 'n/a']:
        return None
    # parentheses -> negative
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    # remove currency and spaces and commas
    s = s.replace('$', '').replace(',', '').replace(' ', '').replace('\u2013','-')
    # remove any characters except digits, dot, minus
    s = re.sub(r'[^\d\-.]', '', s)
    if s in ['', '.', '-']:
        return None
    try:
        val = float(s)
    except:
        return None
    if neg:
        val = -val
    return val * scale

ALIASES = {
    "Revenue": ["revenue", "net sales", "sales", "turnover", "total revenue"],
    "Cost of Goods Sold": ["cost of goods sold", "cogs", "cost of sales", "cost of goods"],
    "Gross Profit": ["gross profit"],
    "Operating Income": ["operating income", "ebit", "operating profit"],
    "Net Income": ["net income", "profit for the year", "net profit", "profit (loss)", "profit attributable"],
    "Total Assets": ["total assets", "assets"],
    "Total Liabilities": ["total liabilities", "liabilities"],
    "Equity": ["equity", "total equity", "shareholders' equity"],
    "Cash and Equivalents": ["cash and cash equivalents", "cash at bank", "cash"],
    "Current Assets": ["current assets"],
    "Current Liabilities": ["current liabilities"],
    "Inventory": ["inventory", "inventories"],
    "Short Term Debt": ["current portion of long-term debt", "short-term borrowings", "short term debt"],
    "Long Term Debt": ["long-term debt", "long term debt", "long term borrowings"],
}

def extract_text_from_pdf(path):
    if not HAVE_PDFPLUMBER:
        raise RuntimeError("pdfplumber not installed. Install with: pip install pdfplumber")
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            p = page.extract_text() or ""
            text += p + "\n"
    return text

def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def detect_scale(text):
    # Detect "in thousands" or similar notes -> scale by 1000
    low = text.lower()
    if "in thousands" in low or "(in thousands" in low or "amounts in thousands" in low:
        return 1000.0
    if "in millions" in low or "(in millions" in low or "amounts in millions" in low:
        return 1000000.0
    return 1.0

def find_by_aliases(text, scale=1.0):
    results = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        nums = number_re.findall(ln)
        for key, phrases in ALIASES.items():
            for ph in phrases:
                if ph in low:
                    # choose rightmost number on line if present
                    if nums:
                        raw = nums[-1]
                        val = parse_number_str(raw, scale=scale)
                        if val is not None:
                            results[key] = val
    return results

def extract_all_numbers(text, scale=1.0):
    nums = number_re.findall(text)
    cleaned = []
    for raw in nums:
        v = parse_number_str(raw, scale=scale)
        if v is not None:
            cleaned.append(v)
    return cleaned

def safe_div(a,b):
    try:
        if a is None or b is None:
            return None
        if b == 0:
            return None
        return a / b
    except:
        return None

def compute_ratios(fin):
    r = {}
    rev = fin.get("Revenue")
    gross = fin.get("Gross Profit") or (None if (fin.get("Revenue") is None or fin.get("Cost of Goods Sold") is None) else fin["Revenue"] - fin["Cost of Goods Sold"])
    r["gross_margin"] = safe_div(gross, rev)
    r["operating_margin"] = safe_div(fin.get("Operating Income"), rev)
    r["net_margin"] = safe_div(fin.get("Net Income"), rev)
    r["current_ratio"] = safe_div(fin.get("Current Assets"), fin.get("Current Liabilities"))
    r["debt_to_equity"] = safe_div(fin.get("Total Liabilities"), fin.get("Equity"))
    r["roe"] = safe_div(fin.get("Net Income"), fin.get("Equity"))
    r["roa"] = safe_div(fin.get("Net Income"), fin.get("Total Assets"))
    return r

def flag_anomalies(fin, ratios):
    flags = []
    if ratios.get("current_ratio") is not None and ratios["current_ratio"] < 1:
        flags.append("Current ratio < 1 — potential short-term liquidity concern")
    if ratios.get("debt_to_equity") is not None and ratios["debt_to_equity"] > 2:
        flags.append("High debt-to-equity (>2) — leverage is high")
    if fin.get("Net Income") is not None and fin.get("Net Income") < 0:
        flags.append("Net income negative — company reported a loss")
    if fin.get("Cash and Equivalents") is not None and fin.get("Cash and Equivalents") < 0:
        flags.append("Negative cash — check parsing errors")
    return flags

def write_reports(fin, numbers, ratios, flags, out_prefix="report"):
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_json = f"{out_prefix}_{now}.json"
    base_csv = f"{out_prefix}_{now}.csv"
    base_html = f"{out_prefix}_{now}.html"
    report = {"financial_items": fin, "numbers_found": numbers, "ratios": ratios, "flags": flags}
    with open(base_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    # CSV summary
    with open(base_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Item","Value"])
        for k,v in fin.items():
            writer.writerow([k, v])
        writer.writerow([])
        writer.writerow(["Ratio","Value"])
        for k,v in ratios.items():
            writer.writerow([k, v])
        writer.writerow([])
        writer.writerow(["Flags"])
        for fline in flags:
            writer.writerow([fline])
    # Simple HTML
    html_parts = []
    html_parts.append("<html><head><meta charset='utf-8'><title>Financial Analyzer Report</title></head><body>")
    html_parts.append("<h2>Extracted Financial Items</h2><table border='1' cellpadding='4'>")
    for k,v in fin.items():
        html_parts.append(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>")
    html_parts.append("</table>")
    html_parts.append("<h2>Ratios</h2><table border='1' cellpadding='4'>")
    for k,v in ratios.items():
        if v is None:
            display = "N/A"
        else:
            if "margin" in k:
                display = f"{v*100:.2f}%"
            else:
                display = f"{v:.2f}"
        html_parts.append(f"<tr><td><b>{k}</b></td><td>{display}</td></tr>")
    html_parts.append("</table>")
    html_parts.append("<h2>Flags</h2><ul>")
    if flags:
        for fline in flags:
            html_parts.append(f"<li>{fline}</li>")
    else:
        html_parts.append("<li>No obvious flags detected.</li>")
    html_parts.append("</ul>")
    html_parts.append("<h2>All Numbers Found (sample)</h2>")
    html_parts.append("<p>" + ", ".join(map(str, numbers[:50])) + (" ..." if len(numbers)>50 else "") + "</p>")
    html_parts.append("</body></html>")
    with open(base_html, "w", encoding="utf-8") as f:
        f.write("\\n".join(html_parts))
    return base_json, base_csv, base_html

def choose_file_dialog():
    if not HAVE_TK:
        return None
    root = tk.Tk()
    root.withdraw()
    fpath = filedialog.askopenfilename(title="Select financial statement file", filetypes=[("PDF files","*.pdf"),("Text files","*.txt"),("All files","*.*")])
    root.update()
    return fpath

def analyze_file(path):
    if not os.path.exists(path):
        print("File not found:", path)
        return
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        if not HAVE_PDFPLUMBER:
            print("pdfplumber not installed. Install with: pip install pdfplumber, or convert PDF to text and retry.")
            return
        text = extract_text_from_pdf(path)
    else:
        text = extract_text_from_txt(path)
    scale = detect_scale(text)
    if scale != 1.0:
        print(f"Detected scale note in document. Scaling numeric values by {scale}.")
    fin = find_by_aliases(text, scale=scale)
    numbers = extract_all_numbers(text, scale=scale)
    ratios = compute_ratios(fin)
    flags = flag_anomalies(fin, ratios)
    # Print to console neatly
    print("\\n===== Financial Analyzer Results =====\\n")
    print("Extracted items:")
    for k,v in fin.items():
        print(f" - {k}: {v}")
    print("\\nRatios:")
    for k,v in ratios.items():
        if v is None:
            ds = "N/A"
        else:
            ds = (f"{v*100:.2f}%" if 'margin' in k else f"{v:.2f}")
        print(f" - {k}: {ds}")
    if flags:
        print("\\nFlags:")
        for fline in flags:
            print(" * ", fline)
    else:
        print("\\nNo obvious flags detected.")
    out_json, out_csv, out_html = write_reports(fin, numbers, ratios, flags, out_prefix="report")
    print(f"\\nReports written: {out_json}, {out_csv}, {out_html}")

def main():
    parser = argparse.ArgumentParser(description='Automated Financial Statement Analyzer')
    parser.add_argument('file', nargs='?', help='Path to PDF or TXT financial statement')
    args = parser.parse_args()
    fname = args.file
    # if no filename provided, look for defaults
    if not fname:
        for default in ["complex_statement.txt", "statement.txt"]:
            if os.path.exists(default):
                fname = default
                break
    # if still no filename, try GUI file chooser
    if not fname:
        print("No file specified.")
        if HAVE_TK:
            print("Opening file dialog... (choose a .txt or .pdf)")
            chosen = choose_file_dialog()
            if chosen:
                fname = chosen
        else:
            print("Place a text or text-based PDF in the same folder and re-run, or call: python analyzer.py yourfile.pdf")
            return
    analyze_file(fname)

if __name__ == '__main__':
    main()
