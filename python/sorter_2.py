import json
import requests
import socket
import base64
from urllib.parse import urlparse, urlunparse, ParseResult
import ipaddress

def get_ip(host):
    try:
        # Check if the host is an IP address
        ipaddress.ip_address(host)
        return host
    except ValueError:
        # If not, resolve the hostname to an IP address
        try:
            return socket.gethostbyname(host)
        except socket.gaierror:
            print(f"Unable to resolve hostname: {host}")
            return None


def country_code_to_emoji(country_code):
    # Convert the country code to corresponding Unicode
    flag_emoji = ''.join(chr(ord(char) + 127397) for char in country_code.upper())
    return flag_emoji


def set_remarks_from_custom_url(url, custom_url_base, counter):
    if url.startswith('vmess://'):
        try:
            base64_str = url[8:]
            # Calculate the required padding length
            padding_length = (-len(base64_str) % 4)

# Add the correct amount of padding
            base64_str += '=' * padding_length

# Decode the base64 string
            decoded_str = base64.b64decode(base64_str.encode('utf-8', 'ignore')).decode('utf-8')

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Error decoding string: {e}")
            return None, None
        config = json.loads(decoded_str)
        host = config['add']
    else:
        parsed_url = urlparse(url)
        netloc_parts = parsed_url.netloc.split('@', 1)
        if len(netloc_parts) < 2:
            print(f"Invalid URL format: {url}")
            return None, None
        host = netloc_parts[1].split(':', 1)[0]

    ip = get_ip(host)
    if ip is None:
        return None, None

    custom_url = custom_url_base + ip
    response = requests.get(custom_url)

    if response.status_code != 200:
        print(f"Failed to get remarks from {custom_url}")
        return url, None

    country_code = response.text
    country_emoji = country_code_to_emoji(country_code)
    new_remarks = f"{country_emoji}_{country_code}_{counter}_@Surfboardv2ray"

    if url.startswith('vmess://'):
        config['ps'] = new_remarks
        new_url = 'vmess://' + base64.b64encode(json.dumps(config).encode('utf-8', 'ignore')).decode('utf-8')
    else:
        new_parsed_url = ParseResult(
            scheme=parsed_url.scheme,
            netloc=parsed_url.netloc,
            path=parsed_url.path,
            params=parsed_url.params,
            query=parsed_url.query,
            fragment=new_remarks
        )
        new_url = urlunparse(new_parsed_url)

    return new_url, country_code



def convert_proxies(input_file, output_file, ir_file, us_file, custom_url_base):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out, open(ir_file, 'w') as f_ir, open(us_file, 'w') as f_us:
        for counter, line in enumerate(f_in, start=1):
            url = line.strip()
            new_url, country_code = set_remarks_from_custom_url(url, custom_url_base, counter)
            if new_url is None:
                continue
            f_out.write(new_url + '\n')
            if country_code == 'IR':
                f_ir.write(new_url + '\n')
            elif country_code == 'US':
                f_us.write(new_url + '\n')
                
# Usage
custom_url_base = 'https://ip-api.colaho6124.workers.dev/'
convert_proxies('input/proxies.txt', 'output/converted.txt', 'output/IR.txt', 'output/US.txt', custom_url_base)
