import network
import socket

# 连接到WiFi
ssid = 'AI'
password = '1234567890'

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    pass

print('Connection successful')
print(station.ifconfig())

# 设置服务器
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('192.168.213.63', 8080))
server_socket.listen(1)

print('Waiting for a connection...')
conn, addr = server_socket.accept()
print('Connection from', addr)

while True:
    data = conn.recv(1024)
    if not data:
        break
    print('Received:', data.decode())
    response = 'ACK: ' + data.decode()
    conn.send(response.encode())

conn.close()
server_socket.close()

