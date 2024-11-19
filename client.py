import socket
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import select

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("900x600")
        self.root.configure(bg="#282c34")
        
        self.client_socket = None
        self.username = ""
        self.current_room = "General"
        self.room_messages = {}  # Store messages for each room
        self.setup_styles()
        self.setup_ui()
        self.setup_connection()
        
    def setup_styles(self):
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

        style.configure(
            "Create.TButton",
            background="#98c379",
            foreground="white",
            font=("Poppins", 12),
            padding=5
        )
        style.map(
            "Create.TButton",
            background=[("active", "#7aa85e")],
            foreground=[("active", "white")]
        )

        style.configure("TListbox", background="#3a3f4b", foreground="white", 
                       font=("Poppins", 12), borderwidth=0)
        style.configure("TLabel", background="#282c34", foreground="white", 
                       font=("Poppins", 12))
        style.configure("TFrame", background="#282c34")
        style.configure("TEntry", font=("Poppins", 14), fieldbackground="#3a3f4b", 
                       foreground="white", relief="flat")
        
    def setup_ui(self):
        # Initialize message history for all rooms
        self.rooms = ["General", "Tech", "Music"]
        for room in self.rooms:
            self.room_messages[room] = []
            
        # Sidebar
        self.sidebar = ttk.Frame(self.root, width=200, style="TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        rooms_label = ttk.Label(self.sidebar, text="Rooms", style="TLabel")
        rooms_label.pack(pady=10)
        
        # # Create Room button
        # create_room_btn = ttk.Button(
        #     self.sidebar,
        #     text="+ Create Room",
        #     style="Create.TButton",
        #     command=self.prompt_create_room
        # )
        # create_room_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame to hold room buttons
        self.room_buttons_frame = ttk.Frame(self.sidebar, style="TFrame")
        self.room_buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_room_buttons()

        # Main Chat Area
        self.main_area = ttk.Frame(self.root, style="TFrame")
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.room_label = ttk.Label(self.main_area, text="Current Room: General", 
                                  style="TLabel")
        self.room_label.pack(anchor=tk.W, padx=10, pady=5)

        self.message_frame = ttk.Frame(self.main_area, style="TFrame")
        self.message_frame.pack(fill=tk.BOTH, expand=True)

        self.message_display = tk.Text(
            self.message_frame,
            bg="#3a3f4b",
            fg="white",
            font=("Poppins", 12),
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.message_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.message_scrollbar = tk.Scrollbar(self.message_frame,
                                            command=self.message_display.yview)
        self.message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.message_display.config(yscrollcommand=self.message_scrollbar.set)

        # Input Area
        self.input_frame = ttk.Frame(self.main_area, style="TFrame")
        self.input_frame.pack(fill=tk.X)

        self.message_entry = ttk.Entry(self.input_frame, style="TEntry")
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_button = ttk.Button(self.input_frame, text="Send", 
                                    command=self.send_message, style="TButton")
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=5)

    def create_room_buttons(self):
        # Clear existing buttons
        for widget in self.room_buttons_frame.winfo_children():
            widget.destroy()
            
        # Create buttons for all rooms
        for room in self.rooms:
            room_button = ttk.Button(
                self.room_buttons_frame, 
                text=room, 
                style="Room.TButton", 
                command=lambda r=room: self.change_room(r)
            )
            room_button.pack(fill=tk.X, padx=10, pady=5)

    def prompt_create_room(self):
        def submit_room():
            room_name = room_entry.get().strip()
            if room_name:
                if room_name in self.rooms:
                    messagebox.showwarning("Error", "Room already exists!")
                else:
                    self.create_new_room(room_name)
                    room_window.destroy()
            else:
                messagebox.showwarning("Input Error", "Room name cannot be empty!")

        room_window = tk.Toplevel(self.root)
        room_window.title("Create New Room")
        room_window.geometry("300x150")
        room_window.configure(bg="#282c34")

        tk.Label(room_window, text="Enter room name:", bg="#282c34", 
                fg="white", font=("Poppins", 12)).pack(pady=10)
        room_entry = tk.Entry(room_window, font=("Poppins", 14), 
                            bg="#3a3f4b", fg="white", relief=tk.FLAT)
        room_entry.pack(pady=10)
        ttk.Button(room_window, text="Create", command=submit_room, 
                  style="Create.TButton").pack(pady=10)

        room_window.transient(self.root)
        room_window.grab_set()

    def create_new_room(self, room_name):
        self.rooms.append(room_name)
        self.room_messages[room_name] = []
        self.create_room_buttons()
        try:
            self.client_socket.send(f"/create_room {room_name}".encode())
            self.change_room(room_name)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to create room: {e}")
            
    def prompt_username(self):
        def submit_username():
            nonlocal username_window
            username = username_entry.get().strip()
            if username:
                self.username = username
                username_window.destroy()
            else:
                messagebox.showwarning("Input Error", "Username cannot be empty!")

        username_window = tk.Toplevel(self.root)
        username_window.title("Enter Username")
        username_window.geometry("300x150")
        username_window.configure(bg="#282c34")

        tk.Label(username_window, text="Enter your username:", bg="#282c34", 
                fg="white", font=("Poppins", 12)).pack(pady=10)
        username_entry = tk.Entry(username_window, font=("Poppins", 14), 
                                bg="#3a3f4b", fg="white", relief=tk.FLAT)
        username_entry.pack(pady=10)
        ttk.Button(username_window, text="Submit", command=submit_username, 
                  style="TButton").pack(pady=10)

        username_window.transient(self.root)
        username_window.grab_set()
        self.root.wait_window(username_window)
            
    def setup_connection(self):
        self.prompt_username()
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 8080))
            self.client_socket.send(f"/username {self.username}".encode())
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to the server: {str(e)}")
    
    def add_message_to_display(self, message):
        self.message_display.config(state=tk.NORMAL)
        formatted_message = message.replace('\\n', '\n')
        self.message_display.insert(tk.END, formatted_message )
        self.message_display.config(state=tk.DISABLED)
        self.message_display.see(tk.END)
            
    def receive_messages(self):
        while True:
            try:
                readable, _, _ = select.select([self.client_socket], [], [], 0.1)
                if readable:
                    message = self.client_socket.recv(1024).decode()
                    if message:
                        if message.startswith("/room_created"):
                            _, room_name = message.split(" ", 1)
                            if room_name not in self.rooms:
                                self.rooms.append(room_name)
                                self.room_messages[room_name] = []
                                self.create_room_buttons()
                        else:
                            self.room_messages[self.current_room].append(message)
                            self.add_message_to_display(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
                
    def change_room(self, room):
        if self.current_room != room:
            self.current_room = room
            self.room_label.config(text=f"Current Room: {self.current_room}")
            
            self.message_display.config(state=tk.NORMAL)
            self.message_display.delete(1.0, tk.END)
            self.message_display.config(state=tk.DISABLED)
            
            # for message in self.room_messages[room]:
            #     self.add_message_to_display(message)
            
            try:
                self.client_socket.send(f"/change_room {room}".encode())
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to switch room: {e}")
                
    def send_message(self):
        message = self.message_entry.get()
        if message.strip():
            try:
                self.client_socket.send(message.encode())
                formatted_message = f"{self.username}: {message}"
                self.room_messages[self.current_room].append(formatted_message)
                self.add_message_to_display(formatted_message)
            except Exception as e:
                messagebox.showerror("Connection Error", 
                                   f"Message could not be sent: {e}")
            self.message_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()