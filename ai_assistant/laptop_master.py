import socket
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import requests
from http import HTTPStatus
import dashscope

# Global variables for result storage
result_str = ""

# Parameters for various APIs
IFLYTEK_APPID = 'b2***********1'
IFLYTEK_APIKEY = '6b77***************3e35ca'
IFLYTEK_APISECRET = 'OWEwZ*********************************QzZmUy'
AUDIO_FILE = 'ask.raw'
DASHSCOPE_API_KEY = 'sk-19fd******************************ee58e'
ASK_STR = '占位符'
BAIDU_API_KEY = "UQlk********************CyOcqP"
BAIDU_SECRET_KEY = "1OGkj*************************8QQvI"

# WebSocket Parameters for iFlyTek
STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        url = url + '?' + urlencode(v)
        return url

def on_message(ws, message):
    global result_str
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            for i in data:
                for w in i["cw"]:
                    result_str += w["w"]
            print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))
    except Exception as e:
        print("receive msg,but parse exception:", e)

def on_error(ws, error):
    print("### error:", error)

def on_close(ws, a, b):
    print("### closed ###")

def on_open(ws, wsParam):
    def run(*args):
        frameSize = 8000
        intervel = 0.04
        status = STATUS_FIRST_FRAME
        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                if not buf:
                    status = STATUS_LAST_FRAME
                if status == STATUS_FIRST_FRAME:
                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())

def audio_to_text(APPID, APIKey, APISecret, AudioFile):
    global result_str
    result_str = ""
    wsParam = Ws_Param(APPID=APPID, APISecret=APISecret, APIKey=APIKey, AudioFile=AudioFile)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = lambda ws: on_open(ws, wsParam)  # Pass wsParam to on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return result_str

def get_reply_content(askstr, api_key):
    dashscope.api_key = api_key
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': askstr}]
    response = dashscope.Generation.call(
        dashscope.Generation.Models.qwen_turbo,
        messages=messages,
        result_format='message',
    )
    if response.status_code == HTTPStatus.OK:
        reply_content = response.output['choices'][0]['message']['content']
        return reply_content
    else:
        raise Exception('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))

def get_access_token(api_key, secret_key):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception("Failed to obtain access token")

def create_tts_task(access_token, text):
    url = "https://aip.baidubce.com/rpc/2.0/tts/v1/create?access_token=" + access_token
    payload = json.dumps({
        "text": text,
        "format": "wav",
        "voice": 0,
        "lang": "zh",
        "speed": 5,
        "pitch": 5,
        "volume": 5,
        "enable_subtitle": 0
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json().get("task_id")
    else:
        raise Exception("Failed to create TTS task")

def query_tts_result(access_token, task_id):
    url = "https://aip.baidubce.com/rpc/2.0/tts/v1/query?access_token=" + access_token
    payload = json.dumps({
        "task_ids": [task_id]
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        result = response.json().get("tasks_info", [])[0]
        if result.get("task_status") == "Success":
            return result.get("task_result", {}).get("speech_url")
        else:
            raise Exception("TTS task not successful")
    else:
        raise Exception("Failed to query TTS task result")

if __name__ == '__main__':
    try:
        # 创建Socket对象
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('192.168.213.61', 12345))  # 绑定主机和端口
        server_socket.listen(1)

        print('Server is listening...')

        while True:
            client_socket, addr = server_socket.accept()
            print('Connection from:', addr)

            print("接收录音文件")
            # 接收录音文件
            with open(AUDIO_FILE, 'wb') as f:
                while True:
                    data = client_socket.recv(1024)
                    if data.endswith(b'EOF'):
                        f.write(data[:-3])  # 去掉EOF标记
                        break
                    f.write(data)
            print("接收成功")
            client_socket.close()

            # Step 1: Convert audio file to text
            print("Converting audio file to text...")
            text_result = audio_to_text(IFLYTEK_APPID, IFLYTEK_APIKEY, IFLYTEK_APISECRET, AUDIO_FILE)
            print("Text result:", text_result)

            # Step 2: Get reply content from Dashscope
            print("Getting reply content from Dashscope...")
            reply_content = get_reply_content(text_result, DASHSCOPE_API_KEY)
            print("Reply content:", reply_content)

            # Step 3: Convert text to speech URL using Baidu TTS
            print("Converting text to speech URL using Baidu TTS...")
            access_token = get_access_token(BAIDU_API_KEY, BAIDU_SECRET_KEY)
            task_id = create_tts_task(access_token, reply_content)
            time.sleep(10)  # Wait for the TTS task to complete
            speech_url = query_tts_result(access_token, task_id)
            print("Speech URL:", speech_url)

            # 发送URL到ESP32
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('192.168.213.63', 12346))  # 连接ESP32的服务器
            client_socket.send(speech_url.encode())
            client_socket.close()

    except Exception as e:
        print("Error:", str(e))
