import socket
import tkinter as tk
from tkinter import messagebox
import threading
import select

# Function to receive messages from the server
def receive_messages():
    while True:
        # Using select to make the socket non-blocking
        try:
            # Wait for the socket to be ready to read (non-blocking)
            readable, _, _ = select.select([client_socket], [], [], 0.1)  
            if readable:
                message = client_socket.recv(1024).decode()
                if message:
                    print(f"Received: {message}")  # Debugging output
                    message_list.insert(tk.END, message)
                    message_list.yview(tk.END)  # Auto-scroll to the bottom
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Function to send a message
def send_message():
    message = message_entry.get()
    if message != "":
        # Show the sender's message immediately
        sender_message = f"{username}: {message}"
        message_list.insert(tk.END, sender_message)
        message_list.yview(tk.END)  # Auto-scroll to the bottom
        try:
            client_socket.send(message.encode())  # Send the message to the server
        except:
            messagebox.showerror("Connection Error", "Message could not be sent. Server disconnected.")
        message_entry.delete(0, tk.END)

# Function to change room
def change_room(room):
    global current_room
    current_room = room
    room_label.config(text=f"Current Room: {current_room}")
    client_socket.send(room.encode())

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

# Setup connection to server
def setup_connection():
    global client_socket
    global current_room
    global username
    current_room = "General"
    username = "User"  # Default username for now; this can be asked from the user in future

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 8080))
        threading.Thread(target=receive_messages, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to the server: {str(e)}")

# Change room when selected
rooms_listbox.bind("<ButtonRelease-1>", lambda event: change_room(rooms_listbox.get(rooms_listbox.curselection())))

# Start the connection setup
setup_connection()

# Start the Tkinter event loop
root.mainloop()
