"""Yerel Qwen3 sunucusuyla terminal sohbeti. Çıkış: /exit, temizleme: /reset."""
import json
import urllib.error
import urllib.request

URL = 'http://127.0.0.1:18086/v1/chat/completions'


def main():
    messages = []
    print('Qwen3 hazır. /exit: çıkış, /reset: sohbeti temizle')
    while True:
        try:
            prompt = input('\nSen: ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if prompt in ('/exit', '/quit'):
            return
        if prompt == '/reset':
            messages.clear()
            print('Sohbet temizlendi.')
            continue
        if not prompt:
            continue
        pending = messages + [{'role': 'user', 'content': prompt}]
        payload = {'model': 'qwen3-30b-a3b-erotic-q4', 'messages': pending,
                   'stream': True, 'max_tokens': 1024, 'temperature': 0.7,
                   'chat_template_kwargs': {'enable_thinking': False}}
        request = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                         headers={'Content-Type': 'application/json'})
        answer = ''
        try:
            print('Model: ', end='', flush=True)
            with urllib.request.urlopen(request, timeout=300) as response:
                for raw in response:
                    line = raw.decode().strip()
                    if not line.startswith('data: '):
                        continue
                    if line == 'data: [DONE]':
                        break
                    data = json.loads(line[6:])
                    choices = data.get('choices', [])
                    token = (choices[0].get('delta', {}).get('content') or '') if choices else ''
                    answer += token
                    print(token, end='', flush=True)
            print()
            messages = pending + [{'role': 'assistant', 'content': answer}]
        except urllib.error.HTTPError as error:
            print('\nSunucu hatası:', error.read().decode(errors='replace'))
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print('\nBağlantı hatası:', error)
        except KeyboardInterrupt:
            print('\nYanıt kesildi. Yeni mesaj yazabilir veya /exit kullanabilirsin.')


if __name__ == '__main__':
    main()
