import base64
import json
import requests
import re
import socket



def get_country_code(ip_address):
    try:
        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(ip_address)
    except socket.gaierror:
        print("Unable to resolve hostname")
        return None
    response = requests.get(f'https://ip-api.colaho6124.workers.dev/{ip_address}')
    return response.text

def process_vmess(proxy):
    base64_str = proxy.split('://')[1]
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '='* (4 - missing_padding)
    try:
        decoded_str = base64.b64decode(base64_str).decode('utf-8')
        proxy_json = json.loads(decoded_str)
        ip_address = proxy_json['add']
        country_code = get_country_code(ip_address)
        if country_code is None:
            return None
        proxy_json['ps'] = country_code
        encoded_str = base64.b64encode(json.dumps(proxy_json).encode('utf-8')).decode('utf-8')
        return 'vmess://' + encoded_str
    except Exception as e:
        print("Invalid base64 string")
        return None


def process_vless(proxy):
    ip_address = proxy.split('@')[1].split(':')[0]
    country_code = get_country_code(ip_address)
    if country_code is None:
        return None
    return proxy.split('#')[0] + '#' + country_code

with open('input/bugfix.txt', 'r') as f:
    proxies = f.readlines()

output_proxies = []
for proxy in proxies:
    proxy = proxy.strip()
    if proxy.startswith('vmess://'):
        processed_proxy = process_vmess(proxy)
        if processed_proxy is not None:
            output_proxies.append(processed_proxy)
    elif proxy.startswith('vless://'):
        output_proxies.append(process_vless(proxy))

with open('output/bugfix.txt', 'w') as f:
    for proxy in output_proxies:
        f.write(proxy + '\n')
