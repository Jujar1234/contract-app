import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import glob
import PyPDF2
import re
from flask import Flask, render_template, request

# Initialize Flask app
app = Flask(__name__)

# Step 1: Contract ID Input and URL generation
def get_contract_data(contract_id):
    base_url = f"https://commonwebapp.mahindrafs.com/SOA_Mobile_CLMS/DownloadSOA_crm.aspx?userid=5100000016&contractno={contract_id}"

    # Set up Selenium WebDriver with headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Chromedriver path for Linux environment (Render)
    service = Service("/usr/bin/chromedriver")  # Default location for Render
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(base_url)

    # Wait for 20 seconds after opening the URL
    time.sleep(20)

    # Step 3: Download PDF
    downloads_folder = "/tmp"  # Use /tmp for Render's file storage
    file_pattern = f"SOA_{contract_id}_*.pdf"  # Pattern for the downloaded file
    file_path = glob.glob(os.path.join(downloads_folder, file_pattern))

    if not file_path:
        driver.quit()
        return {"error": "File not found!"}

    file_path = file_path[0]  # Get the first matched file

    # Step 4: Extract data from the PDF
    data_extracted = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                data_extracted += page.extract_text()
    except Exception as e:
        driver.quit()
        return {"error": f"Error extracting data: {e}"}

    # Step 5: Parse extracted data using regex
    contract_no_pattern = re.compile(r"Contract No\s*:\s*(\d+)")
    customer_name_pattern = re.compile(r"Name\s*:\s*([A-Za-z\s]+)")
    loan_summary_pattern = re.compile(r"Particulars\s+Due\s+Received\s+Balance\s+No\s+of\s+Instalments\s*(\d+)\s*(\d+)\s*(\d+)\s*Instalment\s+Amount\s*(\d+)\s*(\d+)\s*(\d+)")

    contract_no = contract_no_pattern.search(data_extracted)
    customer_name = customer_name_pattern.search(data_extracted)
    loan_summary = loan_summary_pattern.search(data_extracted)

    contract_no_value = contract_no.group(1) if contract_no else "N/A"
    customer_name_value = customer_name.group(1).strip() if customer_name else "N/A"
    no_of_instalments = loan_summary.group(1) if loan_summary else "N/A"
    due = loan_summary.group(2) if loan_summary else "N/A"
    received = loan_summary.group(3) if loan_summary else "N/A"
    balance = loan_summary.group(4) if loan_summary else "N/A"
    instalment_amount = loan_summary.group(5) if loan_summary else "N/A"

    # Prepare data for table
    data = {
        "Contract No": contract_no_value,
        "Customer Name": customer_name_value,
        "No of Instalments": no_of_instalments,
        "Due": due,
        "Received": received,
        "Balance": balance,
        "Instalment Amount": instalment_amount
    }

    # Close browser after extracting data
    driver.quit()
    return data

# Route to render the frontend form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission and display contract data
@app.route('/get_contract_info', methods=['POST'])
def contract_info():
    contract_id = request.form['contract_id']
    if contract_id:
        contract_data = get_contract_data(contract_id)
        if "error" in contract_data:
            return render_template('index.html', error=contract_data['error'])
        return render_template('index.html', contract_data=contract_data)
    return render_template('index.html', error="Contract ID is required")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
