import socket
import threading

#Clients list will contain dict with keys client_socket and client_name
clients = []

temp_arg = []

commands = {
    '/help': lambda: broadcast_message("Available commands: /help, /exit, /about, /report <username>, /changename <new-username>"),
    '/exit': lambda: clients.remove(temp_arg[0]) #temp_arg[0] is the client in this case
}

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

            #This func will check for commands in the message
            if  message.split()[0] in [cmd for cmd in commands.keys()]:
                temp_arg.append(client, message.split()[1]) #adding argument to temp_arg
                commands[message.split()[0]]() #calling the lambda command
                temp_arg.clear() #Making the temp_arg empty again
            
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

        #This function is checking whether the user already exists or not.
        #This algorithm can be enhanced ***
        if client_name in [i['client_name'] for i in clients]:
            client_socket.send("Username already taken. Connection closed.".encode())
            client_socket.close() #Closing the socket if username already exists
            continue

        client = {'client_name': client_name, 'client_socket': client_socket}
        clients.append(client)

        #Initial connection message
        broadcast_message(f"{client_name} has joined the chat!")

        thread = threading.Thread(target=handle_client, args=(client,))

        thread.start()

receive_connections()