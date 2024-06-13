import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.213.63', 8080))

try:
    while True:
        message = input('Enter message to send: ')
        client_socket.send(message.encode())
        data = client_socket.recv(1024)
        print('Received from server:', data.decode())
finally:
    client_socket.close()
