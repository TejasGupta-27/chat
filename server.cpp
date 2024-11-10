#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <mutex>
#include <netinet/in.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

struct Client {
    int socket;
    std::string username;
    int room_id;
};

std::vector<std::string> rooms = {"General", "Tech", "Music"};
std::vector<std::vector<Client>> room_clients(rooms.size());
std::unordered_map<int, Client> clients;
std::mutex clients_mutex; // Mutex to protect shared resources

void broadcastMessage(int sender_socket, const std::string& message, int room_id) {
    // Locking the shared room_clients to prevent race conditions
    std::lock_guard<std::mutex> lock(clients_mutex);

    for (const Client& client : room_clients[room_id]) {
        if (client.socket != sender_socket) {
            send(client.socket, message.c_str(), message.length(), 0);
        }
    }
}

void handleClient(int client_socket) {
    char buffer[1024];
    Client client;
    client.socket = client_socket;

    // Ask for username
    send(client_socket, "Enter your username: ", 21, 0);
    int n = recv(client_socket, buffer, sizeof(buffer), 0);
    if (n > 0) {
        client.username = std::string(buffer, n);
    }

    // Ask for room
    send(client_socket, "Enter room (General, Tech, Music): ", 34, 0);
    memset(buffer, 0, sizeof(buffer));
    n = recv(client_socket, buffer, sizeof(buffer), 0);
    if (n > 0) {
        std::string room_name(buffer, n);
        auto it = std::find(rooms.begin(), rooms.end(), room_name);
        client.room_id = (it != rooms.end()) ? std::distance(rooms.begin(), it) : 0; // Default to General
    }

    // Lock the room_clients for thread-safe insertion
    {
        std::lock_guard<std::mutex> lock(clients_mutex);
        room_clients[client.room_id].push_back(client);
        clients[client_socket] = client;
    }

    // Notify the room
    std::string welcome_message = "Welcome to the " + rooms[client.room_id] + " room, " + client.username + "!\n";
    send(client_socket, welcome_message.c_str(), welcome_message.length(), 0);

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        n = recv(client_socket, buffer, sizeof(buffer), 0);
        if (n <= 0) {
            break;
        }
        std::string message = client.username + ": " + std::string(buffer, n);
        broadcastMessage(client_socket, message, client.room_id);
    }

    // Lock for removing the client from the room
    {
        std::lock_guard<std::mutex> lock(clients_mutex);
        room_clients[client.room_id].erase(std::remove_if(room_clients[client.room_id].begin(), room_clients[client.room_id].end(), 
            [client_socket](const Client& c) { return c.socket == client_socket; }), room_clients[client.room_id].end());
        clients.erase(client_socket);
    }
    close(client_socket);
}

int main() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        std::cerr << "Failed to create socket\n";
        return 1;
    }

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(8080);

    if (bind(server_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        std::cerr << "Bind failed\n";
        return 1;
    }

    if (listen(server_fd, 5) == -1) {
        std::cerr << "Listen failed\n";
        return 1;
    }

    std::cout << "Server is listening on port 8080...\n";

    while (true) {
        int client_socket = accept(server_fd, NULL, NULL);
        if (client_socket < 0) {
            std::cerr << "Client accept failed\n";
            continue;
        }

        // Create a new thread to handle the client
        std::thread client_thread(handleClient, client_socket);
        client_thread.detach(); // Detach the thread to let it run independently
    }

    close(server_fd);
    return 0;
}
