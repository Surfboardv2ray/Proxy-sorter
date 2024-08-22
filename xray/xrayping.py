import sys
sys.path.append('./modules/xray_url_decoder/XrayUrlDecoder.py')
sys.path.append('./modules/clash_meta_url_decoder/')
sys.path.append('./')
sys.path.append('./modules')
sys.path.append('xray/modules/gitRepo.py')

import json
import uuid
from ruamel.yaml import YAML
from modules.gitRepo import commitPushRActiveProxiesFile, getLatestActiveConfigs

from xray_url_decoder.XrayUrlDecoder import XrayUrlDecoder
from modules.XrayPing import XrayPing
from modules.clash_meta_url_decoder.ClashMetaUrlDecoder import ClashMetaDecoder


def is_good_for_game(config: XrayUrlDecoder):
    return (config.type in ['tcp', 'grpc']) and (config.security in [None, "tls"])


# for more info, track this issue https://github.com/MetaCubeX/Clash.Meta/issues/801
def is_buggy_in_clash_meta(config: ClashMetaDecoder):
    return config.security == "reality" and config.type == "grpc"




with open("xray/configs/raw-url/all.txt", 'r') as rowProxiesFile:
    configs = []
    clash_meta_configs = []
    for_game_proxies = []
    for url in rowProxiesFile:
        if len(url) > 10:
            try:
                cusTag = uuid.uuid4().hex

                # ############# xray ############
                c = XrayUrlDecoder(url, cusTag)
                c_json = c.generate_json_str()
                if c.isSupported and c.isValid:
                    configs.append(c_json)

                # ############# clash Meta ##########
                ccm = ClashMetaDecoder(url, cusTag)
                ccm_json = ccm.generate_obj_str()
                if c.isSupported and c.isValid and (not is_buggy_in_clash_meta(ccm)):
                    clash_meta_configs.append(json.loads(ccm_json))

                if is_good_for_game(c):
                    for_game_proxies.append(url)
            except:
                print("There is error with this proxy => " + url)

    # getLatestGoodForGame()
    # with open("xray/configs/row-url/for_game.txt", 'w') as forGameProxiesFile:
    #     for forGame in for_game_proxies:
    #         forGameProxiesFile.write(forGame)
    # commitPushForGameProxiesFile()

    delays = XrayPing(configs, 200)
    getLatestActiveConfigs()

    yaml = YAML()
    with open("xray/configs/clash-meta/all.yaml", 'w') as allClashProxiesFile:
        yaml.dump({"proxies": clash_meta_configs}, allClashProxiesFile)

    with open("xray/configs/clash-meta/actives_under_1000ms.yaml", 'w') as active1000ClashProxiesFile:
        values_to_filter = {d['proxy']['tag'].split("_@_")[0] for d in delays.realDelay_under_1000}
        filtered_array = [item for item in clash_meta_configs if item['name'].split("_@_")[0] in values_to_filter]
        yaml.dump({"proxies": filtered_array}, active1000ClashProxiesFile)

    with open("xray/configs/clash-meta/actives_under_1500ms.yaml", 'w') as active1500ClashProxiesFile:
        values_to_filter = {d['proxy']['tag'].split("_@_")[0] for d in delays.realDelay_under_1500}
        filtered_array = [item for item in clash_meta_configs if item['name'].split("_@_")[0] in values_to_filter]
        yaml.dump({"proxies": filtered_array}, active1500ClashProxiesFile)

    with open("xray/configs/xray-json/actives_all.txt", 'w') as activeProxiesFile:
        for active in delays.actives:
            activeProxiesFile.write(json.dumps(active['proxy']) + "\n")

    with open("xray/configs/xray-json/actives_under_1000ms.txt", 'w') as active1000ProxiesFile:
        for active in delays.realDelay_under_1000:
            active1000ProxiesFile.write(json.dumps(active['proxy']) + "\n")

    with open("xray/configs/xray-json/actives_under_1500ms.txt", 'w') as active1500ProxiesFile:
        for active in delays.realDelay_under_1500:
            active1500ProxiesFile.write(json.dumps(active['proxy']) + "\n")

    with open("xray/configs/xray-json/actives_no_403_under_1000ms.txt", 'w') as active1000no403ProxiesFile:
        for active in delays.no403_realDelay_under_1000:
            active1000no403ProxiesFile.write(json.dumps(active['proxy']) + "\n")

    with open("xray/configs/xray-json/actives_for_ir_server_no403_u1s.txt",
              'w') as active1000no403ForServerProxiesFile:
        for active in delays.no403_realDelay_under_1000:
            if active['proxy']["streamSettings"]["network"] not in ["ws", "grpc"]:
                active1000no403ForServerProxiesFile.write(json.dumps(active['proxy']) + "\n")




commitPushRActiveProxiesFile()
