from machine import I2S, Pin
import time
import struct

# 定义I2S引脚
INMP441_WS = 25
INMP441_SCK = 26
INMP441_SD = 33
SAMPLE_RATE = 16000  # 设定采样率为16kHz
BITS_PER_SAMPLE = 16
BUFFER_SIZE = 1024  # 调整缓冲区大小，每次读取1024个字节
RECORDING_DURATION = 5  # 录音时长5秒
THRESHOLD = 0.01  # 音量阈值

# 录音文件路径
audio_file = 'tmp.raw'

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

def get_rms(data):
    """计算RMS音量"""
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

print("初始化完成，等待1秒...")

# 延时1秒
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
except KeyboardInterrupt:
    print("程序中断")
finally:
    i2s_in.deinit()

