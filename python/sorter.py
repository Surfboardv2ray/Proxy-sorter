import json
import requests
from urllib.parse import urlparse

def set_remarks_from_custom_url(proxy_template, custom_url_base, ip):
    # Construct the custom URL
    custom_url = custom_url_base + ip

    # Make a request to the custom URL
    response = requests.get(custom_url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to get remarks from {custom_url}")
        return proxy_template

    # Parse the response URL and extract the fragment (the remarks)
    remarks = urlparse(response.url).fragment

    # Replace the REMARKS in the proxy template with the extracted remarks
    new_proxy = proxy_template.replace('REMARKS', remarks)

    return new_proxy

def convert_proxies(input_file, output_file, proxy_template, custom_url_base):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            ip = line.strip().split('@')[1].split(':')[0]
            new_proxy = set_remarks_from_custom_url(proxy_template, custom_url_base, ip)
            f_out.write(new_proxy + '\n')

# Usage
proxy_template = 'vless://USERID@IP:PORT?encryption=ENCRYPTION&security=SECURITY&sni=SNI&alpn=ALPN&fp=USERAGENT&type=TYPE&host=HOST&path=PATH#REMARKS'
custom_url_base = 'https://ipinfo.divineglaive.workers.dev/'
convert_proxies('input/vless.txt', 'output/converted.txt', proxy_template, custom_url_base)
