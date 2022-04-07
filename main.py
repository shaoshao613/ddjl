import json
import time
import urllib
from urllib import parse
from urllib.parse import urlparse

import requests

# 以下涉及叮咚个人信息，建议自行抓包
DDXQSESSID = "***"
# 你家的经纬度
ddmc_longitude = "****"
ddmc_latitude = '****'
# 通知的飞书群的机器人的webhook
notify_url = "https://open.feishu.cn/open-apis/bot/v2/hook/**"


def url2Dict(query):
    return dict([(k, parse.unquote(v[0])) for k, v in parse.parse_qs(query).items()])


def get_time_str():
    return time.strftime("%Y{y}%m{m}%d{d} %H:%M", time.localtime(time.time())).format(y='年', m='月', d='日')


def get_ddxq_cookie():
    return {
        'DDXQSESSID': DDXQSESSID,
    }


def get_ddxq_header():
    return {
        'Host': 'maicai.api.ddxq.mobi',
        'ddmc-city-number': '0101',
        'referer': 'https://servicewechat.com/wx1e113254eda17715/421/page-frame.html',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.12(0x18000c2b) NetType/WIFI Language/zh_CN',
        'ddmc-api-version': '9.49.1',
        'ddmc-build-version': '2.81.4',
        'ddmc-app-client-id': '4',
        'accept-language': 'zh-cn',
        'ddmc-channel': 'applet',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded',
        'ddmc-os-version': '[object Undefined]',
    }


def get_ddxq_station():
    params = {
        'uid': '624e46dde51a800001cb07f1',
        'longitude': ddmc_longitude,
        'latitude': ddmc_latitude,
        'city_number': '0101',
        'api_version': '9.49.1',
        'app_version': '2.81.4',
        'applet_source': '',
        'channel': 'applet',
        'app_client_id': '4',
        'sharer_uid': '',
    }
    response = requests.get('https://sunquan.api.ddxq.mobi/api/v2/user/location/refresh/',
                            params=params)
    return json.loads(response.content)


def get_ddxq_available_time(station_id):
    data = {
        'longitude': ddmc_longitude,
        'latitude': ddmc_latitude,
        'station_id': station_id,
        'city_number': '0101',
        'api_version': '9.49.1',
        'app_version': '2.81.4',
        'channel': 'applet',
        'app_client_id': '4',
        'products': '[[{}]]',
        'isBridge': 'false',
    }
    response = requests.post('https://maicai.api.ddxq.mobi/order/getMultiReserveTime', headers=get_ddxq_header(),
                             cookies=get_ddxq_cookie(),
                             data=urllib.parse.urlencode(data))
    result = json.loads(response.content)
    return result


def send_msg_feishu(text):
    if "https://open.feishu.cn" in notify_url and "*" not in notify_url:
        payload_message = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", notify_url, headers=headers, data=json.dumps(payload_message))
        return json.loads(response.content)


def is_full(times):
    is_time_full_flag = True
    msg = ""
    for time_item in times:
        if not time_item["fullFlag"]:
            is_time_full_flag = False
        msg += f"{time_item['arrival_time_msg']} {time_item['textMsg']} "
    return is_time_full_flag, msg


if __name__ == '__main__':
    if "*" in ddmc_longitude:
        ddmc_longitude = input("请输入你家的经度，比如121.468629:")
    if "*" in ddmc_latitude:
        ddmc_latitude = input("请输入你家的纬度，比如31.25919:")
    station_id = get_ddxq_station()['data']['station_id']
    station_name = get_ddxq_station()['data']['station_info']['name']
    print(f"你的站点为{station_name}")

    if "*" in DDXQSESSID:
        DDXQSESSID = input("请输入你叮咚的登录DDXQSESSID(自行抓包）"
                           ":")
    if "*" in notify_url:
        notify_url = input("请输入飞书通知的链接:")

    for i in range(1, 10000):
        dd_time = get_ddxq_available_time(station_id)
        if dd_time.get("success", False) is False:
            error_msg = f'叮咚登录故障:{dd_time.get("msg", "报错了")}'
            print(error_msg)
            send_msg_feishu(error_msg)
            break
        is_full_flag, msg = is_full(dd_time['data'][0]['time'][0]['times'])
        if not is_full_flag:
            send_msg_feishu(f"你们小区{station_name}叮咚有运力了，别上班了，快抢菜")
            time.sleep(5 * 60)
        print(f"{get_time_str()} 已监控{station_name}{i}次,{msg}")
        time.sleep(60)
