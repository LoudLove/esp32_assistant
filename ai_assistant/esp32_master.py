from machine import I2S, Pin
import socket
import time
import network
import urequests

# 定义I2S引脚
INMP441_WS = 25
INMP441_SCK = 26
INMP441_SD = 33
SAMPLE_RATE = 16000  # 设定采样率为16kHz
BITS_PER_SAMPLE = 16
BUFFER_SIZE = 1024  # 调整缓冲区大小，每次读取1024个字节
DURATION = 5  # 录音时长5秒

# 录音文件路径
audio_file = 'ask.raw'

# 配置INMP441麦克风的I2S输入
i2s_in = I2S(
    0,  # 使用I2S0
    sck=Pin(INMP441_SCK),
    ws=Pin(INMP441_WS),
    sd=Pin(INMP441_SD),
    mode=I2S.RX,
    bits=BITS_PER_SAMPLE,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=BUFFER_SIZE * 8
)

# 打开文件以写入二进制数据
with open(audio_file, 'wb') as f:
    start_time = time.time()
    print("Recording...")

    while time.time() - start_time < DURATION:
        # 读取音频数据
        buffer = bytearray(BUFFER_SIZE)
        i2s_in.readinto(buffer)
        f.write(buffer)

    print("Recording finished.")

i2s_in.deinit()

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

# 创建Socket对象并连接到主机
host = '192.168.213.61'
port = 12345  # 确保端口号与你的服务器一致

s = socket.socket()
s.connect((host, port))

print('sending pcm....')
# 发送录音文件
with open(audio_file, 'rb') as f:
    while True:
        buffer = f.read(BUFFER_SIZE)
        if not buffer:
            break
        s.send(buffer)
# 发送结束信号
s.send(b'EOF')
print('sending pcm successfully!')

s.close()

# 创建Socket服务器等待接收URL
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 12346))  # ESP32 作为服务器，绑定端口12346
server_socket.listen(1)

print('Waiting for URL from host...')

client_socket, addr = server_socket.accept()
print('Connection from:', addr)

# 接收处理后的音频URL
data = client_socket.recv(1024)
audio_url = data.decode()
print('Received URL from server:', audio_url)

client_socket.close()
server_socket.close()

# 配置MAX98357A的I2S输出
sck_pin = Pin(12)  # 串行时钟输出
ws_pin = Pin(14)  # 字时钟
sd_pin = Pin(13)  # 串行数据输出

# 初始化i2s，针对tts，rate要调小一点
audio_out = I2S(1, sck=sck_pin, ws=ws_pin, sd=sd_pin, mode=I2S.TX, bits=16, format=I2S.MONO, rate=16000, ibuf=20000)

# 下载音频文件并播放
try:
    response = urequests.get(audio_url, stream=True)
    response.raw.read(44)  # 跳过开头的44字节音频文件头信息

    print("开始播放音频...")

    # 将其写入I2S DAC
    while True:
        content_byte = response.raw.read(1024)  # 每次读取1024个字节

        # 判断WAV文件是否结束
        if len(content_byte) == 0:
            break

        # 调用I2S对象播放音频
        audio_out.write(content_byte)
except Exception as ret:
    print("程序产生异常...", ret)
    audio_out.deinit()

audio_out.deinit()  # 音乐播放完毕后，退出

