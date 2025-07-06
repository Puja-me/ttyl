import socket
import threading
from random import randint

#Clients list will contain dict with keys client_socket and client_name
clients = []

HOST = '127.0.0.1'
PORT = 7423

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

def broadcast_message(msg, sender=None):
    for client in clients:
        client_name = client['client_name']
        client_socket = client['client_socket']
        if sender is None or client_name != sender['client_name']:
            client_socket.send(msg.encode())

#Function to handle messages from clients
def handle_client(client):
    while True:
        try:
            client_socket = client['client_socket']
            message = client_socket.recv(1024).decode()
            if not message:
                #Disconnect client message if no message received, by default it means the client is no longer connected
                raise Exception(f"{client['client_name']} disconnected!")
            
            broadcast_message(f"{client['client_name']}: {message}", client)

            
        #If client has closed the socket or left the chat
        except Exception as e:
            if client in clients:
                broadcast_message(f"{client['client_name']} has left the chat!", client)
                clients.remove(client)
                break

#Fuction to receive and accept connections from clients
def receive_connections():
    print(f"Server is listening on port {PORT}...")

    while True:
        client_socket, address = server.accept()

        print(f"Connection from: {str(address)}")

        #First message from the client will be the username
        client_name = client_socket.recv(1024).decode()

        # This block checks whether the username already exists; if it does, it appends a random 2-digit number to ensure uniqueness.
        existing_names = [i['client_name'] for i in clients]

        if client_name in existing_names:
            client_socket.send("Username already taken. Assigning you a new name.".encode())
            #This block check the newly generated name if it is also exists already and assign a new
            while True:
                new_name = client_name + str(randint(1, 99))
                if new_name not in existing_names:
                    client_name = new_name
                    break

        client = {'client_name': client_name, 'client_socket': client_socket}
        clients.append(client)

        #Initial connection message
        broadcast_message(f"{client_name} has joined the chat!", client)

        thread = threading.Thread(target=handle_client, args=(client,))

        thread.start()

receive_connections()