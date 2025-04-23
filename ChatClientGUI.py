import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox


class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("TCP Chat Client")
        self.master.geometry("400x500")

        self.chat_display = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(master)
        self.msg_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.msg_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(pady=(0, 10))

        self.sent_messages = []  # ✅ store sent messages

        self.host = 'localhost'
        self.port = 9091
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            messagebox.showerror("Connection Failed", "Unable to connect to the server.")
            master.quit()
            return

        self.display_message("Connected to server.")
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                self.display_message(data.decode())
            except:
                break

    def send_message(self, event=None):
        message = self.msg_entry.get().strip()
        if message:
            try:
                self.sock.send(message.encode())
                self.sent_messages.append(message)
                self.display_message(f"You: {message}")
            except:
                self.display_message("Failed to send message.")
            self.msg_entry.delete(0, tk.END)
            if message.lower() == 'exit':
                self.master.quit()

    def on_close(self):
        try:
            self.sock.send(b"exit")
            self.sock.close()
        except:
            pass
        print("Sent Messages History:", self.sent_messages)
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", client.on_close)
    root.mainloop()
