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
        self.banned = [] #Containing usernames of banned clients
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

            # Assign new admin if the only admin left
            if self.clients and not any(c['isAdmin'] for c in self.clients):
                self.clients[0]['isAdmin'] = True


    class ClientHandler:
        def __init__(self, server_instance, client_socket, client_name, isAdmin):
            self.server = server_instance
            self.socket = client_socket
            self.name = client_name
            self.commands = {
                '!USERLIST_REQUEST': self.handle_userlist,
                '!PRIVATE': self.handle_private,
                '!REPORT': self.handle_report,
                '!DISCONNECT': self.handle_disconnect,
                '!KICK': self.handle_kick,
                '!BAN': self.handle_ban,
                '!UNBAN': self.handle_unban,
                '!ADMIN': self.handle_admin,
                '!DEMOTE': self.handle_demote,
            }

        def is_admin(self):
            return any(c['name'] == self.name and c['isAdmin'] for c in self.server.clients)


        def handle(self, message):
            for prefix, handler in self.commands.items():
                if message.startswith(prefix):
                    return handler(message[len(prefix):].lstrip(':'))
            return False

        def handle_userlist(self, _):
            user_list = [c['name']+' - admin' if c['isAdmin'] else c['name'] for c in self.server.clients]
            self.socket.send(f"!USERLIST:{','.join(user_list)}".encode())
            return True 
        
        def handle_private(self, args):
            recipient, *msg_parts = args.split(':', 1)
            
            if not msg_parts:
                return
            for client in self.server.clients:
                if client['name'] == recipient:
                    client['socket'].send(f"!PRIVATE:{self.name}:{msg_parts[0]}".encode())
                    return True
            #If invalid recipient
            self.socket.send(f"!WARNING:User {recipient} doesn't exist!".encode())
            return True

        def handle_report(self, username):
            self.server.reports.append({
                'reporter': self.name,
                'reported': username,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            for clients in self.server.clients:
                if clients['name'] == username:     #issue: the warning msg is send to the reporter instead of the username
                    self.socket=clients['socket']   #fix: change the client socket to the username socket
                    self.socket.send(f"!WARNING:User {username} reported. Admin notified.".encode())
                else:
                    break

        def handle_disconnect(self, _):
            raise ConnectionAbortedError("Client requested disconnect")
        
        def handle_kick(self, username):
            if self.is_admin() == True:
                if username not in [c['name'] for c in self.server.clients]:
                    self.socket.send(f"!WARNING:User {username} doesn't exist!".encode())
                    return True
                else:
                    for client in self.server.clients:
                        if client['name'] == username:
                            if client['isAdmin']==True:
                                self.socket.send(f"!WARNING:User {username} is an admin, you can't kick an admin!".encode())
                                return True
                            client['socket'].send("You have been kicked by admin!".encode())
                            client['socket'].shutdown(socket.SHUT_RDWR)
                            client['socket'].close()
                    self.server.clients = [client for client in self.server.clients if client['name']!=username]
                    self.server.broadcast(f"User {username} has been kicked by admin {self.name}!")
            else:
                self.socket.send(f"!WARNING:Only admins can kick a user".encode())
            return True
        
        def handle_ban(self, username):
            if self.is_admin() == True:
                if username not in [c['name'] for c in self.server.clients]:
                    self.socket.send(f"!WARNING:User {username} doesn't exist!".encode())
                    return True
                else:
                    for client in self.server.clients:
                        if client['name'] == username:
                            if client['isAdmin']==True:
                                self.socket.send(f"!WARNING:User {username} is an admin, you can't ban an admin!".encode())
                                return True
                            self.server.banned.append(username)
                            client['socket'].send("You have been banned by admin!".encode())
                            self.server.broadcast(f"User {username} has been banned by admin {self.name}!", client)
            else:
                self.socket.send(f"!WARNING:Only admins can ban a user".encode())
            return True
        
        def handle_unban(self, username):
            if self.is_admin() == True:
                if username not in [c['name'] for c in self.server.clients]:
                    self.socket.send(f"!WARNING:User {username} doesn't exist!".encode())
                    return True
                
                else:
                    for client in self.server.clients:
                        if client['name'] == username:
                            if username in self.server.banned:
                                self.server.banned.remove(username)
                                client['socket'].send("You have been unbanned by admin!".encode())
                                self.server.broadcast(f"User {username} has been unbanned by admin {self.name}!", client)
                            else:
                                self.socket.send(f"!WARNING:User {username} isn't banned!".encode())
                        
            else:
                self.socket.send(f"!WARNING:Only admins can unban a user!".encode())
            return True
        
        def handle_admin(self, username):
            if self.is_admin():
                if not self.is_admin():
                    self.socket.send("!WARNING:You're not an admin.".encode())
                    return True
                for client in self.server.clients:
                    if client['name'] == username:
                        client['isAdmin'] = True
                        client['socket'].send(f"{self.name} promoted you to admin!".encode())
                        self.server.broadcast(f"{username} promoted to admin by {self.name}", client)
                        return True
            else:
                self.socket.send("!WARNING:You're not an admin.".encode())
            return True

        def handle_demote(self, _):
            if self.is_admin():
                if self.server.clients and not any(c['isAdmin'] and c['name'] !=self.name for c in self.server.clients):
                    self.socket.send("Make someone else admin before demoting yourself!".encode())
                    return True
                
                for client in self.server.clients:
                    if client['name'] == self.name:
                        client['isAdmin'] = False
                        self.socket.send("You are no longer an admin.".encode())
                        self.server.broadcast(f"{self.name} demoted itself to user!", client)
                        return True
            else:
                self.socket.send("!WARNING:You're not an admin.".encode())
            return True
        
        def process_messages(self):
            try:
                while True:
                    try:
                        message = self.socket.recv(1024).decode()
                        if not message:
                            break
                        elif self.name in self.server.banned:
                            self.socket.send(f"!WARNING:You can't send messages, you're banned from the server.".encode())
                        elif not self.handle(message):
                            self.server.broadcast(f"{self.name}: {message}", sender={'name': self.name})
                    except (ConnectionResetError, ConnectionAbortedError, OSError):
                        break
            except Exception as e:
                print(f"Error with {self.name}: {e}")
            finally:
                self.server.remove_client({'socket': self.socket, 'name': self.name})
                try:
                    self.socket.close()
                except:
                    pass


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
            
            #First client will be the admin by-default
            isAdmin=True if len(self.clients) == 0 else False

            client = {'socket': client_socket, 'name': client_name, 'isAdmin': isAdmin}
            self.clients.append(client)
            
            self.broadcast(f"{client_name} has joined the chat!", client)
            client_socket.send(f"Welcome {client_name}!".encode())

            handler = self.ClientHandler(self, client_socket, client_name, isAdmin)
            thread = threading.Thread(target=handler.process_messages)
            thread.start()

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.accept_connections()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server.close()