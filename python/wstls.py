import base64
import json
import urllib.parse

def filter_proxies():
    with open('output/converted.txt', 'r') as f:
        proxies = f.readlines()

    filtered_proxies = []
    for proxy in proxies:
        proxy = proxy.strip()
        if proxy.startswith('vmess://'):
            base64_str = proxy.split('vmess://')[1]
            proxy_info = base64.b64decode(base64_str).decode('utf-8')
            proxy_dict = json.loads(proxy_info)

            if proxy_dict.get('tls') == 'tls' and proxy_dict.get('net') == 'ws' and proxy_dict.get('port') == '443':
                filtered_proxies.append(proxy)
        elif proxy.startswith('vless://'):
    proxy_info = proxy.split('vless://')[1]
    url_parts = urllib.parse.urlparse('http://' + proxy_info)
    query_params = urllib.parse.parse_qs(url_parts.query)

    if query_params.get('port') == ['443'] and query_params.get('security') == ['tls'] and query_params.get('type') == ['ws']:
        filtered_proxies.append(proxy)


    with open('ws_tls/proxies/wstls', 'w') as f:
        for proxy in filtered_proxies:
            f.write(proxy + '\n')

if __name__ == '__main__':
    filter_proxies()
