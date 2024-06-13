import wave
import struct
import os

# 设定参数
SAMPLE_RATE = 16000  # 采样率为16kHz
BITS_PER_SAMPLE = 16
CHANNELS = 1  # 单声道
DURATION = 5  # 录音时长5秒
BUFFER_SIZE = 1024  # 缓冲区大小，每次读取1024个字节

# 读取RAW音频文件
raw_file = 'ask.raw'
wav_file = 'ask.wav'

# 计算总帧数
expected_num_frames = SAMPLE_RATE * DURATION
frame_size = CHANNELS * (BITS_PER_SAMPLE // 8)
expected_byte_count = expected_num_frames * frame_size

# 检查原始文件大小
actual_byte_count = os.path.getsize(raw_file)

if actual_byte_count < expected_byte_count:
    print(f"警告：文件大小 ({actual_byte_count} 字节) 小于预期 ({expected_byte_count} 字节)。文件可能不完整。")
    # 根据实际录音数据调整DURATION
    DURATION = actual_byte_count // (SAMPLE_RATE * frame_size)
elif actual_byte_count > expected_byte_count:
    print(f"警告：文件大小 ({actual_byte_count} 字节) 大于预期 ({expected_byte_count} 字节)。文件可能包含额外数据。")

# 创建WAV文件
with wave.open(wav_file, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(BITS_PER_SAMPLE // 8)
    wf.setframerate(SAMPLE_RATE)

    with open(raw_file, 'rb') as rf:
        while True:
            data = rf.read(BUFFER_SIZE)
            if not data:
                break
            wf.writeframes(data)

print(f"转换完成: {wav_file}")
