import base64
import json
import socket
import time
import requests
import ipaddress
import os
import maxminddb


# -----------------------------
# Configuration
# -----------------------------

INPUT_FILE = "input/proxies.txt"
OUTPUT_FILE = "output/converted.txt"

DATABASE_FILE = "databases/dbip-country-lite.mmdb"

TEMP_DIR = "temp"

TEMP0 = f"{TEMP_DIR}/temp0_configs.txt"
TEMP1 = f"{TEMP_DIR}/temp1_hosts.json"
TEMP2 = f"{TEMP_DIR}/temp2_ips.json"

REQUEST_DELAY = 1.5
MAX_API_ERRORS = 3

API_SERVICES = [
    "ipwho.is",
    "ipapi.co",
    "ip-api.com",
    "ip.guide",
    "ip.sb"
]


session = requests.Session()

next_request_time = 0

proxy_counter = 0

dns_cache = {}

country_cache = {}

api_error_counter = {}

api_index = 0


os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)


# -----------------------------
# Rate limiting
# -----------------------------


def wait_rate():

    global next_request_time

    now = time.monotonic()

    if now < next_request_time:
        time.sleep(next_request_time - now)

    next_request_time = time.monotonic() + REQUEST_DELAY



# -----------------------------
# IP validation
# -----------------------------


def is_private_ip(ip):

    try:

        addr = ipaddress.ip_address(ip)

        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_reserved
            or addr.is_link_local
            or addr.is_multicast
        )

    except Exception:

        return True



# -----------------------------
# DNS
# -----------------------------


def resolve_hostname(host):

    if host in dns_cache:
        return dns_cache[host]


    try:

        ip = socket.gethostbyname(host)

        dns_cache[host] = ip

        return ip


    except Exception as e:

        print(
            f"DNS resolution failed: {host} | {e}"
        )

        return None



# -----------------------------
# Local DB lookup
# -----------------------------


def lookup_local_database(ip):

    try:

        reader = maxminddb.open_database(
            DATABASE_FILE
        )


    except Exception as e:

        print(
            "FAILED opening DB-IP database:",
            e
        )

        return None


    try:

        result = reader.get(ip)

        reader.close()


        if not result:
            return None


        country = (
            result
            .get("country", {})
            .get("iso_code")
        )


        if country:

            return country.upper()


    except Exception as e:

        print(
            f"Database lookup failed {ip}: {e}"
        )


    return None



# -----------------------------
# API lookup
# -----------------------------


def api_lookup(ip):

    global api_index


    if api_error_counter.get(ip, 0) >= MAX_API_ERRORS:

        print(
            f"Skipping API lookup for {ip}"
        )

        return None



    start_index = api_index


    while True:


        service = API_SERVICES[api_index]


        api_index = (
            api_index + 1
        ) % len(API_SERVICES)



        try:

            wait_rate()


            print(
                f"Querying API: {service} -> {ip}"
            )



            if service == "ipwho.is":

                r = session.get(
                    f"https://ipwho.is/{ip}",
                    timeout=10
                )

                data = r.json()

                country = data.get(
                    "country_code"
                )



            elif service == "ipapi.co":

                r = session.get(
                    f"https://ipapi.co/{ip}/json/",
                    timeout=10
                )

                data = r.json()

                country = data.get(
                    "country"
                )



            elif service == "ip-api.com":

                r = session.get(
                    f"http://ip-api.com/json/{ip}",
                    timeout=10
                )

                data = r.json()

                country = data.get(
                    "countryCode"
                )



            elif service == "ip.guide":

                r = session.get(
                    f"https://ip.guide/{ip}",
                    timeout=10
                )

                data = r.json()

                country = (
                    data
                    .get("location", {})
                    .get("country_code")
                )



            elif service == "ip.sb":

                r = session.get(
                    f"https://api.ip.sb/geoip/{ip}",
                    timeout=10
                )

                data = r.json()

                country = data.get(
                    "country_code"
                )



            else:

                country = None



            if country and len(country) == 2:

                return country.upper()



            raise Exception(
                "No country returned"
            )



        except Exception as e:


            print(
                f"API failed {service} {ip}: {e}"
            )


            api_error_counter[ip] = (
                api_error_counter.get(ip,0)+1
            )


            if api_index == start_index:

                return None



# -----------------------------
# Main country resolver
# -----------------------------


def get_country(ip):


    if ip in country_cache:

        return country_cache[ip]


    if is_private_ip(ip):

        return None



    print(
        f"Querying local database: {ip}"
    )


    country = lookup_local_database(ip)


    if country:

        country_cache[ip] = country

        return country



    print(
        f"Local DB failed, using APIs: {ip}"
    )


    country = api_lookup(ip)


    if country:

        country_cache[ip] = country


    return country



# -----------------------------
# Extract hosts
# -----------------------------


def extract_host(proxy):

    try:

        if proxy.startswith("vmess://"):

            encoded = proxy.split("://")[1]

            encoded += "=" * (
                -len(encoded)%4
            )

            data = json.loads(
                base64.b64decode(encoded)
                .decode()
            )

            return data["add"]



        if proxy.startswith("vless://"):

            return (
                proxy
                .partition("@")[2]
                .partition(":")[0]
            )


    except Exception as e:

        print(
            "Extract host failed:",
            e
        )


    return None



# -----------------------------
# temp0
# -----------------------------


with open(INPUT_FILE) as f:

    original = [
        x.strip()
        for x in f
        if x.strip()
    ]


unique_configs = list(
    dict.fromkeys(original)
)


with open(TEMP0,"w") as f:

    f.write(
        "\n".join(unique_configs)
    )


print(
    "Configs deduplicated and saved temp0."
)

print(
    f"Number of configs: {len(original)}"
)

print(
    f"Number deduplicated: {len(unique_configs)}"
)



# -----------------------------
# temp1
# -----------------------------


hosts=[]


for i,p in enumerate(unique_configs):

    host=extract_host(p)

    if host:

        hosts.append(
            {
                "id":i,
                "host":host
            }
        )


with open(TEMP1,"w") as f:

    json.dump(
        hosts,
        f,
        indent=2
    )


print(
    f"Extracted hosts: {len(hosts)}"
)



# -----------------------------
# temp2
# -----------------------------


ips=[]


for item in hosts:

    host=item["host"]


    if is_private_ip(host):

        continue


    ip=host


    try:

        ipaddress.ip_address(ip)

    except:

        ip=resolve_hostname(host)



    if ip and not is_private_ip(ip):

        ips.append(
            {
                "id":item["id"],
                "ip":ip
            }
        )


with open(TEMP2,"w") as f:

    json.dump(
        ips,
        f,
        indent=2
    )


print(
    f"Resolved IPs saved temp2: {len(ips)}"
)



# -----------------------------
# Resolve countries
# -----------------------------


for item in ips:

    get_country(
        item["ip"]
    )


print(
    f"Countries resolved: {len(country_cache)}"
)



# -----------------------------
# Build output
# -----------------------------


id_to_country={}


for item in ips:

    country = country_cache.get(
        item["ip"]
    )

    if country:

        id_to_country[
            item["id"]
        ] = country



with open(OUTPUT_FILE,"w") as out:


    for index,proxy in enumerate(unique_configs):


        country = id_to_country.get(index)


        if not country:

            continue


        proxy_counter += 1


        remark = (
            f"{''.join(chr(ord(c)+127397) for c in country)}"
            f"{country}_{proxy_counter}_@Surfboardv2ray"
        )


        if proxy.startswith("vmess://"):

            encoded = proxy.split("://")[1]

            encoded += "=" * (
                -len(encoded)%4
            )

            data=json.loads(
                base64.b64decode(encoded)
                .decode()
            )

            data["ps"]=remark


            encoded=base64.b64encode(
                json.dumps(data)
                .encode()
            ).decode()


            out.write(
                "vmess://"+encoded+"\n"
            )


        else:

            out.write(
                proxy.split("#")[0]
                +"#"
                +remark
                +"\n"
            )



print(
    f"Finished. Output configs: {proxy_counter}"
)
