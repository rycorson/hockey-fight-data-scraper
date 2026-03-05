# Hockey Fight Data Scraper

## Overview
This Python-based automation tool programmatically extracts, parses, and processes hockey fight data with target dates in mind. 

The script calculates custom "fantasy" point metrics based on community voting percentages and automatically synchronizes the structured data with a Google Sheet in the cloud. It is designed to run recursively, updating existing records and appending new data without duplication.

## Technologies & Libraries
* **Language:** Python 3
* **Web Automation:** Playwright (Chromium)
* **HTML Parsing:** BeautifulSoup4 (bs4)
* **Data Processing:** Regular Expressions (Regex), Datetime
* **Cloud Integration:** Google Sheets API (`gspread`)
* **Security:** `python-dotenv`

## Key Features & Technical Highlights

* **Dynamic Web Automation:** Utilizes Playwright to navigate JavaScript-rendered content and simulate keyboard events to trigger lazy-loaded data.
* **Complex Data Extraction & Cleaning:** Leverages BeautifulSoup and Regular Expressions to parse unstructured text into actionable data points (dates, fighter names, community vote percentages) while filtering out irrelevant content.
* **Automated Cloud Synchronization:** Integrates with the Google Sheets API via `gspread` to perform delta updates. The script checks existing cloud records, appending brand new fights or updating existing scores if a fighter's point value has increased.
* **Secure Credential Management:** Implements environment variables (`.env`) to ensure Google Cloud service account credentials and API keys remain securely isolated from version control.

## How to Run Locally

### 1. Prerequisites
Ensure you have Python 3 installed. You will also need a Google Cloud Service Account JSON key with access to the target Google Sheet.

### 2. Installation
Clone the repository and navigate into the project directory:
```bash
git clone https://github.com/](https://github.com/rycorson/hockey-fight-data-scraper.git

#Install the Python dependencies
pip install playwright beautifulsoup4 gspread python-dotenv

#Install the required Playwright browser binaries
playwright install chromium
```
### 3. Environment Setup
   Create a file names `.env` in the root directory of the project and add your Google Cloud credentials and the Google sheet name you would like to append the data to.
   ```plaintext
   GOOGLE_CRED=your-service-account-file.json
   GOOGLE_SHEET_NAME=your_target_sheet_name
   ```
   **Ensure your `.json` key file is placed in the project root and that both it and the `.env` file are listed in your personal `.gitignore`
### 4. Execution
   Run the script from your terminal:
   ```bash
   python hockeyFightScraper.py
```

## Author
Ryan Corson
* GitHub: @rycorson
* LinkedIn: https://www.linkedin.com/in/ryan-corson/
