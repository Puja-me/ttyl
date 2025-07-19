import socket
import threading
from cryptography.fernet import Fernet

# Configuration
HOST = '127.0.0.1'  # Change to LAN IP for actual LAN connectivity
PORT = 7423
PROTOCOL = "TCP"     # Using TCP which includes 3-way handshake
# Global variables
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
name = ""

public_key=b'6TPrC1hRnL26fp7pA4JBplbaFILCyCNlBHIHmJtW3uY='
public_cipher = Fernet(public_key)
#Fix: For Private messages decryption
#Issue: For every client key was different
#Fix: Shared key (same on all clients)
key = b'SzGcN72UpJh7PhP5hYcvH6H7zhwcr6He9WKfKFAcTrE='
cipher_suite = Fernet(key)

temp_list = {
    'reported_users': [],
    'current_chat': 'public',
    'private_chats': {}
}

def establish_connection():
    try:
        client.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT} via {PROTOCOL}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def get_unique_username():
    global name
    name = input("Enter your username: ")
    client.send(name.encode())
    response = client.recv(1024).decode()
    
    if response.startswith("NAME_EXISTS"):
        suffix = response.split(":")[1]
        name = f"{name}{suffix}"
        print(f"Your username was taken. Assigned new name: {name}")
    elif response == "NAME_ACCEPTED":
        print(f"Username {name} accepted!")
    else:
        print("Unexpected server response")

def encrypt_message(message):
    return cipher_suite.encrypt(message.encode()).decode()

def decrypt_message(encrypted_msg):
    return cipher_suite.decrypt(encrypted_msg.encode()).decode()

#Introduced safe_socket_close to prevent errors
def safe_socket_close():
    """Safely close the socket connection"""
    global running
    running = False
    
    try:
        # Shutdown the socket for both sending and receiving
        client.shutdown(socket.SHUT_RDWR)
    except OSError:
        # Socket might already be closed
        pass
    
    try:
        # Close the socket
        client.close()
    except OSError:
        pass
    
    print("Connection closed safely.")

class ClientCommandHandler:
    def __init__(self, client_socket, cipher_suite):
        self.client = client_socket
        self.cipher = cipher_suite
        self.commands = {
            '/users': self.list_users,
            '/private': self.send_private,
            '/report': self.report_user,
            '/exit': self.exit_chat,
            #Admin commands
            '/kick': self.kick_user,
            '/ban': self.ban_user,
            '/unban': self.unban_user,
            '/admin': self.new_admin,
            '/demote': self.demote_admin
        }
        self.temp_list = {
            'reported_users': [],
            'current_chat': 'public'
        }

    def handle_command(self, msg):
        parts = msg.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in self.commands:
            return self.commands[cmd](args)
        return False  # Not a command

    def list_users(self, _):
        self.client.send("!USERLIST_REQUEST".encode())
        return True

    def send_private(self, args):
        if not args:
            print("Usage: /private username message")
            return True
        
        parts = args.split(' ', 1)
        if len(parts) < 2:
            print("Usage: /private username message")
            return True
            
        recipient, message = parts
        encrypted = self.cipher.encrypt(message.encode()).decode()
        self.client.send(f"!PRIVATE:{recipient}:{encrypted}".encode())
        return True

    def report_user(self, username):
        if not username:
            print("Usage: /report username")
            return True
            
        self.temp_list['reported_users'].append(username)
        self.client.send(f"!REPORT:{username}".encode())
        print(f"User {username} reported to admin")
        return True
    
    def kick_user(self, username):
        if not username:
            print("Usage: /kick username")
            return True
        
        self.client.send(f"!KICK:{username}".encode())
        return True

    def ban_user(self, username):
        if not username:
            print("Usage: /ban username")
            return True
        
        self.client.send(f"!BAN:{username}".encode())
        return True
    
    def unban_user(self, username):
        if not username:
            print("Usage: /ban username")
            return True
        
        self.client.send(f"!UNBAN:{username}".encode())
        return True
    
    def new_admin(self, username):
        if not username:
            print("Usage: /admin username")
            return True
        
        self.client.send(f"!ADMIN:{username}".encode())
        return True
    
    def demote_admin(self , _):
        self.client.send(f"!DEMOTE".encode())
        return True

    def exit_chat(self, _):
        self.client.send("!DISCONNECT".encode())
        self.client.close()
        exit()

def send_message():
    handler = ClientCommandHandler(client, cipher_suite)
    
    while True:
        msg = input()
        if not handler.handle_command(msg):
            # Regular message if not a command
            encrypted_msg = public_cipher.encrypt(msg.encode()).decode()
            client.send(encrypted_msg.encode())


def receive_message():
    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                print("Disconnected from server.")
                exit()
            elif message.startswith("!USERLIST:"):
                users = message[10:].split(',')
                user_list = "\n=== Online Users ===\n"
                for user in users:
                    if user: user_list += f"- {user}\n"
                user_list += "==================="
                print(user_list)

            elif message.startswith("!PRIVATE:"):
                parts = message.split(':', 2)
                sender = parts[1]
                encrypted_msg = parts[2]
                decrypted_msg = decrypt_message(encrypted_msg)
                print(f"\n[PM from {sender}]: {decrypted_msg}\n")
            elif message.startswith("!WARNING:"):
                print(f"\nSERVER WARNING: {message[9:]}\n")
            else:
                if ": " in message:
                    sender, encrypted_part=message.split(": ",1)
                    try:
                        decrypted_msg=public_cipher.decrypt(encrypted_part.encode()).decode()
                        print(f"{sender} : {decrypted_msg}")
                    except Exception:
                        print(message)
                else:
                    try:
                        decrypted_msg=public_cipher.decrypt(message.encode()).decode()
                        print(decrypted_msg)
                    except Exception:
                        print(message)
                
        except Exception as e:
            print(f"Connection error: {e}")
            client.close()
            break

def start_client():
    if not establish_connection():
        return
    
    get_unique_username()
    
    # Start receive thread
    receive_thread = threading.Thread(target=receive_message)
    receive_thread.daemon = True
    receive_thread.start()
    
     # Print help menu
    init_msg = "\n=== Chat Commands ===\n"
    init_msg += "/users - List online users\n"
    init_msg += "/private [user] [msg] - Send private message\n"
    init_msg += "/report [user] - Report a user to admin\n"
    init_msg += "/exit - Leave the chat\n"
    init_msg += "=== Admins only ===\n"
    init_msg += "/kick [user] - Kick a user\n"
    init_msg += "/ban [user] - Ban a user\n"
    init_msg += "/unban [user] - Unban a user\n"
    init_msg += "/admin [user] - Make a user admin\n"
    init_msg += "/demote - Demote itself to user\n"
    init_msg += "====================\n"
    print(init_msg)
    
    # Start sending messages
    send_message()

if __name__ == "__main__":
    try:
        start_client()
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
    finally:
        safe_socket_close()