from machine import I2S, Pin
import time
import struct
import socket
import network
import urequests
import select

# 定义 I2S 引脚
INMP441_WS = 25
INMP441_SCK = 26
INMP441_SD = 33
SAMPLE_RATE = 16000  # 设定采样率为 16kHz
BITS_PER_SAMPLE = 16
BUFFER_SIZE = 1024  # 调整缓冲区大小，每次读取 1024 个字节
RECORDING_DURATION = 5  # 录音时长 5 秒
THRESHOLD = 0.01  # 音量阈值
TIMEOUT_DURATION = 30  # 超时时间 30 秒

# 录音文件路径
audio_file = 'ask.raw'

# 配置 INMP441 麦克风的 I2S 输入
i2s_in = I2S(
    0,  # 使用 I2S0
    sck=Pin(INMP441_SCK),
    ws=Pin(INMP441_WS),
    sd=Pin(INMP441_SD),
    mode=I2S.RX,
    bits=BITS_PER_SAMPLE,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=BUFFER_SIZE * 8
)


def get_rms(data):
    """计算 RMS 音量"""
    count = len(data) // 2
    format = "%dh" % count
    shorts = struct.unpack(format, data)
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0 / 32768.0)
        sum_squares += n * n
    return (sum_squares / count) ** 0.5


def start_recording():
    """开始录音并保存到文件"""
    with open(audio_file, 'wb') as f:
        start_time = time.time()
        print("Recording...")
        while time.time() - start_time < RECORDING_DURATION:
            buffer = bytearray(BUFFER_SIZE)
            i2s_in.readinto(buffer)
            f.write(buffer)
        print("Recording finished.")


def send_recording_to_server():
    # 连接到 WiFi
    ssid = 'AI'
    password = '1234567890'

    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)

    while not station.isconnected():
        pass

    print('Connection successful')
    print(station.ifconfig())

    # 创建 Socket 对象并连接到主机
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


def receive_url_from_server():
    # 创建 Socket 服务器等待接收 URL
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12346))  # ESP32 作为服务器，绑定端口 12346
    server_socket.listen(1)

    print('Waiting for URL from host...')

    client_socket = None
    try:
        ready_to_read, _, _ = select.select([server_socket], [], [], TIMEOUT_DURATION)
        if ready_to_read:
            client_socket, addr = server_socket.accept()
            print('Connection from:', addr)
            data = client_socket.recv(1024)
            audio_url = data.decode()
            print('Received URL from server:', audio_url)
            return audio_url
        else:
            print("接收 URL 超时，返回监听逻辑")
            return None
    finally:
        if client_socket:
            client_socket.close()
        server_socket.close()


def play_audio_from_url(audio_url):
    if audio_url is None:
        return
    # 配置 MAX98357A 的 I2S 输出
    sck_pin = Pin(12)  # 串行时钟输出
    ws_pin = Pin(14)  # 字时钟
    sd_pin = Pin(13)  # 串行数据输出

    # 初始化 i2s，针对 tts，rate 要调小一点
    audio_out = I2S(1, sck=sck_pin, ws=ws_pin, sd=sd_pin, mode=I2S.TX, bits=16, format=I2S.MONO, rate=16000, ibuf=20000)

    # 下载音频文件并播放
    try:
        response = urequests.get(audio_url, stream=True)
        response.raw.read(44)  # 跳过开头的 44 字节音频文件头信息

        print("开始播放音频...")

        # 将其写入 I2S DAC
        while True:
            content_byte = response.raw.read(1024)  # 每次读取 1024 个字节

            # 判断 WAV 文件是否结束
            if len(content_byte) == 0:
                break

            # 调用 I2S 对象播放音频
            audio_out.write(content_byte)
    except Exception as ret:
        print("程序产生异常...", ret)
    finally:
        audio_out.deinit()  # 音乐播放完毕后，退出


print("初始化完成，等待 1 秒...")

# 延时 1 秒
time.sleep(1)

print("开始监听音量阈值...")

try:
    while True:
        buffer = bytearray(BUFFER_SIZE)
        i2s_in.readinto(buffer)
        rms = get_rms(buffer)
        print("RMS:", rms)
        if rms > THRESHOLD:
            print("音量超过阈值，开始录音...")
            start_recording()
            send_recording_to_server()
            audio_url = receive_url_from_server()
            play_audio_from_url(audio_url)
except KeyboardInterrupt:
    print("程序中断")
finally:
    i2s_in.deinit()

