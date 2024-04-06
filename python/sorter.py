import json
import requests
from urllib.parse import urlparse, urlunparse, ParseResult

def set_remarks_from_custom_url(url, custom_url_base):
    # Parse the vless proxy URL
    parsed_url = urlparse(url)

    # Extract the IP from the netloc part of the URL
    ip = parsed_url.netloc.split('@')[1].split(':')[0]

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

    # Replace the fragment in the original parsed URL with the new remarks
    new_parsed_url = ParseResult(
        scheme=parsed_url.scheme,
        netloc=parsed_url.netloc,
        path=parsed_url.path,
        params=parsed_url.params,
        query=parsed_url.query,
        fragment=country_code
    )

    # Convert the new parsed URL back to a string
    new_url = urlunparse(new_parsed_url)

    return new_url

def convert_proxies(input_file, output_file, custom_url_base):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            url = line.strip()
            new_url = set_remarks_from_custom_url(url, custom_url_base)
            f_out.write(new_url + '\n')

# Usage
custom_url_base = 'https://ipinfo.divineglaive.workers.dev/'
convert_proxies('input/vless.txt', 'output/converted.txt', custom_url_base)
