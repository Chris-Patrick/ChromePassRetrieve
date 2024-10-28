import os
import sys
import logging
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import timezone, datetime, timedelta
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)


def get_encryption_key():
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    file_path_var = os.path.join(current_dir, "var.txt")

    os.path.join(current_dir, "var.txt")

    with open(file_path_var, "r") as file:
        lines = file.readlines()
    key_line = lines[0].rstrip('\n')
    lc = os.path.abspath(key_line)

    local_state_path = lc

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


def browse_encrypted_file():
    file_path = filedialog.askopenfilename(title="Select Encrypted Chrome Database File")
    if file_path:
        encrypted_file_entry.delete(0, tk.END)
        encrypted_file_entry.insert(0, file_path)


def browse_save_file():
    file_path = filedialog.asksaveasfilename(title="Save Passwords to File", defaultextension=".txt")
    if file_path:
        save_file_entry.delete(0, tk.END)
        save_file_entry.insert(0, file_path)


def retrieve_passwords():
    # Validate input fields
    encrypted_file_path = encrypted_file_entry.get()
    save_file_path = save_file_entry.get()
    if not os.path.isfile(encrypted_file_path):
        messagebox.showerror("Error", "Invalid or empty encrypted file path.")
        return
    if not save_file_path:
        messagebox.showerror("Error", "Invalid or empty save file path.")
        return

    try:
        # get the AES key
        key = get_encryption_key()
        # local sqlite Chrome database path
        db_file = os.path.abspath(encrypted_file_path)
        db_path = db_file
        # copy the file to another location
        # as the database will be locked if chrome is currently running
        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)
        # connect to the database
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        # `logins` table has the data we need
        cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")

        try:
            with open(save_file_path, 'w') as file:
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
                    else:
                        continue
                    if date_created != 86400000000 and date_created:
                        file.write(f"Creation date: {str(get_chrome_datetime(date_created))}\n")
                    if date_last_used != 86400000000 and date_last_used:
                        file.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}\n")
                    file.write("=" * 50 + '\n')

            cursor.close()
            db.close()
            try:
                # try to remove the copied db file
                os.remove(filename)
            except:
                pass

            messagebox.showinfo("Success", "Passwords retrieved successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while writing to the file: {e}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# Create the main window
window = tk.Tk()
window.title("Chrome Password Retrieval")
window.geometry("400x200")

# Encrypted file path
encrypted_file_label = tk.Label(window, text="Encrypted File Path:")
encrypted_file_label.pack()
encrypted_file_entry = tk.Entry(window, width=40)
encrypted_file_entry.pack(side=tk.LEFT, padx=10)
encrypted_file_browse_button = tk.Button(window, text="Browse", command=browse_encrypted_file)
encrypted_file_browse_button.pack(side=tk.LEFT)

# Save file path
save_file_label = tk.Label(window, text="Save Passwords to:")
save_file_label.pack()
save_file_entry = tk.Entry(window, width=40)
save_file_entry.pack(side=tk.LEFT, padx=10)
save_file_browse_button = tk.Button(window, text="Browse", command=browse_save_file)
save_file_browse_button.pack(side=tk.LEFT)

# Retrieve passwords button
retrieve_passwords_button = tk.Button(window, text="Retrieve Passwords", command=retrieve_passwords)
retrieve_passwords_button.pack(pady=20)

# Start the GUI event loop
window.mainloop()