import os
import sys
import asyncio
import logging
from tkinter import Tk, Label, Entry, Button, StringVar, Text, END, Scrollbar, Frame, messagebox, DISABLED, NORMAL
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
    ApiIdInvalidError
)

logging.basicConfig(
    filename='telegram_assistant.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TelegramAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Account & Login Assistant")
        self.root.geometry("650x650")
        self.root.config(bg="#0f172a")
        self.root.resizable(False, False)

        self.client = None
        self.loop = asyncio.get_event_loop()

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.bg_color = "#0f172a"
        self.card_color = "#1e293b"
        self.text_color = "#f8fafc"
        self.accent_color = "#38bdf8"
        self.btn_bg = "#0284c7"
        self.btn_hover = "#0369a1"

    def create_widgets(self):
        # Title Label
        title_label = Label(
            self.root, 
            text="Telegram Assistant & Setup Guide", 
            font=("Arial", 16, "bold"), 
            bg=self.bg_color, 
            fg=self.accent_color
        )
        title_label.pack(pady=15)

        # Main Frame / Container
        container = Frame(self.root, bg=self.card_color, bd=2, relief="flat")
        container.place(x=30, y=70, width=590, height=350)

        # API ID
        Label(container, text="Telegram API ID:", bg=self.card_color, fg=self.text_color, font=("Arial", 10, "bold")).place(x=20, y=20)
        self.api_id_entry = Entry(container, width=30, font=("Arial", 11), bg="#334155", fg=self.text_color, insertbackground="white")
        self.api_id_entry.place(x=180, y=20)

        # API Hash
        Label(container, text="Telegram API Hash:", bg=self.card_color, fg=self.text_color, font=("Arial", 10, "bold")).place(x=20, y=65)
        self.api_hash_entry = Entry(container, width=30, font=("Arial", 11), bg="#334155", fg=self.text_color, insertbackground="white")
        self.api_hash_entry.place(x=180, y=65)

        # Phone Number
        Label(container, text="Phone Number (+...):", bg=self.card_color, fg=self.text_color, font=("Arial", 10, "bold")).place(x=20, y=110)
        self.phone_entry = Entry(container, width=30, font=("Arial", 11), bg="#334155", fg=self.text_color, insertbackground="white")
        self.phone_entry.place(x=180, y=110)
        self.phone_entry.insert(0, "+")

        # Dynamic Code / Password Field Label & Input
        self.dynamic_label = Label(container, text="Verification Code / Password:", bg=self.card_color, fg=self.text_color, font=("Arial", 10, "bold"))
        self.dynamic_label.place(x=20, y=155)
        self.dynamic_entry = Entry(container, width=30, font=("Arial", 11), bg="#334155", fg=self.text_color, insertbackground="white", show="*")
        self.dynamic_entry.place(x=180, y=155)

        # Action Buttons
        self.action_btn = Button(
            container, 
            text="Start Connection / Send Code", 
            command=self.on_action_click,
            bg=self.btn_bg, 
            fg="white", 
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10, pady=5
        )
        self.action_btn.place(x=180, y=210)

        # Console / Log Terminal Frame
        terminal_frame = Frame(self.root, bg="#000000")
        terminal_frame.place(x=30, y=435, width=590, height=180)

        self.log_text = Text(terminal_frame, bg="#0f172a", fg="#22c55e", font=("Consolas", 9), wrap="word", state=DISABLED)
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = Scrollbar(terminal_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log("System Ready. Please enter your valid Telegram API credentials and phone number.")

    def log(self, message):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, f"> {message}\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)
        logging.info(message)

    def on_action_click(self):
        api_id = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        phone = self.phone_entry.get().strip()
        code_or_pass = self.dynamic_entry.get().strip()

        if not api_id or not api_hash or not phone:
            messagebox.showerror("Error", "Please fill in API ID, API Hash, and Phone Number.")
            return

        # Run async task safely in background or event loop wrapper
        try:
            self.loop.run_until_complete(self.process_telegram_auth(api_id, api_hash, phone, code_or_pass))
        except Exception as e:
            self.log(f"Runtime Exception: {str(e)}")
            messagebox.showerror("Exception", f"An unexpected error occurred: {str(e)}")

    async def process_telegram_auth(self, api_id_str, api_hash, phone, input_val):
        try:
            api_id = int(api_id_str)
        except ValueError:
            self.log("Error: API ID must be an integer number.")
            messagebox.showerror("Invalid API ID", "API ID must consist of numbers only.")
            return

        session_name = f"session_{phone.replace('+', '')}"

        if not self.client:
            self.client = TelegramClient(session_name, api_id, api_hash)

        try:
            if not self.client.is_connected():
                self.log("Connecting to Telegram servers...")
                await self.client.connect()

            if not await self.client.is_user_authorized():
                if not input_val:
                    self.log(f"Requesting verification code sent to {phone}...")
                    await self.client.send_code_request(phone)
                    self.log("Code sent successfully via Telegram. Please type the code above and click the button again.")
                    messagebox.showinfo("Code Sent", "Verification code has been sent to your Telegram app/SMS.")
                else:
                    # Check if input is verification code or 2FA password
                    try:
                        self.log("Attempting sign in with provided code...")
                        await self.client.sign_in(phone, input_val)
                        self.log("Successfully signed in / authenticated!")
                        messagebox.success("Success", "Telegram session successfully established!")
                    except PhoneCodeInvalidError:
                        self.log("Error: The verification code entered is invalid.")
                        messagebox.showerror("Invalid Code", "The code you entered is incorrect.")
                    except SessionPasswordNeededError:
                        self.log("Two-Step Verification (2FA) password required. Please enter your cloud password above.")
                        # Change field to show password securely
                        self.dynamic_entry.config(show="*")
                        if input_val:
                            try:
                                await self.client.sign_in(password=input_val)
                                self.log("Successfully signed in with 2FA password!")
                                messagebox.showinfo("Success", "Logged in successfully with 2FA password!")
                            except Exception as e:
                                self.log(f"2FA Error: {str(e)}")
                                messagebox.showerror("2FA Error", str(e))
            else:
                self.log("User is already authorized and logged in with this session.")
                messagebox.showinfo("Status", "You are already logged in!")

        except FloodWaitError as e:
            self.log(f"Rate limit hit! Telegram requires waiting for {e.seconds} seconds.")
            messagebox.showwarning("Rate Limit", f"Too many requests. Please wait {e.seconds} seconds.")
        except ApiIdInvalidError:
            self.log("Error: The provided API ID or API Hash is invalid.")
            messagebox.showerror("Invalid API", "API ID or API Hash is incorrect according to Telegram.")
        except PhoneNumberInvalidError:
            self.log("Error: The phone number format is invalid.")
            messagebox.showerror("Invalid Phone", "The phone number format is incorrect.")
        except Exception as e:
            self.log(f"Authentication Error: {str(e)}")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = Tk()
    app = TelegramAssistantApp(root)
    root.mainloop()
