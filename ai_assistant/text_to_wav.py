import requests
import json

API_KEY = "UQ***************************qP"
SECRET_KEY = "1O**********************************I"


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
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


def main():
    # core text --> speech_url
    text = "1234收到vv都被别人echo my heart"
    try:
        access_token = get_access_token()
        task_id = create_tts_task(access_token, text)
        print("Task created with ID:", task_id)
        # 等待任务完成
        import time
        time.sleep(10)  # 适当延迟，等待任务完成
        speech_url = query_tts_result(access_token, task_id)
        print("Speech URL:", speech_url)
    except Exception as e:
        print("Error:", str(e))


if __name__ == '__main__':
    main()
