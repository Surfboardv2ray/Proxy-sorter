import base64
import json
import socket
import time
import requests

# -----------------------------
# Configuration
# -----------------------------

REQUEST_DELAY = 1.5
RATE_LIMIT_WAIT = 3
MAX_IP_ERRORS = 1

INPUT_FILE = "input/proxies.txt"
OUTPUT_FILE = "output/converted.txt"

session = requests.Session()

next_request_time = 0

proxy_counter = 0

ip_error_counter = {}

dns_cache = {}

country_cache = {}

# -----------------------------
# Helpers
# -----------------------------


def wait_for_rate_limit():
    global next_request_time

    now = time.monotonic()

    if now < next_request_time:
        time.sleep(next_request_time - now)

    next_request_time = time.monotonic() + REQUEST_DELAY


def resolve_hostname(host):

    if host in dns_cache:
        return dns_cache[host]

    try:
        ip = socket.gethostbyname(host)
        dns_cache[host] = ip
        return ip

    except socket.gaierror:
        print(f"Unable to resolve hostname: {host}")

    except UnicodeError:
        print(f"Hostname violates IDNA rules: {host}")

    return None


def get_country_code(host):

    ip = resolve_hostname(host)

    if ip is None:
        return None

    # Cached lookup
    if ip in country_cache:
        return country_cache[ip]

    if ip_error_counter.get(ip, 0) >= MAX_IP_ERRORS:
        print(f"Skipping IP after repeated failures: {ip}")
        return None

    try:

        wait_for_rate_limit()

        response = session.get(
            f"http://ip-api.com/json/{ip}",
            timeout=10
        )

        if response.status_code == 429:

            print("Rate limit reached. Waiting...")

            time.sleep(RATE_LIMIT_WAIT)

            response = session.get(
                f"http://ip-api.com/json/{ip}",
                timeout=10
            )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "success":

            print(f"Lookup failed for {ip}: {data}")

            ip_error_counter[ip] = ip_error_counter.get(ip, 0) + 1

            return None

        country = data.get("countryCode")

        if not country or len(country) != 2:

            print(f"Invalid country code: {country}")

            ip_error_counter[ip] = ip_error_counter.get(ip, 0) + 1

            return None

        country = country.upper()

        country_cache[ip] = country

        return country

    except requests.RequestException as e:

        print(f"Request error for {ip}: {e}")

        ip_error_counter[ip] = ip_error_counter.get(ip, 0) + 1

        return None


def country_code_to_emoji(country):
    return "".join(chr(ord(c) + 127397) for c in country)


# -----------------------------
# Proxy helpers
# -----------------------------


def extract_host(proxy):

    if proxy.startswith("vmess://"):

        encoded = proxy.split("://", 1)[1]

        encoded += "=" * (-len(encoded) % 4)

        try:
            data = json.loads(
                base64.b64decode(encoded).decode("utf-8")
            )

            return data["add"]

        except Exception:
            return None

    elif proxy.startswith("vless://"):

        return proxy.partition("@")[2].partition(":")[0]

    return None


def process_vmess(proxy):

    global proxy_counter

    encoded = proxy.split("://", 1)[1]

    encoded += "=" * (-len(encoded) % 4)

    try:

        data = json.loads(
            base64.b64decode(encoded).decode("utf-8")
        )

        country = get_country_code(data["add"])

        if country is None:
            return None

        proxy_counter += 1

        data["ps"] = (
            f"{country_code_to_emoji(country)}"
            f"{country}_{proxy_counter}_@Surfboardv2ray"
        )

        encoded = base64.b64encode(
            json.dumps(data).encode()
        ).decode()

        return "vmess://" + encoded

    except Exception as e:

        print(f"VMESS error: {e}")

        return None


def process_vless(proxy):

    global proxy_counter

    host = proxy.partition("@")[2].partition(":")[0]

    country = get_country_code(host)

    if country is None:
        return None

    proxy_counter += 1

    remarks = (
        f"{country_code_to_emoji(country)}"
        f"{country}_{proxy_counter}_@Surfboardv2ray"
    )

    return proxy.split("#", 1)[0] + "#" + remarks


# -----------------------------
# Pre-cache unique IPs
# -----------------------------

with open(INPUT_FILE, "r") as f:

    proxies = [line.strip() for line in f]

print(f"Total input lines: {len(proxies)}")

unique_hosts = {
    extract_host(p)
    for p in proxies
    if extract_host(p)
}

print(f"Unique hosts: {len(unique_hosts)}")

print("Resolving countries...")

for host in unique_hosts:
    get_country_code(host)

print(f"Country cache size: {len(country_cache)}")

# -----------------------------
# Process proxies
# -----------------------------

skipped = 0

with open(OUTPUT_FILE, "w") as out:

    for proxy in proxies:

        processed = None

        if proxy.startswith("vmess://"):
            processed = process_vmess(proxy)

        elif proxy.startswith("vless://"):
            processed = process_vless(proxy)

        else:
            skipped += 1
            print("Skipped:", proxy[:80])

        if processed:
            out.write(processed + "\n")

print(f"Skipped lines: {skipped}")
print(f"Processed proxies: {proxy_counter}")

# -----------------------------
# Split by country
# -----------------------------

with open(OUTPUT_FILE) as f:

    with open("output/IR.txt", "w") as ir,\
         open("output/US.txt", "w") as us:

        for line in f:

            if "IR_" in line:
                ir.write(line)

            elif "US_" in line:
                us.write(line)
