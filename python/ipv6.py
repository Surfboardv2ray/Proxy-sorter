import base64
import json
import re
import requests

# Configuration URLs
config_urls = [
    "https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/refs/heads/main/submerge/converted.txt",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/refs/heads/main/configtg.txt",
#    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/my.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://github.com/Surfboardv2ray/v2ray-worker-sub/raw/refs/heads/master/providers/providers",
]

# Helper functions
def is_base64(s):
    try:
        return base64.b64encode(base64.b64decode(s)).decode() == s
    except Exception:
        return False

def is_ipv6(address):
    return re.match(r'^[0-9a-fA-F:]+$', address) and ':' in address

def parse_config(line):
    line = line.strip()
    if line.startswith("vmess://"):
        config = line[8:]
        if is_base64(config):
            try:
                config_json = json.loads(base64.b64decode(config))
                if is_ipv6(config_json.get("add", "")):
                    return line
            except json.JSONDecodeError:
                print(f"Invalid JSON format in vmess config.")
    elif any(line.startswith(proto) for proto in ["vless://", "trojan://", "ss://", "hy2://", "hysteria2://", "tuic://"]):
        at_index = line.find('@')
        if at_index != -1:
            ip_port_part = line[at_index + 1:]
            if ip_port_part.startswith("["):
                end_bracket_index = ip_port_part.find("]")
                if end_bracket_index > -1:
                    ip = ip_port_part[1:end_bracket_index]
                    if is_ipv6(ip):
                        return line
            else:
                colon_index = ip_port_part.find(":")
                if colon_index > -1:
                    ip = ip_port_part[:colon_index]
                    if is_ipv6(ip):
                        return line
    return None

# Fetch and filter configurations
def fetch_and_filter_configs():
    ipv6_configs = []
    for url in config_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            text = response.text
            lines = base64.b64decode(text).decode().split('\n') if is_base64(text.strip()) else text.split('\n')
            for line in lines:
                valid_config = parse_config(line)
                if valid_config:
                    ipv6_configs.append(valid_config)
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
    return ipv6_configs

# Save to files
def save_configs(ipv6_configs):
    with open("custom/ipv6.txt", "w") as f_ipv6, open("custom/ipv64.txt", "w") as f_ipv64:
        ipv6_data = "\n".join(ipv6_configs)
        f_ipv6.write(ipv6_data)
        f_ipv64.write(base64.b64encode(ipv6_data.encode()).decode())

# Main execution
if __name__ == "__main__":
    ipv6_configs = fetch_and_filter_configs()
    save_configs(ipv6_configs)
    print("Configs saved to ipv6.txt and ipv64.txt")
