esp32智能语音助手
使用esp32+讯飞开放平台 语音听写（流式版）+阿里灵积模型服务 通义千问qwen-plus+百度智能云  长文本在线合成-基础音库
-------------------------------------------------------------------------------
esp32和主机都连接到手机热点上：
esp32
    Connection successful
    ('192.168.213.63', '255.255.255.0', '192.168.213.214', '192.168.213.214')
主机(windows10笔记本，开发环境pycharm+python3.9)
   IPv4 地址 . . . . . . . . . . . . : 192.168.213.61
   子网掩码  . . . . . . . . . . . . : 255.255.255.0
-------------------------------------------------------------------------------
# 说明esp32，esp-wroom-32（已烧二极管）,esp32-s也行，连线方式：

# esp32 pin13     max98357a DIN
# esp32 pin12     max98357a BCLK
# esp32 pin14     max98357a LRC
# esp32 GND 和 独立供电模块共地，供电在独立供电模块接，不要在esp32上接，容易烧二极管
# 独立供电模块 GND     max98357a GND
# 独立供电模块 5V     max98357a VIN

# esp32 pin26     inmp441 SCK
# esp32 pin25     inmp441 WS
# esp32 pin33     inmp441 SD
# 独立供电模块 GND     inmp441 GND
# 独立供电模块 3.3V     inmp441 VDD
# 独立供电模块 GND      inmp441 L/R

-------------------------------------------------------------------------------
主机：
if __name__ == '__main__':
    server_socket.bind(('192.168.213.61', 12345))  # 绑定主机和端口

def handle_client(client_socket):
    client_socket.connect(('192.168.213.63', 12346))  # 连接ESP32的服务器

-------------------------------------------------------------------------------
esp32:

# 定义 I2S 引脚
INMP441_WS = 25
INMP441_SCK = 26
INMP441_SD = 33

def send_recording_to_server():
    # 连接到 WiFi
    ssid = 'AI'
    password = '1234567890'
    。。。。。
    # 创建 Socket 对象并连接到主机
    host = '192.168.213.61'
    port = 12345  # 确保端口号与你的服务器一致

def receive_url_from_server():
    # 创建 Socket 服务器等待接收 URL
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12346))  # ESP32 作为服务器，绑定端口 12346

def play_audio_from_url(audio_url):
    if audio_url is None:
        return
    # 配置 MAX98357A 的 I2S 输出
    sck_pin = Pin(12)  # 串行时钟输出
    ws_pin = Pin(14)  # 字时钟
    sd_pin = Pin(13)  # 串行数据输出


-------------------------------------------------------------------------------
讯飞api，pcm数据 -》 text
阿里通义千问  text -》 text
百度tts   text -》 wav文件的url
各自的api需要各自看pcm_to_text.py, text2text.py, text_to_wav.py文件