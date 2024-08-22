import sys
import uuid
import time
import subprocess
from random import randint
from threading import Thread
from pathlib import Path
import requests
import json

# Adjust the sys.path to point to the modules folder
sys.path.append(str(Path(__file__).resolve().parent / 'modules'))

from XrayPing import XrayPing

class XrayUrlDecoder:
    def __init__(self, url, tag):
        self.url = url.strip()
        self.tag = tag

    def generate_json_str(self):
        # Example: Convert raw URL to a simplified Xray JSON config
        return json.dumps({
            "tag": self.tag,
            "streamSettings": {
                "network": "tcp"  # This is a placeholder; modify it to suit your needs
            }
        })

def real_delay(port: int, proxy_name: str):
    test_url = 'http://detectportal.firefox.com/success.txt'
    err_403_url = 'https://open.spotify.com/'
    proxy = f"socks5://127.0.0.1:{port}"
    delay = -1
    statusCode = -1
    try:
        start_time = time.time()
        requests.get(test_url, timeout=10, proxies=dict(http=proxy, https=proxy))
        end_time = time.time()
        delay = end_time - start_time
        err_403_res = requests.get(err_403_url, timeout=10, proxies=dict(http=proxy, https=proxy))
        statusCode = err_403_res.status_code
    except:
        pass
    return dict(proxy=proxy_name, realDelay_ms=round(delay if delay <= 0 else delay * 1000), is403=(statusCode == 403))

class XrayPing:
    def __init__(self, configs, limit=200):
        self.result = []
        self.actives = []
        self.realDelay_under_1000 = []
        self.realDelay_under_1500 = []
        self.no403_realDelay_under_1000 = []

        socksPorts = list(set([randint(2000, 49999) for _ in range(len(configs) * 2)]))

        # For each config, we would ideally start an Xray instance and test the delay
        for index, config in enumerate(configs):
            # Simulate the delay check (you need to have Xray running for real testing)
            delay_result = real_delay(socksPorts[index], config)
            self.result.append(delay_result)
            if delay_result["realDelay_ms"] > 0 and len(self.actives) < limit:
                self.actives.append(delay_result)
            if 1000 >= delay_result['realDelay_ms'] > 0 and len(self.realDelay_under_1000) < limit:
                self.realDelay_under_1000.append(delay_result)
                if not delay_result["is403"]:
                    self.no403_realDelay_under_1000.append(delay_result)
            if 1500 >= delay_result['realDelay_ms'] > 0 and len(self.realDelay_under_1500) < limit:
                self.realDelay_under_1500.append(delay_result)

# Main script execution
with open("xray/configs/all_configs.txt", 'r') as configsFile:
    urls = []
    for url in configsFile:
        if len(url) > 10:
            try:
                cusTag = uuid.uuid4().hex
                c = XrayUrlDecoder(url, cusTag)
                urls.append(c.generate_json_str())
            except Exception as e:
                print(f"There is an error with this proxy => {url}, error: {str(e)}")

    delays = XrayPing(urls, 200)

    with open("xray/configs/actives_under_1000ms.txt", 'w') as active1000ProxiesFile:
        for active in delays.realDelay_under_1000:
            active1000ProxiesFile.write(active['proxy'] + "\n")

    with open("xray/configs/actives_under_1500ms.txt", 'w') as active1500ProxiesFile:
        for active in delays.realDelay_under_1500:
            active1500ProxiesFile.write(active['proxy'] + "\n")

    with open("xray/configs/actives_no_403_under_1000ms.txt", 'w') as active1000no403ProxiesFile:
        for active in delays.no403_realDelay_under_1000:
            active1000no403ProxiesFile.write(active['proxy'] + "\n")

# Xray core file placement
# Place the 'xray' core executable in the same directory as this script.
