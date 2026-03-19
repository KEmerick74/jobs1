import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

KEYWORDS = [
    "senior manager", "director", "delivery", "client success",
    "operations", "implementation", "program manager", "project manager"
]

US_LOCATIONS = ["united states", "usa", "remote - us", "remote us", "remote (us)"]

def matches_filters(title, location):
    title = title.lower()
    location = location.lower()
    if not any(k in title for k in KEYWORDS):
        return False
    if not any(u in location for u in US_LOCATIONS):
        return False
    return True

def scrape_greenhouse(company_name, url):
    jobs = []
    try:
        data = requests.get(url).json()
        for job in data["jobs"]:
            title = job["title"]
            location = job["location"]["name"]
            job_url = job["absolute_url"]
            if matches_filters(title, location):
                jobs.append([title, company_name, location, job_url, "Greenhouse"])
    except:
        pass
    return jobs

def scrape_lever(company_name, url):
    jobs = []
    try:
        data = requests.get(url).json()
        for job in data:
            title = job["text"]
            location = job["categories"]["location"]
            job_url = job["hostedUrl"]
            if matches_filters(title, location):
                jobs.append([title, company_name, location, job_url, "Lever"])
    except:
        pass
    return jobs

def scrape_workday(company_name, url):
    jobs = []
    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, "lxml")
        for job in soup.select("li"):
            title_tag = job.select_one("a")
            if not title_tag:
                continue
            title = title_tag.text.strip()
            job_url = "https://wd5.myworkdayjobs.com" + title_tag.get("href")
            location_tag = job.select_one("div.gd-location")
            location = location_tag.text.strip() if location_tag else "Unknown"
            if matches_filters(title, location):
                jobs.append([title, company_name, location, job_url, "Workday"])
    except:
        pass
    return jobs

GREENHOUSE_COMPANIES = {
    "ZoomInfo": "https://boards-api.greenhouse.io/v1/boards/zoominfo/jobs",
    "Snowflake": "https://boards-api.greenhouse.io/v1/boards/snowflake/jobs",
    "Databricks": "https://boards-api.greenhouse.io/v1/boards/databricks/jobs",
    "Plaid": "https://boards-api.greenhouse.io/v1/boards/plaid/jobs",
    "Stripe": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
    "Brex": "https://boards-api.greenhouse.io/v1/boards/brex/jobs",
    "HubSpot": "https://boards-api.greenhouse.io/v1/boards/hubspot/jobs",
    "Zendesk": "https://boards-api.greenhouse.io/v1/boards/zendesk/jobs",
    "Asana": "https://boards-api.greenhouse.io/v1/boards/asana/jobs",
    "Smartsheet": "https://boards-api.greenhouse.io/v1/boards/smartsheet/jobs",
    "Monday.com": "https://boards-api.greenhouse.io/v1/boards/monday/jobs",
    "Atlassian": "https://boards-api.greenhouse.io/v1/boards/atlassian/jobs",
    "UiPath": "https://boards-api.greenhouse.io/v1/boards/uipath/jobs",
    "Automation Anywhere": "https://boards-api.greenhouse.io/v1/boards/automationanywhere/jobs",
    "C3.ai": "https://boards-api.greenhouse.io/v1/boards/c3ai/jobs",
    "DataRobot": "https://boards-api.greenhouse.io/v1/boards/datarobot/jobs"
}

LEVER_COMPANIES = {
    "Bill.com": "https://api.lever.co/v0/postings/bill",
    "SoFi": "https://api.lever.co/v0/postings/sofi"
}

WORKDAY_COMPANIES = {
    "Experian": "https://wd5.myworkdayjobs.com/ExperianCareers",
    "Equifax": "https://wd5.myworkdayjobs.com/Equifax",
    "TransUnion": "https://wd5.myworkdayjobs.com/TransUnion",
    "LexisNexis Risk Solutions": "https://wd5.myworkdayjobs.com/LexisNexis",
    "Moody's Analytics": "https://wd5.myworkdayjobs.com/Moodys",
    "S&P Global": "https://wd5.myworkdayjobs.com/SPGlobalCareers",
    "Acxiom": "https://wd5.myworkdayjobs.com/Acxiom",
    "Envestnet Yodlee": "https://wd5.myworkdayjobs.com/Envestnet",
    "FIS": "https://wd5.myworkdayjobs.com/FIS",
    "FICO": "https://wd5.myworkdayjobs.com/FICO",
    "ServiceNow": "https://wd5.myworkdayjobs.com/servicenow",
    "Salesforce": "https://wd5.myworkdayjobs.com/salesforce",
    "Workday": "https://wd5.myworkdayjobs.com/workday",
    "Oracle Cloud": "https://wd5.myworkdayjobs.com/Oracle",
    "ADP": "https://wd5.myworkdayjobs.com/ADP",
    "Thermo Fisher": "https://wd5.myworkdayjobs.com/ThermoFisher"
}

all_jobs = []

for company, url in GREENHOUSE_COMPANIES.items():
    all_jobs.extend(scrape_greenhouse(company, url))

for company, url in LEVER_COMPANIES.items():
    all_jobs.extend(scrape_lever(company, url))

for company, url in WORKDAY_COMPANIES.items():
    all_jobs.extend(scrape_workday(company, url))

df = pd.DataFrame(all_jobs, columns=["Title", "Company", "Location", "URL", "Source"])
df.to_excel("job_report.xlsx", index=False)

msg = MIMEMultipart()
msg["From"] = os.getenv("GMAIL_EMAIL")
msg["To"] = os.getenv("RECIPIENT_EMAIL")
msg["Subject"] = "Daily Job Report"
msg.attach(MIMEText("Attached is your daily job report.", "plain"))

with open("job_report.xlsx", "rb") as f:
    part = MIMEApplication(f.read(), Name="job_report.xlsx")
    part["Content-Disposition"] = 'attachment; filename=\"job_report.xlsx\"'
    msg.attach(part)

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(os.getenv("GMAIL_EMAIL"), os.getenv("GMAIL_APP_PASSWORD"))
    server.send_message(msg)
