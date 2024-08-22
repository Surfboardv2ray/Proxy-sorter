import sys
import uuid
import time
import subprocess
from random import randint
from threading import Thread
from pathlib import Path
import requests

# Adjust the sys.path to point to the modules folder
sys.path.append(str(Path(__file__).resolve().parent / 'modules'))

from XrayPing import XrayPing

class XrayUrlDecoder:
    def __init__(self, url, tag):
        self.url = url.strip()
        self.tag = tag
        self.isSupported = True
        self.isValid = True

    def generate_raw_config(self):
        # Simulated method for generating raw config from the Xray URL
        return f"{self.url}#{self.tag}"  # Example; real implementation should decode the URL

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

        # No need for JSON processing, handle configs as raw URLs
        confs = configs  # Already in the required format
        socks = []
        rules = []
        socksPorts = list(set([randint(2000, 49999) for _ in range(len(confs) * 2)]))

        for index, outbound in enumerate(confs):
            socksInbound = Inbound("socks__" + outbound, socksPorts[index], "0.0.0.0", "socks", Sniffing(), SocksSettings())
            rule = Rule(socksInbound.tag, outbound, [])
            socks.append(socksInbound)
            rules.append(rule)

        route = XrayRouting("IPIfNonMatch", "hybrid", rules)
        xrayConfig = appendBypassMode(XrayConfigSimple(socks, confs, route))
        configFilePath = "./xray/configs/xray_config_ping.json"
        with open(configFilePath, 'w') as f:
            f.write(xrayConfig)  # Write raw configurations directly

        runXrayThread = Thread(target=subprocess.run, args=([Path("xray").resolve(), "run", "-c", configFilePath],))
        runXrayThread.daemon = True
        runXrayThread.start()
        time.sleep(5)

        proxiesSorted = [real_delay(s.port, s.tag.split("__")[1]) for s in socks]
        proxiesSorted = sorted(proxiesSorted, key=lambda d: d['realDelay_ms'])

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

# Main script execution
with open("xray/configs/all_configs.txt", 'r') as configsFile:
    urls = []
    for url in configsFile:
        if len(url) > 10:
            try:
                cusTag = uuid.uuid4().hex
                c = XrayUrlDecoder(url, cusTag)
                if c.isSupported and c.isValid:
                    urls.append(c.generate_raw_config())
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
