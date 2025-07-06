import socket
import threading

HOST = '127.0.0.1'
PORT = 7423


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

name = input("Enter your name : ")


def send_message():
    while True:
        msg = input()
        client.send(msg.encode())

def receive_message():
    while True:
        server_message = client.recv(1024).decode()
        print(server_message)

def talk_to_server():
    #Sending name to the server as the initial message
    client.send(name.encode())

    #Starting receive_message function to fetch and show msgs from server
    thread = threading.Thread(target=receive_message)
    thread.start()

    #Calling the infinite looped function to send message to server
    send_message()

talk_to_server()