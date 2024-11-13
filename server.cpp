#include <iostream>
#include <thread>
#include <mutex>
#include <map>
#include <set>
#include <vector>
#include <string>
#include <cstring>
#include <algorithm>
#include <sstream>
#include <netinet/in.h>
#include <unistd.h>

#define PORT 8080
#define BUFFER_SIZE 1024

std::map<int, std::string> client_usernames; // Map client socket -> username
std::map<int, std::string> client_rooms;    // Map client socket -> current room
std::map<std::string, std::set<int>> rooms; // Map room name -> set of client sockets
std::mutex clients_mutex;

// Helper function to send a message to a specific client
void send_to_client(int client_socket, const std::string &message) {
    send(client_socket, message.c_str(), message.length(), 0);
}

// Broadcast a message to all clients in the same room
void broadcast_to_room(const std::string &room, const std::string &message, int sender_socket) {
    std::lock_guard<std::mutex> lock(clients_mutex);

    if (rooms.find(room) != rooms.end()) {
        for (int client_socket : rooms[room]) {
            if (client_socket != sender_socket) { // Don't send to the sender
                send_to_client(client_socket, message);
            }
        }
    }
}

// Handle client messages
void handle_client(int client_socket) {
    char buffer[BUFFER_SIZE];
    std::string username;
    std::string current_room = "General"; // Default room

    {
        std::lock_guard<std::mutex> lock(clients_mutex);
        client_rooms[client_socket] = current_room;
        rooms[current_room].insert(client_socket);
    }

    // Welcome the user
    send_to_client(client_socket, "Welcome to the chat server!\n");
    send_to_client(client_socket, "You have joined the General room.\n");

    while (true) {
        memset(buffer, 0, BUFFER_SIZE);
        int bytes_received = recv(client_socket, buffer, BUFFER_SIZE, 0);

        if (bytes_received <= 0) {
            std::lock_guard<std::mutex> lock(clients_mutex);
            std::cout << "Client disconnected: " << client_socket << std::endl;

            // Remove client from their current room
            rooms[current_room].erase(client_socket);
            if (rooms[current_room].empty()) {
                rooms.erase(current_room);
            }

            client_usernames.erase(client_socket);
            client_rooms.erase(client_socket);
            close(client_socket);
            break;
        }

        std::string message(buffer);
        std::cout << "Received from client " << client_socket << ": " << message << std::endl;

        // Handle special commands
        if (message.find("/username ") == 0) {
            username = message.substr(10);
            std::lock_guard<std::mutex> lock(clients_mutex);
            client_usernames[client_socket] = username;
            send_to_client(client_socket, "Username set to " + username + "\n");
        } else if (message.find("/change_room ") == 0) {
            std::string new_room = message.substr(13);
            {
                std::lock_guard<std::mutex> lock(clients_mutex);

                // Leave current room
                rooms[current_room].erase(client_socket);
                if (rooms[current_room].empty()) {
                    rooms.erase(current_room);
                }

                // Join new room
                current_room = new_room;
                client_rooms[client_socket] = current_room;
                rooms[current_room].insert(client_socket);
            }
            send_to_client(client_socket, "You have joined the room: " + current_room + "\n");
        } else {
            // Broadcast the message to the current room
            std::string full_message = username + ": " + message;
            broadcast_to_room(current_room, full_message, client_socket);
        }
    }
}

// Main server function
int main() {
    int server_socket, client_socket;
    sockaddr_in server_addr{}, client_addr{};
    socklen_t addr_len = sizeof(client_addr);

    // Create socket
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }

    // Bind to port
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Listen for connections
    if (listen(server_socket, 10) < 0) {
        perror("Listen failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    std::cout << "Server started. Listening on port " << PORT << "...\n";

    // Accept client connections in a loop
    while (true) {
        if ((client_socket = accept(server_socket, (struct sockaddr *)&client_addr, &addr_len)) < 0) {
            perror("Accept failed");
            continue;
        }

        std::cout << "New connection: " << client_socket << std::endl;

        // Create a thread to handle the new client
        std::thread(handle_client, client_socket).detach();
    }

    close(server_socket);
    return 0;
}
