import socket
import threading
from random import randint
from datetime import datetime

class ChatServer:
    def __init__(self, host='127.0.0.1', port=7423):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.reports = []
        self.setup_server()

    def setup_server(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f"Server listening on {self.host}:{self.port}")

    def broadcast(self, message, sender=None):
        for client in self.clients:
            if sender and client['name'] == sender['name']:
                continue
            try:
                client['socket'].send(message.encode())
            except:
                self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
            self.broadcast(f"{client['name']} has left the chat.")

    class ClientHandler:
        def __init__(self, server_instance, client_socket, client_name):
            self.server = server_instance
            self.socket = client_socket
            self.name = client_name
            self.commands = {
                '!USERLIST_REQUEST': self.handle_userlist,
                '!PRIVATE': self.handle_private,
                '!REPORT': self.handle_report,
                '!DISCONNECT': self.handle_disconnect
            }

        def handle(self, message):
            for prefix, handler in self.commands.items():
                if message.startswith(prefix):
                    #Issue: Making recipient empty as ':' prefix was still there
                    #Fix: Removed unwanted ':' from very left side (prefix)
                    return handler(message[len(prefix):].lstrip(':'))
            return False

        def handle_userlist(self, _):
            user_list = [c['name'] for c in self.server.clients]
            self.socket.send(f"!USERLIST:{','.join(user_list)}".encode())

        def handle_private(self, args):
            recipient, *msg_parts = args.split(':', 1)
            
            if not msg_parts:
                return
            for client in self.server.clients:
                if client['name'] == recipient:
                    client['socket'].send(f"!PRIVATE:{self.name}:{msg_parts[0]}".encode())
                    break
            #Issue: Broadcasting Private msgs
            #Fix:  self.handle(message) was returning false even for Private msgs, return True will output True, telling it's a private message and not to broadcast
            return True

        def handle_report(self, username):
            self.server.reports.append({
                'reporter': self.name,
                'reported': username,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.socket.send(f"!WARNING:User {username} reported. Admin notified.".encode())

        def handle_disconnect(self, _):
            raise ConnectionAbortedError("Client requested disconnect")

        def process_messages(self):
            try:
                while True:
                    message = self.socket.recv(1024).decode()
                    if not message:
                        break
                    if not self.handle(message):
                        self.server.broadcast(f"{self.name}: {message}", sender={'name': self.name})
            except ConnectionAbortedError:
                print(f"{self.name} requested disconnect")
            except Exception as e:
                print(f"Error with {self.name}: {e}")
            finally:
                self.server.remove_client({'socket': self.socket, 'name': self.name})
                self.socket.close()

    def accept_connections(self):
        while True:
            client_socket, addr = self.server.accept()
            client_name = client_socket.recv(1024).decode()

            # Handle duplicate names
            existing_names = [c['name'] for c in self.clients]
            if client_name in existing_names:
                suffix = str(randint(10, 99))
                client_socket.send(f"NAME_EXISTS:{suffix}".encode())
                client_name = f"{client_name}{suffix}"
            else:
                client_socket.send("NAME_ACCEPTED".encode())

            client = {'socket': client_socket, 'name': client_name}
            self.clients.append(client)
            
            self.broadcast(f"{client_name} has joined the chat!")
            client_socket.send(f"Welcome {client_name}! Commands: /users, /private, /report".encode())

            handler = self.ClientHandler(self, client_socket, client_name)
            thread = threading.Thread(target=handler.process_messages)
            thread.start()

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.accept_connections()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server.close()