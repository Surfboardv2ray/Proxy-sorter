import base64
import json
import requests
import re
import socket
from urllib.parse import urlparse, parse_qs

def get_country_code(ip_address):
    try:
        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(ip_address)
    except socket.gaierror:
        print(f"Unable to resolve hostname: {ip_address}")
        return None
    except UnicodeError:
        print(f"Hostname violates IDNA rules: {ip_address}")
        return None
    try:
        response = requests.get(f'https://ip-api.colaho6124.workers.dev/{ip_address}')
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

def country_code_to_emoji(country_code):
    # Convert the country code to corresponding Unicode regional indicator symbols
    return ''.join(chr(ord(letter) + 127397) for letter in country_code.upper())

# Counter for all proxies
proxy_counter = 0

# Files for each country code
files = {'IR': open('output/IR.txt', 'w'), 'US': open('output/US.txt', 'w')}

# Set to keep track of the proxies we've seen so far
seen_proxies = set()

def process_vmess(proxy):
    global proxy_counter
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
        flag_emoji = country_code_to_emoji(country_code)
        proxy_counter += 1
        remarks = flag_emoji + country_code + '_' + str(proxy_counter) + '_' + '@Surfboardv2ray'
        proxy_json['ps'] = remarks
        encoded_str = base64.b64encode(json.dumps(proxy_json).encode('utf-8')).decode('utf-8')
        processed_proxy = 'vmess://' + encoded_str
        # Create a unique identifier for the proxy based on the specific attributes
        try:
            proxy_id = (proxy_json['add'], proxy_json['port'], proxy_json['id'], proxy_json['net'], proxy_json['host'], proxy_json['path'], proxy_json['tls'])
        except KeyError as e:
            print(f"Missing attribute in vmess proxy: {e}")
            return None
        # Check if we've seen this proxy before
        if proxy_id in seen_proxies:
            return None
        seen_proxies.add(proxy_id)
        return processed_proxy
    except Exception as e:
        print("Error processing vmess proxy: ", e)
        return None

def process_vless(proxy):
    global proxy_counter
    try:
        # Parse the vless URL
        url = urlparse(proxy)
        # Extract the UUID, IP address, and port
        uuid, ip_address = url.netloc.split('@')
        port = url.port
        # Extract the network, host, and path from the query parameters
        query_params = parse_qs(url.query)
        network = query_params.get('type', [''])[0]
        host = query_params.get('host', [''])[0]
        path = query_params.get('path', [''])[0]
        # Create a unique identifier for the proxy based on the specific attributes
        proxy_id = (uuid, ip_address, port, network, host, path)
        # Check if we've seen this proxy before
        if proxy_id in seen_proxies:
            return None
        seen_proxies.add(proxy_id)
        # Get the country code and generate the remarks
        country_code = get_country_code(ip_address)
        if country_code is None or country_code not in ['US', 'IR']:
            return None
        flag_emoji = country_code_to_emoji(country_code)
        proxy_counter += 1
        remarks = flag_emoji + country_code + '_' + str(proxy_counter) + '_' + '@Surfboardv2ray'
        return proxy.split('#')[0] + '#' + remarks
    except Exception as e:
        print(f"Error processing vless proxy: {e}")
        return None

# Process the proxies and write them to output.txt and the country-specific files
with open('input/proxies.txt', 'r') as f, open('output/converted.txt', 'w') as out_f:
    proxies = f.readlines()
    for proxy in proxies:
        proxy = proxy.strip()
        if proxy.startswith('vmess://'):
            processed_proxy = process_vmess(proxy)
        elif proxy.startswith('vless://'):
            processed_proxy = process_vless(proxy)
        if processed_proxy is not None:
            out_f.write(processed_proxy + '\n')

# Close the country-specific files
for file in files.values():
    file.close()
