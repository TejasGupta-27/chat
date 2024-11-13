import socket
import tkinter as tk
from tkinter import messagebox
import threading
import select

# Function to receive messages from the server
def receive_messages():
    while True:
        try:
            # Wait for the socket to be ready to read
            readable, _, _ = select.select([client_socket], [], [], 0.1)
            if readable:
                message = client_socket.recv(1024).decode()
                if message:
                    print(f"Received: {message}")  # Debugging output
                    # Insert messages to the UI safely
                    message_list.insert(tk.END, message)
                    message_list.yview(tk.END)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Function to send a message
def send_message():
    message = message_entry.get()
    if message.strip():  # Avoid sending empty messages
        try:
            # Notify user and server
            sender_message = f"{username}: {message}"
            message_list.insert(tk.END, sender_message)
            message_list.yview(tk.END)
            client_socket.send(message.encode())
        except Exception as e:
            messagebox.showerror("Connection Error", f"Message could not be sent: {e}")
        message_entry.delete(0, tk.END)

# Function to change the chat room
def change_room(room):
    global current_room
    if current_room != room:
        current_room = room
        room_label.config(text=f"Current Room: {current_room}")
        message_list.delete(0, tk.END)  # Clear chat window
        try:
            # Notify the server of the room change
            client_socket.send(f"/change_room {room}".encode())
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to switch room: {e}")

# Prompt the user to enter a username
def prompt_username():
    def submit_username():
        nonlocal username_window
        global username
        username = username_entry.get().strip()
        if username:
            username_window.destroy()
        else:
            messagebox.showwarning("Input Error", "Username cannot be empty!")

    username_window = tk.Toplevel(root)
    username_window.title("Enter Username")
    username_window.geometry("300x150")
    username_window.configure(bg="#2f3136")

    tk.Label(username_window, text="Enter your username:", bg="#2f3136", fg="white", font=("Arial", 12)).pack(pady=10)
    username_entry = tk.Entry(username_window, font=("Arial", 14), bg="#40444b", fg="white", relief=tk.FLAT)
    username_entry.pack(pady=10)

    tk.Button(username_window, text="Submit", command=submit_username, bg="#7289da", fg="white", font=("Arial", 14), relief=tk.FLAT).pack(pady=10)

    username_window.transient(root)
    username_window.grab_set()
    root.wait_window(username_window)

# Setup the connection to the server
def setup_connection():
    global client_socket
    global current_room
    current_room = "General"
    prompt_username()  # Prompt for username before connecting

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 8080))
        client_socket.send(f"/username {username}".encode())  # Send username to the server
        threading.Thread(target=receive_messages, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to the server: {str(e)}")

# UI Setup using Tkinter
root = tk.Tk()
root.title("Multiprocess Chat Application")
root.geometry("800x600")
root.configure(bg="#2f3136")

# Frame for Sidebar and Chat Window
frame = tk.Frame(root, bg="#2f3136")
frame.pack(fill=tk.BOTH, expand=True)

# Sidebar for rooms and user list
sidebar = tk.Frame(frame, width=200, bg="#2f3136")
sidebar.pack(side=tk.LEFT, fill=tk.Y)

rooms_listbox = tk.Listbox(sidebar, height=10, bg="#2f3136", fg="white", selectmode=tk.SINGLE, font=("Arial", 14))
rooms_listbox.pack(pady=20, padx=10)
rooms = ["General", "Tech", "Music"]
for room in rooms:
    rooms_listbox.insert(tk.END, room)

# Chat window (main area)
chat_frame = tk.Frame(frame, bg="#2f3136")
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Chat message display area
message_list = tk.Listbox(chat_frame, bg="#2f3136", fg="white", font=("Arial", 12), height=20, selectmode=tk.SINGLE)
message_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Status label showing current room
room_label = tk.Label(root, text="Current Room: General", bg="#2f3136", fg="white", font=("Arial", 12))
room_label.pack(side=tk.BOTTOM, fill=tk.X)

# Message input area
input_frame = tk.Frame(root, bg="#40444b")
input_frame.pack(fill=tk.X)

message_entry = tk.Entry(input_frame, width=50, bg="#40444b", fg="white", font=("Arial", 14), bd=0, relief=tk.FLAT)
message_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

send_button = tk.Button(input_frame, text="Send", command=send_message, bg="#7289da", fg="white", font=("Arial", 14), relief=tk.FLAT)
send_button.pack(side=tk.RIGHT, padx=10, pady=5)

# Change room when selected
rooms_listbox.bind("<ButtonRelease-1>", lambda event: change_room(rooms_listbox.get(rooms_listbox.curselection())))

# Start the connection setup
setup_connection()

# Start the Tkinter event loop
root.mainloop()
