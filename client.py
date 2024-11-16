import socket
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import select

# Function to receive messages from the server
def receive_messages():
    while True:
        try:
            readable, _, _ = select.select([client_socket], [], [], 0.1)
            if readable:
                message = client_socket.recv(1024).decode()
                if message:
                    message_list.insert(tk.END, message)
                    message_list.yview(tk.END)
        except Exception as e:
            break

# Function to send a message
def send_message():
    message = message_entry.get()
    if message.strip():
        try:
            client_socket.send(message.encode())
            message_list.insert(tk.END, f"{username}: {message}")
            message_list.yview(tk.END)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Message could not be sent: {e}")
        message_entry.delete(0, tk.END)

# Function to change the chat room
def change_room(room):
    global current_room
    if current_room != room:
        current_room = room
        room_label.config(text=f"Current Room: {current_room}")
        message_list.delete(0, tk.END)
        try:
            client_socket.send(f"/change_room {room}".encode())
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to switch room: {e}")

# Prompt for username
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
    username_window.configure(bg="#282c34")

    tk.Label(username_window, text="Enter your username:", bg="#282c34", fg="white", font=("Poppins", 12)).pack(pady=10)
    username_entry = tk.Entry(username_window, font=("Poppins", 14), bg="#3a3f4b", fg="white", relief=tk.FLAT)
    username_entry.pack(pady=10)
    ttk.Button(username_window, text="Submit", command=submit_username, style="TButton").pack(pady=10)

    username_window.transient(root)
    username_window.grab_set()
    root.wait_window(username_window)

# Setup connection
def setup_connection():
    global client_socket
    global current_room
    current_room = "General"
    prompt_username()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 8080))
        client_socket.send(f"/username {username}".encode())
        threading.Thread(target=receive_messages, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to the server: {str(e)}")

# Function to render room buttons
def create_room_buttons():
    for room in rooms:
        room_button = ttk.Button(
            sidebar, 
            text=room, 
            style="Room.TButton", 
            command=lambda r=room: change_room(r)
        )
        room_button.pack(fill=tk.X, padx=10, pady=5)

# UI Setup
root = tk.Tk()
root.title("Chat Application")
root.geometry("900x600")
root.configure(bg="#282c34")

# Define styles
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TButton", 
    background="#61afef", 
    foreground="white", 
    font=("Poppins", 12), 
    padding=5, 
    borderwidth=0
)
style.map(
    "TButton", 
    background=[("active", "#528fcc")],
    foreground=[("active", "white")]
)

style.configure(
    "Room.TButton", 
    background="#3a3f4b", 
    foreground="white", 
    font=("Poppins", 12, "bold"), 
    padding=10, 
    relief="flat"
)
style.map(
    "Room.TButton", 
    background=[("active", "#61afef"), ("!active", "#3a3f4b")],
    foreground=[("active", "white"), ("!active", "white")]
)

style.configure("TListbox", background="#3a3f4b", foreground="white", font=("Poppins", 12), borderwidth=0)
style.configure("TLabel", background="#282c34", foreground="white", font=("Poppins", 12))
style.configure("TFrame", background="#282c34")
style.configure("TEntry", font=("Poppins", 14), fieldbackground="#3a3f4b", foreground="white", relief="flat")

# Sidebar
sidebar = ttk.Frame(root, width=200, style="TFrame")
sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5)

rooms_label = ttk.Label(sidebar, text="Rooms", style="TLabel")
rooms_label.pack(pady=10)

rooms = ["General", "Tech", "Music"]
create_room_buttons()

# Main Chat Area
main_area = ttk.Frame(root, style="TFrame")
main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

room_label = ttk.Label(main_area, text="Current Room: General", style="TLabel")
room_label.pack(anchor=tk.W, padx=10, pady=5)

message_frame = ttk.Frame(main_area, style="TFrame")
message_frame.pack(fill=tk.BOTH, expand=True)

message_list = tk.Listbox(message_frame, bg="#3a3f4b", fg="white", font=("Poppins", 12), selectmode=tk.SINGLE, relief=tk.FLAT)
message_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

message_scrollbar = tk.Scrollbar(message_frame, command=message_list.yview)
message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
message_list.config(yscrollcommand=message_scrollbar.set)

# Input Area
input_frame = ttk.Frame(main_area, style="TFrame")
input_frame.pack(fill=tk.X)

message_entry = ttk.Entry(input_frame, style="TEntry")
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)

send_button = ttk.Button(input_frame, text="Send", command=send_message, style="TButton")
send_button.pack(side=tk.RIGHT, padx=10, pady=5)

# Start connection setup
setup_connection()

# Tkinter event loop
root.mainloop()
