import base64
import json
import requests
import re
import socket
import os
import time


# Rate limit settings for ip-api.com
REQUEST_DELAY = 1.5
RATE_LIMIT_WAIT = 3
MAX_IP_ERRORS = 1

last_request_time = 0

ip_error_counter = {}


def get_country_code(ip_address):
    global last_request_time

    try:
        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(ip_address)
    except socket.gaierror:
        print(f"Unable to resolve hostname: {ip_address}")
        return None
    except UnicodeError:
        print(f"Hostname violates IDNA rules: {ip_address}")
        return None


    # Skip IPs that repeatedly fail
    if ip_error_counter.get(ip_address, 0) >= MAX_IP_ERRORS:
        print(f"Skipping IP after multiple errors: {ip_address}")
        return None


    try:

        # Respect ip-api.com rate limit
        elapsed = time.time() - last_request_time

        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)


        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=10
        )

        last_request_time = time.time()


        # Rate limit hit
        if response.status_code == 429:

            print(
                f"Rate limit reached. Waiting {RATE_LIMIT_WAIT} seconds..."
            )

            time.sleep(RATE_LIMIT_WAIT)


            response = requests.get(
                f'http://ip-api.com/json/{ip_address}',
                timeout=10
            )


        response.raise_for_status()


        data = response.json()


        if data.get("status") != "success":
            print(
                f"API lookup failed for {ip_address}: {data}"
            )

            ip_error_counter[ip_address] = (
                ip_error_counter.get(ip_address, 0) + 1
            )

            return None


        country_code = data.get("countryCode")


        if not country_code or len(country_code) != 2:

            print(
                f"Invalid country code for {ip_address}: {country_code}"
            )

            ip_error_counter[ip_address] = (
                ip_error_counter.get(ip_address, 0) + 1
            )

            return None


        return country_code.upper()


    except requests.exceptions.RequestException as e:

        print(
            f"Error sending request for {ip_address}: {e}"
        )

        ip_error_counter[ip_address] = (
            ip_error_counter.get(ip_address, 0) + 1
        )

        return None



def country_code_to_emoji(country_code):
    # Convert the country code to corresponding Unicode regional indicator symbols
    return ''.join(chr(ord(letter) + 127397) for letter in country_code.upper())



# Counter for all proxies
proxy_counter = 0



def process_vmess(proxy):
    global proxy_counter

    base64_str = proxy.split('://')[1]

    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)

    try:
        decoded_str = base64.b64decode(base64_str).decode('utf-8')
        proxy_json = json.loads(decoded_str)

        ip_address = proxy_json['add']

        country_code = get_country_code(ip_address)

        if country_code is None:
            return None

        flag_emoji = country_code_to_emoji(country_code)

        proxy_counter += 1

        remarks = (
            flag_emoji
            + country_code
            + '_'
            + str(proxy_counter)
            + '_'
            + '@Surfboardv2ray'
        )

        proxy_json['ps'] = remarks

        encoded_str = base64.b64encode(
            json.dumps(proxy_json).encode('utf-8')
        ).decode('utf-8')

        processed_proxy = 'vmess://' + encoded_str

        return processed_proxy

    except Exception as e:
        print("Error processing vmess proxy:", e)
        return None



def process_vless(proxy):
    global proxy_counter

    ip_address = proxy.split('@')[1].split(':')[0]

    country_code = get_country_code(ip_address)

    if country_code is None:
        return None

    flag_emoji = country_code_to_emoji(country_code)

    proxy_counter += 1

    remarks = (
        flag_emoji
        + country_code
        + '_'
        + str(proxy_counter)
        + '_'
        + '@Surfboardv2ray'
    )

    processed_proxy = proxy.split('#')[0] + '#' + remarks

    return processed_proxy



# Process the proxies and write them to converted.txt
with open('input/proxies.txt', 'r') as f, open('output/converted.txt', 'w') as out_f:

    proxies = f.readlines()

    print("Total input lines:", len(proxies))

    skipped = 0

    for proxy in proxies:

        # Important: reset every iteration
        processed_proxy = None

        proxy = proxy.strip()

        if proxy.startswith('vmess://'):
            processed_proxy = process_vmess(proxy)

        elif proxy.startswith('vless://'):
            processed_proxy = process_vless(proxy)

        else:
            skipped += 1
            print("Skipped line:", proxy[:80])

        if processed_proxy is not None:
            out_f.write(processed_proxy + '\n')


    print("Skipped lines:", skipped)
    print("Total processed proxies:", proxy_counter)



# Read from converted.txt and separate the proxies based on country code
with open('output/converted.txt', 'r') as in_f:

    proxies = in_f.readlines()

    with open('output/IR.txt', 'w') as ir_f, open('output/US.txt', 'w') as us_f:

        for proxy in proxies:

            if 'IR_' in proxy:
                ir_f.write(proxy)

            elif 'US_' in proxy:
                us_f.write(proxy)
