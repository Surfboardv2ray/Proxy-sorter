import json
import requests
import socket
import base64
from urllib.parse import urlparse, urlunparse, ParseResult

def get_ip(host):
    try:
        # Check if the host is an IP address
        socket.inet_aton(host)
        return host
    except socket.error:
        # If not, resolve the hostname to an IP address
        return socket.gethostbyname(host)

def country_code_to_emoji(country_code):
    # Convert the country code to corresponding Unicode
    flag_emoji = ''.join(chr(ord(char) + 127397) for char in country_code.upper())
    return flag_emoji

def set_remarks_from_custom_url(url, custom_url_base, counter):
    # Check if the URL starts with 'vmess://'
    if url.startswith('vmess://'):
        # Decode the base64 string after 'vmess://'
        decoded_str = base64.b64decode(url[8:]).decode('utf-8')
        config = json.loads(decoded_str)

        # Extract the IP or hostname from the "add" field in the config
        host = config['add']
    else:
        # Parse the vless proxy URL
        parsed_url = urlparse(url)

        # Extract the IP or hostname from the netloc part of the URL
        host = parsed_url.netloc.split('@')[1].split(':')[0]

    # Get the IP address
    ip = get_ip(host)

    # Construct the custom URL
    custom_url = custom_url_base + ip

    # Make a request to the custom URL
    response = requests.get(custom_url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to get remarks from {custom_url}")
        return url

    # The response text is assumed to be the country code
    country_code = response.text

    # Convert the country code to an emoji flag
    country_emoji = country_code_to_emoji(country_code)

    # Append the counter to the country code to create the new remarks
    new_remarks = f"{country_emoji}_{country_code}_{counter}_@Surfboardv2ray"

    if url.startswith('vmess://'):
        # Set the "ps" field in the config to the new remarks
        config['ps'] = new_remarks

        # Re-encode the config back to a base64 string
        new_url = 'vmess://' + base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
    else:
        # Replace the fragment in the original parsed URL with the new remarks
        new_parsed_url = ParseResult(
            scheme=parsed_url.scheme,
            netloc=parsed_url.netloc,
            path=parsed_url.path,
            params=parsed_url.params,
            query=parsed_url.query,
            fragment=new_remarks
        )

        # Convert the new parsed URL back to a string
        new_url = urlunparse(new_parsed_url)

    return new_url

def convert_proxies(input_file, output_file, ir_file, us_file, custom_url_base):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out, open(ir_file, 'w') as f_ir, open(us_file, 'w') as f_us:
        for counter, line in enumerate(f_in, start=1):
            url = line.strip()
            new_url, country_code = set_remarks_from_custom_url(url, custom_url_base, counter)
            f_out.write(new_url + '\n')
            if country_code == 'IR':
                f_ir.write(new_url + '\n')
            elif country_code == 'US':
                f_us.write(new_url + '\n')
                
# Usage
custom_url_base = 'https://ipinfo.dehel15354.workers.dev/'
convert_proxies('input/proxies.txt', 'output/converted.txt', 'output/IR.txt', 'output/US.txt', custom_url_base)
