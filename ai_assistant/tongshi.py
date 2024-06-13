from machine import I2S, Pin
import time

# 定义I2S引脚
INMP441_WS = 25
INMP441_SCK = 26
INMP441_SD = 33
MAX98357a_LRC = 14
MAX98357a_BCLK = 12
MAX98357a_DIN = 13
SAMPLE_RATE = 16000  # 设定采样率为16kHz
BITS_PER_SAMPLE = 16
BUFFER_SIZE = 512  # 调整缓冲区大小，每次读取512个字节

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

# 配置MAX98357A的I2S输出
i2s_out = I2S(
    1,  # 使用I2S1
    sck=Pin(MAX98357a_BCLK),
    ws=Pin(MAX98357a_LRC),
    sd=Pin(MAX98357a_DIN),
    mode=I2S.TX,
    bits=BITS_PER_SAMPLE,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=BUFFER_SIZE * 8
)

print("开始实时录音和播放...")

try:
    while True:
        # 从麦克风读取音频数据
        buffer = bytearray(BUFFER_SIZE)
        i2s_in.readinto(buffer)
        # 将音频数据写入I2S DAC以播放
        i2s_out.write(buffer)
except KeyboardInterrupt:
    print("播放中断")
finally:
    i2s_in.deinit()
    i2s_out.deinit()

print("播放结束")

