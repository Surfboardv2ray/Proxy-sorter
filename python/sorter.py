import base64
import json
import re
import os

# Global variable to keep track of processed proxies
proxy_counter = 0

def rename_vmess_address(proxy, new_address):
    global proxy_counter
    base64_str = proxy.split('://')[1]
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    try:
        decoded_str = base64.b64decode(base64_str).decode('utf-8')
        print("Decoded VMess proxy JSON:", decoded_str)  # Debugging
        proxy_json = json.loads(decoded_str)
        proxy_json['add'] = new_address
        proxy_counter += 1
        encoded_str = base64.b64encode(json.dumps(proxy_json).encode('utf-8')).decode('utf-8')
        renamed_proxy = 'vmess://' + encoded_str
        print("Renamed VMess proxy:", renamed_proxy)  # Debugging
        return renamed_proxy
    except Exception as e:
        print("Error processing vmess proxy: ", e)
        return None

def rename_vless_address(proxy, new_address):
    global proxy_counter
    try:
        parts = proxy.split('@')
        userinfo = parts[0]
        hostinfo = parts[1]
        hostinfo_parts = hostinfo.split(':')
        hostinfo_parts[0] = new_address
        hostinfo = ':'.join(hostinfo_parts)
        renamed_proxy = userinfo + '@' + hostinfo
        proxy_counter += 1
        print("Renamed VLess proxy:", renamed_proxy)  # Debugging
        return renamed_proxy
    except Exception as e:
        print("Error processing vless proxy: ", e)
        return None

def process_proxies(input_file, output_file, new_address):
    with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
        proxies = f.readlines()
        for proxy in proxies:
            proxy = proxy.strip()
            if proxy.startswith('vmess://'):
                renamed_proxy = rename_vmess_address(proxy, new_address)
            elif proxy.startswith('vless://'):
                renamed_proxy = rename_vless_address(proxy, new_address)
            if renamed_proxy is not None:
                out_f.write(renamed_proxy + '\n')

# Example usage
input_file = 'StarStruck/Star'
output_file = 'StarStruck/StarRenamed'
new_address = '188.114.97.161'

process_proxies(input_file, output_file, new_address)
