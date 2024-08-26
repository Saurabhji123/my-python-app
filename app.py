from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import vonage
import os
import time
import threading

app = Flask(__name__)

# Set port for deployment
port = int(os.environ.get('PORT', 5000))

# Environment Variables
VONAGE_API_KEY = os.environ.get('71257b49')
VONAGE_API_SECRET = os.environ.get('PNu4Uu4CLxHP8Hgj')
TO_PHONE_NUMBER = '919335210176'  # Recipient phone number (where you receive SMS notifications)
TARGET_PHONE_NUMBER = '9451150496'  # Targeted person's phone number

# Initialize Vonage Client
client = vonage.Client(key=os.getenv('VONAGE_API_KEY'), secret=os.getenv('VONAGE_API_SECRET'))
sms = vonage.Sms(client)

# Setup Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_to_whatsapp():
    driver.get("https://web.whatsapp.com")
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="pane-side"]'))
    )
    print("Logged in to WhatsApp Web")

def find_contact(phone_number):
    search_box = driver.find_element(By.XPATH, '//*[@title="Search input textbox"]')
    search_box.clear()
    search_box.send_keys(phone_number)  # Targeted person's phone number
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f'//span[@title="{phone_number}"]'))
    )
    contact = driver.find_element(By.XPATH, f'//span[@title="{phone_number}"]')
    contact.click()
    print(f"Contact {phone_number} selected")

def check_online_status():
    try:
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@class="_3c9sP"]'))
        )
        online_status = status_element.text
        return "online" in online_status.lower()
    except:
        print("Could not determine online status")
        return False

def send_sms_notification(phone_number):
    responseData = sms.send_message(
        {
            "from": "Vonage APIs",  # Ensure this is the desired sender ID (or brand name)
            "to": TO_PHONE_NUMBER,  # Recipient phone number for SMS notifications
            "text": f"{phone_number} is online on WhatsApp!"
        }
    )
    
    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")

def monitoring_task():
    login_to_whatsapp()
    while True:
        find_contact(TARGET_PHONE_NUMBER)
        if check_online_status():
            send_sms_notification(TARGET_PHONE_NUMBER)
        time.sleep(60)  # Check every minute

@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    # Start the monitoring in a separate thread
    thread = threading.Thread(target=monitoring_task)
    thread.start()
    return jsonify({"status": "success", "message": "Monitoring started"}), 200

@app.route('/check-status', methods=['GET'])
def check_status():
    try:
        login_to_whatsapp()
        find_contact(TARGET_PHONE_NUMBER)
        if check_online_status():
            send_sms_notification(TARGET_PHONE_NUMBER)
            return jsonify({"status": "success", "message": "Notification sent"}), 200
        return jsonify({"status": "failure", "message": "Target is not online"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
