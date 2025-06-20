from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
from flask_login import  login_required
core = Blueprint('core', __name__)

UPLOAD_FOLDER = 'uploads'
EXCEL_FOLDER = 'excel_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)

# Helper functions
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except Exception:
        return None

def extract_transactions(pdf_path, password):
    rows = []
    with pdfplumber.open(pdf_path, password=password) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines.extend(text.split('\n'))

    temp_block = ""
    transactions = []
    for line in lines:
        if re.match(r"^\d+\s+\d{2}/\d{2}/\d{4}", line):
            if temp_block:
                transactions.append(temp_block.strip())
            temp_block = line
        else:
            temp_block += " " + line
    if temp_block:
        transactions.append(temp_block.strip())

    for tx in transactions:
        pattern = re.match(
            r"^(?P<sn>\d+)\s+(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<txn_id>\S+)\s+(?P<remarks>.+?)\s+(?P<amount>[\d,]+\.\d{2})\s+\((?P<amt_type>Cr|Dr)\)\s+(?P<balance>[\d,]+\.\d{2})\s+\((?P<bal_type>Cr|Dr)\)",
            tx
        )
        if pattern:
            data = pattern.groupdict()
            amount_signed = f"+{data['amount']}" if data['amt_type'] == "Cr" else f"-{data['amount']}"
            date_obj = parse_date(data["date"])
            rows.append({
                "SN0": data["sn"],
                "Date": date_obj,
                "Transaction ID": data["txn_id"],
                "Remarks": data["remarks"].strip(),
                "Amount": float(amount_signed.replace(',', '')),
                "Balance": float(data["balance"].replace(',', ''))
            })
    return pd.DataFrame(rows)

import pdfplumber
import re

def extract_account_info(pdf_path, password):
    with pdfplumber.open(pdf_path, password=password) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            text = text.replace('\n', ' ')  # Flatten into a single line for easier regex matching

            info = {}
            bank_name_match = "Union Bank Of India"
            mobile_match = re.search(r"Mobile No\s+(\d{10,})", text)
            branch_match = re.search(
                r"Home branch\s+(.*?)(?:\s+Statement Period\s+\d{2}/\d{2}/\d{4}\s+To\s+\d{2}/\d{2}\s*/\s*\d{4})?\s+IFSC",
                text)
            ifsc_match = re.search(r"IFSC\s+([A-Z0-9]+)", text)
            acct_number_match = re.search(r"Account Number\s+(\d+)", text)

            # Assign extracted values or None
            info["Bank"] = bank_name_match if mobile_match else None
            info["Mobile No"] = mobile_match.group(1) if mobile_match else None
            info["Home Branch"] = branch_match.group(1).strip() if branch_match else None
            info["IFSC"] = ifsc_match.group(1) if ifsc_match else None
            info["Account Number"] = acct_number_match.group(1) if acct_number_match else None

            return info  # Return after first page scan

def get_summary(df):
    if df.empty:
        return {}

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(by="Date")
    opening_balance = df.iloc[0]["Balance"]
    closing_balance = df.iloc[-1]["Balance"]
    start_date = df["Date"].min()
    end_date = df["Date"].max()

    start_date_str = start_date.strftime("%d-%m-%Y")
    end_date_str = end_date.strftime("%d-%m-%Y")

    credits_df = df[df["Amount"] > 0]
    debits_df = df[df["Amount"] < 0]

    credits = credits_df["Amount"].sum()
    debits = debits_df["Amount"].sum()
    net_change = closing_balance - opening_balance
    total_transactions = len(df)
    largest_credit = credits_df["Amount"].max() if not credits_df.empty else 0
    largest_debit = debits_df["Amount"].min() if not debits_df.empty else 0
    credit_frequency = len(credits_df)
    debit_frequency = len(debits_df)
    growth_rate = (net_change / opening_balance) * 100 if opening_balance != 0 else 0

    total_days = (end_date - start_date).days + 1
    avg_daily_balance = df["Balance"].mean() if total_days > 0 else 0

    return {
        "statement_period": f"{start_date_str} to {end_date_str}",
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(closing_balance, 2),
        "total_credits": round(credits, 2),
        "total_debits": round(abs(debits), 2),
        "net_change": round(net_change, 2),
        "total_transactions": total_transactions,
        "largest_credit": round(largest_credit, 2),
        "credit_frequency": credit_frequency,
        "largest_debit": round(largest_debit, 2),
        "debit_frequency": debit_frequency,
        "growth_rate": round(growth_rate, 2),
        "avg_daily_balance": round(avg_daily_balance, 2)
    }

# ---------------- ROUTES ----------------
@core.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        password = request.form.get('password')

        if not pdf_file:
            flash('No file uploaded.')
            return redirect(request.url)

        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(pdf_path)

        session['pdf_filename'] = pdf_file.filename
        session['pdf_password'] = password

        return redirect(url_for('core.get_all'))

    return render_template('index.html')

@core.route('/stats', methods=['GET'])
@login_required
def get_all():
    pdf_filename = session.get('pdf_filename')
    password = session.get('pdf_password')

    if not pdf_filename:
        flash("No PDF found in session. Please upload again.")
        return redirect(url_for('core.index'))

    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

    try:
        # Extract Transactions
        df = extract_transactions(pdf_path, password)
        if df.empty:
            flash('❌ No transactions found.')
            return redirect(url_for('core.index'))

        # Extract Account Info
        account_info = extract_account_info(pdf_path, password)

        # Apply Filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        txn_type = request.args.get('type')  # 'credit' or 'debit'

        if start_date:
            df = df[df["Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Date"] <= pd.to_datetime(end_date)]

        if txn_type == "credit":
            df = df[df["Amount"] > 0]
        elif txn_type == "debit":
            df = df[df["Amount"] < 0]

        # Save Excel
        excel_filename = f"{os.path.splitext(pdf_filename)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        excel_path = os.path.join(EXCEL_FOLDER, excel_filename)

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='FilteredTransactions')

        summary = get_summary(df)
        table_html = df.to_html(classes="table table-bordered table-hover table-striped", index=False)

        session['last_excel'] = excel_filename

        # Convert dates for chart labels
        dates = df["Date"].dt.strftime('%Y-%m-%d').tolist()
        balances = df["Balance"].tolist()

        record = {
            "summary": summary,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "excel_filename": excel_filename,
            "table_html": table_html,
            "account_info": account_info,
            "dates": dates,
            "balances": balances
        }

        return render_template("all_records.html", records=[record])

    except Exception as e:
        flash(f"❌ Error: {str(e)}")
        return redirect(url_for('core.index'))



@core.route('/download_last_excel')
def download_excel():
    filename = session.get('last_excel')
    if not filename:
        flash("No Excel available to download.")
        return redirect(url_for('core.index'))

    path = os.path.join(EXCEL_FOLDER, filename)
    if not os.path.exists(path):
        flash("Excel file not found.")
        return redirect(url_for('core.index'))

    return send_file(path, as_attachment=True, download_name=filename)
