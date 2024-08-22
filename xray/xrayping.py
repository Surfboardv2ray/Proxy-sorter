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
        self.isSupported = True
        self.isValid = True

    def generate_json_str(self):
        # Simulated method for generating JSON config from raw Xray URL
        return json.dumps({
            "tag": self.tag,
            "streamSettings": {
                "network": "tcp"  # Example; real implementation should decode the URL
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
    except Exception as e:
        print(f"Error in real_delay: {e}")
    return dict(proxy=proxy_name, realDelay_ms=round(delay if delay <= 0 else delay * 1000), is403=(statusCode == 403))

def appendBypassMode(config):
    inbounds = [Inbound("bypass_mode", 3080, "0.0.0.0", "socks", Sniffing(), SocksSettings())] + config.inbounds
    outbounds = [{'tag': 'direct-out', 'protocol': 'freedom'}] + config.outbounds
    rules = [Rule("bypass_mode", "direct-out", [])] + config.routing.rules
    route = XrayRouting("IPIfNonMatch", "hybrid", rules)
    return XrayConfigSimple(inbounds, outbounds, route)

class XrayPing:
    def __init__(self, configs, limit=200):
        self.result = []
        self.actives = []
        self.realDelay_under_1000 = []
        self.realDelay_under_1500 = []
        self.no403_realDelay_under_1000 = []

        confs = [json.loads(c) for c in configs]
        print(f"Parsed {len(confs)} configurations for processing.")  # Debugging statement

        socks = []
        rules = []
        socksPorts = list(set([randint(2000, 49999) for _ in range(len(confs) * 2)]))

        for index, outbound in enumerate(confs):
            socksInbound = Inbound("socks__" + outbound["tag"], socksPorts[index], "0.0.0.0", "socks", Sniffing(), SocksSettings())
            rule = Rule(socksInbound.tag, outbound["tag"], [])
            socks.append(socksInbound)
            rules.append(rule)

        route = XrayRouting("IPIfNonMatch", "hybrid", rules)
        xrayConfig = appendBypassMode(XrayConfigSimple(socks, confs, route))
        configFilePath = "./xray/configs/xray_config_ping.json"
        with open(configFilePath, 'w') as f:
            f.write(json.dumps(xrayConfig, default=lambda x: x.__dict__))

        print(f"Xray configuration file written to {configFilePath}.")  # Debugging statement

        runXrayThread = Thread(target=subprocess.run, args=([Path("xray").resolve(), "run", "-c", configFilePath],))
        runXrayThread.daemon = True
        runXrayThread.start()
        time.sleep(5)

        proxiesSorted = [real_delay(s.port, s.tag.split("__")[1]) for s in socks]
        proxiesSorted = sorted(proxiesSorted, key=lambda d: d['realDelay_ms'])

        print(f"Processed delays for {len(proxiesSorted)} proxies.")  # Debugging statement

        for index, r in enumerate(proxiesSorted):
            r["proxy"] = confs[index]
            self.result.append(r)
            if r["realDelay_ms"] > 0 and len(self.actives) < limit:
                self.actives.append(r)
            if 1000 >= r['realDelay_ms'] > 0 and len(self.realDelay_under_1000) < limit:
                self.realDelay_under_1000.append(r)
                if not r["is403"]:
                    self.no403_realDelay_under_1000.append(r)
            if 1500 >= r['realDelay_ms'] > 0 and len(self.realDelay_under_1500) < limit:
                self.realDelay_under_1500.append(r)

        print(f"Found {len(self.actives)} active proxies under 200ms, {len(self.realDelay_under_1000)} under 1000ms, and {len(self.realDelay_under_1500)} under 1500ms.")  # Debugging statement

# Main script execution
with open("xray/configs/all_configs.txt", 'r') as configsFile:
    urls = configsFile.readlines()
    print(f"Found {len(urls)} URLs in the config file.")  # Debugging statement

    if not urls:
        print("No URLs found in the config file. Exiting.")
        sys.exit(1)

    valid_urls = []
    for url in urls:
        if len(url.strip()) > 10:
            try:
                cusTag = uuid.uuid4().hex
                c = XrayUrlDecoder(url, cusTag)
                if c.isSupported and c.isValid:
                    valid_urls.append(url.strip())
            except Exception as e:
                print(f"There is an error with this proxy => {url}: {e}")

    print(f"Collected {len(valid_urls)} valid URLs.")  # Debugging statement

    delays = XrayPing(valid_urls, 200)

    with open("xray/configs/actives_under_1000ms.txt", 'w') as active1000ProxiesFile:
        for active in delays.realDelay_under_1000:
            active1000ProxiesFile.write(active['proxy']['tag'] + "\n")
    print("Saved active proxies under 1000ms to 'actives_under_1000ms.txt'.")  # Debugging statement

    with open("xray/configs/actives_under_1500ms.txt", 'w') as active1500ProxiesFile:
        for active in delays.realDelay_under_1500:
            active1500ProxiesFile.write(active['proxy']['tag'] + "\n")
    print("Saved active proxies under 1500ms to 'actives_under_1500ms.txt'.")  # Debugging statement

    with open("xray/configs/actives_no_403_under_1000ms.txt", 'w') as active1000no403ProxiesFile:
        for active in delays.no403_realDelay_under_1000:
            active1000no403ProxiesFile.write(active['proxy']['tag'] + "\n")
    print("Saved active proxies under 1000ms with no 403 error to 'actives_no_403_under_1000ms.txt'.")  # Debugging statement

# Xray core file placement
print("Place the 'xray' core executable in the same directory as this script.")  # Debugging statement
