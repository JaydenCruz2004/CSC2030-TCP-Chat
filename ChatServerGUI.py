import socket
import select
import threading
import tkinter as tk
from tkinter import scrolledtext


class ChatServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("TCP Chat Server")
        self.master.geometry("500x500")

        self.log = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD)
        self.log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(master)
        self.msg_entry.pack(padx=10, pady=(0, 5), fill=tk.X)
        self.msg_entry.bind("<Return>", self.send_server_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_server_message)
        self.send_button.pack(pady=(0, 10))

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.bind(('localhost', 9091))
        self.server.listen(5)

        self.inputs = [self.server]
        self.outputs = []
        self.message_queues = {}
        self.client_addresses = {}

        self.running = True
        threading.Thread(target=self.run_server, daemon=True).start()

        self.log_message("Server started on port 9088...")

    def log_message(self, message):
        self.log.config(state='normal')
        self.log.insert(tk.END, message + "\n")
        self.log.config(state='disabled')
        self.log.yview(tk.END)

    def run_server(self):
        while self.running:
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 0.1)

            for s in readable:
                if s is self.server:
                    connection, address = self.server.accept()
                    connection.setblocking(False)
                    self.inputs.append(connection)
                    self.message_queues[connection] = []
                    self.client_addresses[connection] = address
                    self.log_message(f"Client {address} connected.")
                    self.message_queues[connection].append("Welcome to the chat!".encode())
                    if connection not in self.outputs:
                        self.outputs.append(connection)
                else:
                    try:
                        data = s.recv(1024)
                        if data:
                            msg = f"[{self.client_addresses[s][0]}:{self.client_addresses[s][1]}] {data.decode()}"
                            self.log_message(msg)
                            self.broadcast_message(msg.encode(), exclude_socket=s)
                        else:
                            self.disconnect(s)
                    except:
                        self.disconnect(s)

            for s in writable:
                if self.message_queues[s]:
                    try:
                        next_msg = self.message_queues[s].pop(0)
                        s.send(next_msg)
                    except:
                        self.disconnect(s)
                else:
                    if s in self.outputs:
                        self.outputs.remove(s)

            for s in exceptional:
                self.disconnect(s)

    def send_server_message(self, event=None):
        msg = self.msg_entry.get().strip()
        if msg:
            full_msg = f"[Server]: {msg}"
            self.log_message(full_msg)
            self.broadcast_message(full_msg.encode())
            self.msg_entry.delete(0, tk.END)

    def broadcast_message(self, message, exclude_socket=None):
        for client in self.message_queues:
            if client != exclude_socket:
                self.message_queues[client].append(message)
                if client not in self.outputs:
                    self.outputs.append(client)

    def disconnect(self, s):
        self.log_message(f"Client {self.client_addresses.get(s, 'Unknown')} disconnected.")
        if s in self.outputs:
            self.outputs.remove(s)
        if s in self.inputs:
            self.inputs.remove(s)
        s.close()
        self.message_queues.pop(s, None)
        self.client_addresses.pop(s, None)

    def stop_server(self):
        self.running = False
        self.server.close()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    server_gui = ChatServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", server_gui.stop_server)
    root.mainloop()
