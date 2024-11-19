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
// Add message history storage
struct RoomData {
    std::set<int> clients;
    std::vector<std::string> message_history;
};

std::map<int, std::string> client_usernames;
std::map<int, std::string> client_rooms;
std::map<std::string, RoomData> rooms;
std::mutex clients_mutex;

// Modified send_to_client to handle message history
void send_message_history(int client_socket, const std::string &room) {
    std::lock_guard<std::mutex> lock(clients_mutex);
    if (rooms.find(room) != rooms.end()) {
        for (const auto &message : rooms[room].message_history) {
            send(client_socket, message.c_str(), message.length(), 0);
        }
    }
}

void handle_client(int client_socket) {
    char buffer[1024];
    std::string username;
    std::string current_room = "General";

    {
        std::lock_guard<std::mutex> lock(clients_mutex);
        client_rooms[client_socket] = current_room;
        rooms[current_room].clients.insert(client_socket);
    }

    // Send room history when client joins
    send_message_history(client_socket, current_room);

    while (true) {
        memset(buffer, 0, 1024);
        int bytes_received = recv(client_socket, buffer, 1024, 0);

        if (bytes_received <= 0) {
            std::lock_guard<std::mutex> lock(clients_mutex);
            rooms[current_room].clients.erase(client_socket);
            if (rooms[current_room].clients.empty() && 
                rooms[current_room].message_history.empty()) {
                rooms.erase(current_room);
            }
            client_usernames.erase(client_socket);
            client_rooms.erase(client_socket);
            close(client_socket);
            break;
        }

        std::string message(buffer);

        if (message.find("/username ") == 0) {
            username = message.substr(10);
            std::lock_guard<std::mutex> lock(clients_mutex);
            client_usernames[client_socket] = username;
        }
        else if (message.find("/change_room ") == 0) {
            std::string new_room = message.substr(13);
            {
                std::lock_guard<std::mutex> lock(clients_mutex);
                rooms[current_room].clients.erase(client_socket);
                current_room = new_room;
                client_rooms[client_socket] = current_room;
                rooms[current_room].clients.insert(client_socket);
            }
            // Send history of new room
            send_message_history(client_socket, new_room);
        }
        else {
            std::string full_message = username + ": " + message + "\n";
            std::lock_guard<std::mutex> lock(clients_mutex);
            // Store message in room history
            rooms[current_room].message_history.push_back(full_message);
            // Broadcast to other clients
            for (int client : rooms[current_room].clients) {
                if (client != client_socket) {
                    send(client, full_message.c_str(), full_message.length(), 0);
                }
            }
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
