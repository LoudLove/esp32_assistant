from http import HTTPStatus
import dashscope

askstr = '请介绍一下通义千问'
dashscope.api_key = 'sk-1*******************8e'

def call_with_messages():
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': askstr }]

    response = dashscope.Generation.call(
        dashscope.Generation.Models.qwen_turbo,
        messages=messages,
        result_format='message',  # 将返回结果格式设置为 message
    )
    if response.status_code == HTTPStatus.OK:
        reply_content = response.output['choices'][0]['message']['content']
        print(reply_content)
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))

if __name__ == '__main__':
    #core askstr->reply_content
    call_with_messages()
