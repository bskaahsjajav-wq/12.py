#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█  N U K E   B O X   ·   S I N G U L A R I T Y   E N G I N E  █
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""

import os
import sys
import time
import ssl
import json
import math
import random
import string
import hashlib
import re
import threading
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
import requests
import gc
import paho.mqtt.client as mqtt

# ══════════════════════════════════════════════════════════════
#  ANSI ENGINE
# ══════════════════════════════════════════════════════════════
E  = "\033["
R  = E + "0m"
HC = E + "?25l"
SC = E + "?25h"

try:
    import shutil
    _W = shutil.get_terminal_size((80, 24)).columns
    W = max(40, min(_W - 2, 70))
except Exception:
    W = 66


def rgb(r, g, b):
    return f"{E}38;2;{r};{g};{b}m"


def hue2rgb(h, s=1.0, v=1.0):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, max(0, min(1, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def grad(text, h0=0.0, h1=0.15, sat=1.0, val=1.0):
    n = max(len(text) - 1, 1)
    out = []
    for i, c in enumerate(text):
        h = h0 + (h1 - h0) * (i / n)
        r, g, b = hue2rgb(h, sat, val)
        out.append(rgb(r, g, b) + c)
    return "".join(out) + R


def gradw(text, h0=0.0, h1=0.15, sat=0.95, base=0.62, amp=0.38,
          freq=0.45, phase=0.0):
    n = max(len(text) - 1, 1)
    out = []
    for i, c in enumerate(text):
        h = h0 + (h1 - h0) * (i / n)
        v = base + amp * (0.5 + 0.5 * math.sin(i * freq - phase))
        r, g, b = hue2rgb(h, sat, v)
        out.append(rgb(r, g, b) + c)
    return "".join(out) + R


def cls():
    sys.stdout.write(E + "2J" + E + "3J" + E + "H")
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  BANNER & FLAME
# ══════════════════════════════════════════════════════════════
NUKE_ART = [
    "  ███╗   ██╗██╗   ██╗██╗  ██╗███████╗",
    "  ████╗  ██║██║   ██║██║ ██╔╝██╔════╝",
    "  ██╔██╗ ██║██║   ██║█████╔╝ █████╗  ",
    "  ██║╚██╗██║██║   ██║██╔═██╗ ██╔══╝  ",
    "  ██║ ╚████║╚██████╔╝██║  ██╗███████╗",
    "  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝",
]


def banner_flame(frame):
    lines = [""]
    for i, l in enumerate(NUKE_ART):
        row = []
        for j, c in enumerate(l):
            t = j / max(len(l) - 1, 1)
            h = 0.02 + t * 0.10
            base_v = 0.65 + 0.20 * math.sin(j * 0.4 - frame * 0.5 + i * 0.3)
            spot = (frame * 0.6 + i * 2) % (len(l) + 10) - 5
            d = abs(j - spot)
            bump = math.exp(-(d * d) / 6)
            v = min(1.0, base_v + bump * 0.35)
            r, g, b = hue2rgb(h, 0.95, v)
            row.append(rgb(r, g, b) + c)
        lines.append("".join(row) + R)
    return lines


def flame_strip(width, frame, hue=0.02):
    chars = ["░", "▒", "▓", "█", "▓", "▒", "░"]
    out = []
    for i in range(width):
        t = i / max(width - 1, 1)
        wave = 0.5 + 0.5 * math.sin(i * 0.35 + frame * 0.6)
        idx = int(wave * (len(chars) - 1))
        v = 0.4 + 0.55 * wave
        r, g, b = hue2rgb(hue + t * 0.08, 1.0, v)
        out.append(rgb(r, g, b) + chars[idx])
    return "".join(out) + R


def radar(frame, size=13):
    cx = cy = (size - 1) / 2
    angle = (frame * 0.35) % (2 * math.pi)
    out = []
    for y in range(size):
        row = []
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = math.sqrt(dx * dx + dy * dy)
            if d > cx + 0.5:
                row.append(" ")
                continue
            a = math.atan2(dy, dx) % (2 * math.pi)
            diff = min(abs(a - angle), 2 * math.pi - abs(a - angle))
            if diff < 0.35 and d < cx:
                row.append(rgb(255, 60, 30) + "█")
            elif diff < 0.9 and d < cx:
                row.append(rgb(200, 90, 20) + "▓")
            elif d < 1.2:
                row.append(rgb(255, 255, 200) + "◉")
            elif d > cx - 0.8:
                row.append(rgb(120, 30, 10) + "·")
            elif (x + y) % 4 == 0:
                row.append(rgb(80, 20, 15) + "·")
            else:
                row.append(" ")
        out.append("".join(row) + R)
    return out


def spin_symbols(frame):
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    return frames[frame % len(frames)]


# ══════════════════════════════════════════════════════════════
#  CORE FACEBOOK
# ══════════════════════════════════════════════════════════════
def parse_cookie_string(cookie_string):
    d = {}
    for c in cookie_string.split(";"):
        if "=" in c:
            k, v = c.strip().split("=", 1)
            d[k] = v
    return d


def generate_offline_threading_id():
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))


def get_headers(url, customHeader=None):
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.facebook.com/",
        "Host": urlparse(url).netloc,
        "Origin": "https://www.facebook.com",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 "
                      "Mobile Safari/537.36",
        "Connection": "keep-alive",
    }
    if customHeader:
        headers.update(customHeader)
    return headers


def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))


def generate_session_id():
    return random.randint(1, 2 ** 53)


def generate_client_id():
    def gen(n):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))
    return gen(8) + '-' + gen(4) + '-' + gen(4) + '-' + gen(4) + '-' + gen(12)


def tenbox(newTitle, threadID, dataFB):
    try:
        message_id = generate_offline_threading_id()
        timestamp = int(time.time() * 1000)
        form_data = {
            "client": "mercury",
            "action_type": "ma-type:log-message",
            "author": f"fbid:{dataFB['FacebookID']}",
            "thread_id": str(threadID),
            "timestamp": timestamp,
            "timestamp_relative": str(int(time.time())),
            "source": "source:chat:web",
            "source_tags[0]": "source:chat",
            "offline_threading_id": message_id,
            "message_id": message_id,
            "threading_id": generate_offline_threading_id(),
            "thread_fbid": str(threadID),
            "thread_name": str(newTitle),
            "log_message_type": "log:thread-name",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }
        r = requests.post(
            "https://www.facebook.com/messaging/set_thread_name/",
            data=form_data,
            headers=get_headers("https://www.facebook.com",
                                {"Content-Length": str(len(form_data))}),
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════
#  CLASS: fbTools
# ══════════════════════════════════════════════════════════════
class fbTools:
    def __init__(self, dataFB):
        self.dataFB = dataFB
        self.last_seq_id = None

    def getAllThreadList(self):
        dataForm = {
            "fb_dtsg": self.dataFB["fb_dtsg"],
            "jazoest": self.dataFB["jazoest"],
            "__a": 1,
            "__user": str(self.dataFB["FacebookID"]),
            "__req": "1",
            "__rev": self.dataFB["clientRevision"],
            "av": self.dataFB["FacebookID"],
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3336396659757871",
                    "query_params": {
                        "limit": 20, "before": None,
                        "tags": ["INBOX"],
                        "includeDeliveryReceipts": False,
                        "includeSeqID": True,
                    }
                }
            })
        }
        try:
            r = requests.post(
                "https://www.facebook.com/api/graphqlbatch/",
                data=dataForm,
                headers=get_headers("https://www.facebook.com/api/graphqlbatch/",
                                    {"Content-Type": "application/x-www-form-urlencoded"}),
                cookies=parse_cookie_string(self.dataFB["cookieFacebook"]),
                timeout=15)
            txt = r.text
            if txt.startswith("for(;;);"):
                txt = txt[9:]
            if not txt.strip():
                return False
            first = txt.split("\n")[0]
            data = json.loads(first)
            if "o0" in data and "data" in data["o0"]:
                viewer = data["o0"]["data"].get("viewer", {})
                if "message_threads" in viewer:
                    self.last_seq_id = viewer["message_threads"]["sync_sequence_id"]
                    return True
        except Exception:
            pass
        return False


# ══════════════════════════════════════════════════════════════
#  CLASS: MessageSender
# ══════════════════════════════════════════════════════════════
class MessageSender:
    THEMES = [
        {"id": "3650637715209675", "name": "Besties"},
        {"id": "769656934577391", "name": "Women's History"},
        {"id": "702099018755409", "name": "Dune"},
        {"id": "1480404512543552", "name": "Avatar"},
        {"id": "741311439775765", "name": "Love"},
        {"id": "215565958307259", "name": "Bob Marley"},
        {"id": "194982117007866", "name": "Football"},
        {"id": "1743641112805218", "name": "Soccer"},
        {"id": "730357905262632", "name": "Mean Girls"},
        {"id": "1270466356981452", "name": "Wonka"},
        {"id": "704702021720552", "name": "Pizza"},
        {"id": "1013083536414851", "name": "Wish"},
        {"id": "359537246600743", "name": "Trolls"},
        {"id": "2317258455139234", "name": "One Piece"},
        {"id": "6685081604943977", "name": "1989"},
        {"id": "1508524016651271", "name": "Avocado"},
        {"id": "265997946276694", "name": "Loki"},
        {"id": "6584393768293861", "name": "olivia rodrigo"},
        {"id": "845097890371902", "name": "Baseball"},
        {"id": "292955489929680", "name": "Lollipop"},
        {"id": "6026716157422736", "name": "Basketball"},
        {"id": "390127158985345", "name": "Chill"},
        {"id": "365557122117011", "name": "Support"},
        {"id": "339021464972092", "name": "Music"},
        {"id": "1060619084701625", "name": "Lo-Fi"},
        {"id": "3190514984517598", "name": "Sky"},
        {"id": "627144732056021", "name": "Celebration"},
        {"id": "275041734441112", "name": "Care"},
        {"id": "3082966625307060", "name": "Astrology"},
        {"id": "539927563794799", "name": "Cottagecore"},
        {"id": "527564631955494", "name": "Ocean"},
        {"id": "230032715012014", "name": "Tie-Dye"},
        {"id": "788274591712841", "name": "Monochrome"},
        {"id": "3259963564026002", "name": "Default"},
        {"id": "724096885023603", "name": "Berry"},
        {"id": "624266884847972", "name": "Candy"},
        {"id": "273728810607574", "name": "Unicorn"},
        {"id": "262191918210707", "name": "Tropical"},
        {"id": "2533652183614000", "name": "Maple"},
        {"id": "909695489504566", "name": "Sushi"},
        {"id": "582065306070020", "name": "Rocket"},
        {"id": "557344741607350", "name": "Citrus"},
        {"id": "1257453361255152", "name": "Rose"},
        {"id": "571193503540759", "name": "Lavender"},
        {"id": "2873642949430623", "name": "Tulip"},
        {"id": "403422283881973", "name": "Apple"},
        {"id": "3022526817824329", "name": "Peach"},
        {"id": "672058580051520", "name": "Honey"},
        {"id": "3151463484918004", "name": "Kiwi"},
        {"id": "193497045377796", "name": "Grape"},
    ]

    def __init__(self, fbt, dataFB):
        self.fbt = fbt
        self.dataFB = dataFB
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.lastSeqID = None

    def get_last_seq_id(self):
        if self.fbt.getAllThreadList():
            self.lastSeqID = self.fbt.last_seq_id

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc != 0:
            return
        client.subscribe([("/t_ms", 0)])
        queue = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self.dataFB['FacebookID']
        }
        topic = "/messenger_sync_create_queue"
        queue["initial_titan_sequence_id"] = self.lastSeqID
        queue["device_params"] = None
        client.publish(topic, json_minimal(queue), qos=1, retain=False)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        pass

    def connect_mqtt(self):
        if not self.lastSeqID:
            return False
        session_id = generate_session_id()
        user = {
            "u": self.dataFB["FacebookID"],
            "s": session_id,
            "chat_on": json_minimal(True),
            "fg": False,
            "d": generate_client_id(),
            "ct": "websocket",
            "aid": 219994525426954,
            "mqtt_sid": "",
            "cp": 3,
            "ecp": 10,
            "st": ["/t_ms", "/messenger_sync_get_diffs", "/messenger_sync_create_queue"],
            "pm": [], "dc": "", "no_auto_fg": True, "gas": None, "pack": [],
        }
        host = f"wss://edge-chat.messenger.com/chat?region=eag&sid={session_id}"
        self.mqtt = mqtt.Client(client_id="mqttwsclient", clean_session=True,
                                protocol=mqtt.MQTTv31, transport="websockets")
        self.mqtt.tls_set(certfile=None, keyfile=None,
                          cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.mqtt.on_connect = self._on_connect
        self.mqtt.on_disconnect = self._on_disconnect
        self.mqtt.username_pw_set(username=json_minimal(user))
        parsed = urlparse(host)
        self.mqtt.ws_set_options(
            path=f"{parsed.path}?{parsed.query}",
            headers={
                "Cookie": self.dataFB['cookieFacebook'],
                "Origin": "https://www.messenger.com",
                "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U)",
                "Referer": "https://www.messenger.com/",
                "Host": "edge-chat.messenger.com",
            })
        try:
            self.mqtt.connect(host="edge-chat.messenger.com", port=443, keepalive=10)
            self.mqtt.loop_start()
            time.sleep(1.5)
            return True
        except Exception:
            return False

    def stop(self):
        try:
            if self.mqtt:
                self.mqtt.disconnect()
                self.mqtt.loop_stop()
        except Exception:
            pass

    def create_poll(self, title, options, thread_id):
        if self.mqtt is None:
            return False
        self.ws_req_number += 1
        self.ws_task_number += 1
        task = {
            "failure_count": None,
            "label": "163",
            "payload": json.dumps({
                "question_text": title,
                "thread_key": thread_id,
                "options": options,
                "sync_group": 1,
            }, separators=(",", ":")),
            "queue_name": "poll_creation",
            "task_id": self.ws_task_number,
        }
        content = {
            "app_id": "2220391788200892",
            "payload": json.dumps({
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [task],
                "version_id": "7158486590867448",
            }, separators=(",", ":")),
            "request_id": self.ws_req_number,
            "type": 3,
        }
        try:
            self.mqtt.publish("/ls_req", json.dumps(content, separators=(",", ":")),
                              qos=1, retain=False)
            return True
        except Exception:
            return False

    def set_theme(self, theme_id, thread_id):
        if self.mqtt is None:
            return False
        self.ws_req_number += 1
        self.ws_task_number += 1
        task = {
            "failure_count": None,
            "label": "43",
            "payload": json.dumps({
                "thread_key": thread_id,
                "theme_fbid": theme_id,
                "source": None,
                "sync_group": 1,
                "payload": None,
            }, separators=(",", ":")),
            "queue_name": "thread_theme",
            "task_id": self.ws_task_number,
        }
        content = {
            "app_id": "2220391788200892",
            "payload": json.dumps({
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [task],
                "version_id": "25095469420099952",
            }, separators=(",", ":")),
            "request_id": self.ws_req_number,
            "type": 3,
        }
        try:
            self.mqtt.publish("/ls_req", json.dumps(content, separators=(",", ":")),
                              qos=1, retain=False)
            return True
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════
#  CLASS: ngquanghuyakadzi — lấy fb_dtsg y nguyên zin1.py
# ══════════════════════════════════════════════════════════════
class ngquanghuyakadzi:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except Exception:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        urls = [
            'https://www.facebook.com',
            'https://mbasic.facebook.com',
            'https://m.facebook.com'
        ]
        for url in urls:
            try:
                print(f"[*] Thử lấy fb_dtsg từ {url}")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    print(f"[❌] Yêu cầu tới {url} thất bại, mã trạng thái: {response.status_code}")
                    continue
                fb_dtsg_patterns = [
                    r'"token":"(.*?)"',
                    r'name="fb_dtsg" value="(.*?)"',
                    r'"fb_dtsg":"(.*?)"',
                    r'fb_dtsg=([^&"]+)'
                ]
                jazoest_pattern = r'name="jazoest" value="(\d+)"'
                rev_pattern = r'"__rev":"(\d+)"'
                fb_dtsg = None
                for pattern in fb_dtsg_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        fb_dtsg = match.group(1)
                        break
                jazoest_match = re.search(jazoest_pattern, response.text)
                rev_match = re.search(rev_pattern, response.text)
                if fb_dtsg:
                    self.fb_dtsg = fb_dtsg
                    self.jazoest = jazoest_match.group(1) if jazoest_match else "22036"
                    self.rev = rev_match.group(1) if rev_match else "1015919737"
                    print(f"[✓] Lấy được fb_dtsg: {self.fb_dtsg}, jazoest: {self.jazoest}, rev: {self.rev}")
                    return
                else:
                    print(f"[⚠] Không tìm thấy fb_dtsg trong {url}")
            except Exception as e:
                print(f"[❌] Lỗi khi truy cập {url}: {str(e)}")
                time.sleep(2)
        raise Exception("Không thể lấy được fb_dtsg từ bất kỳ URL nào")


# ══════════════════════════════════════════════════════════════
#  DRAW ENGINE — render frame không nhấp nháy
# ══════════════════════════════════════════════════════════════
def draw(lines, hard_clear=False):
    buf = [E + "H"]
    if hard_clear:
        buf.insert(0, E + "2J" + E + "3J")
    n = len(lines)
    for i, l in enumerate(lines):
        buf.append(l)
        buf.append(E + "K")
        if i < n - 1:
            buf.append("\n")
    buf.append(E + "J")
    sys.stdout.write("".join(buf))
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  LOADING SCREEN — VÔ HẠN CHO ĐẾN KHI XONG
# ══════════════════════════════════════════════════════════════
def build_loading_frame(frame, label, phase_text, state):
    """
    state: 'running' | 'ok' | 'fail'
    Animation chạy mãi cho đến khi state != 'running'.
    """
    lines = [""]
    for bl in banner_flame(frame):
        lines.append("  " + bl)
    lines.append("")
    lines.append("  " + flame_strip(W, frame, 0.02))
    lines.append("")

    # Radar + info
    radar_lines = radar(frame, size=13)

    # Phase title — shimmer chạy
    phase_col = gradw(f"  ⟪ {phase_text} ⟫",
                      0.02, 0.10, 0.95,
                      base=0.65, amp=0.35,
                      freq=0.5, phase=frame * 0.6)

    # Label
    label_col = gradw(f"  ◈ {label}",
                      0.55, 0.75, 0.85,
                      base=0.60, amp=0.30,
                      freq=0.5, phase=frame * 0.5)

    # Spinner — vô hạn
    spin = spin_symbols(frame)
    spin_col = gradw(f"  {spin}  loading",
                     0.02, 0.10, 0.9,
                     base=0.65, amp=0.35,
                     freq=0.7, phase=frame * 0.8)

    # Progress bar dạng "vô định" — trượt qua lại liên tục (không có %)
    bar_w = 30
    period = 40
    p = (frame % period) / period
    pos = (p * 2 if p < 0.5 else (1 - p) * 2) * (bar_w - 1)

    bar = ""
    for i in range(bar_w):
        d = abs(i - pos)
        if d < 1.5:
            bar += rgb(255, 200, 100) + "█"
        elif d < 3:
            bar += rgb(255, 100, 30) + "▓"
        elif d < 5:
            bar += rgb(160, 60, 20) + "▒"
        else:
            bar += rgb(60, 30, 20) + "░"
    bar += R

    status_icon = "◉"
    status_txt = "SYSTEM ACTIVE"
    if state == "ok":
        status_icon = "✓"
        status_txt = "SUCCESS"
    elif state == "fail":
        status_icon = "✗"
        status_txt = "FAILED"

    status_col = gradw(f"  {status_icon} {status_txt}",
                       0.02, 0.10, 0.9,
                       base=0.65, amp=0.35,
                       freq=0.7, phase=frame * 0.7)

    info = [
        "",
        phase_col,
        "",
        label_col,
        "",
        "  " + bar,
        "",
        spin_col,
        "",
        status_col,
        "",
    ]

    h = max(len(radar_lines), len(info))
    for i in range(h):
        left = radar_lines[i] if i < len(radar_lines) else " " * 13
        right = info[i] if i < len(info) else ""
        lines.append("    " + left + "      " + right)

    lines.append("")
    lines.append("  " + flame_strip(W, -frame, 0.05))
    lines.append("")
    lines.append("  " + grad("  ▸ Vui lòng đợi, hệ thống đang xử lý  ",
                               0.02, 0.08, 0.55, 0.85))
    return lines


def run_with_loading(fn, label, phase_text):
    """
    Chạy fn() trong thread nền, animation loading chạy vô hạn
    cho đến khi fn() xong. Trả về (success: bool, result, error).
    """
    result_holder = {"result": None, "error": None, "done": threading.Event()}

    def _worker():
        try:
            result_holder["result"] = fn()
        except Exception as e:
            result_holder["error"] = e
        finally:
            result_holder["done"].set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    frame = 0
    first = True
    while not result_holder["done"].is_set():
        draw(build_loading_frame(frame, label, phase_text, "running"),
             hard_clear=first)
        first = False
        frame += 1
        time.sleep(0.045)

    # Hiển thị kết quả cuối 8 frame
    if result_holder["error"]:
        state = "fail"
    else:
        state = "ok"

    for _ in range(10):
        draw(build_loading_frame(frame, label, phase_text, state))
        frame += 1
        time.sleep(0.05)

    return (result_holder["error"] is None,
            result_holder["result"],
            result_holder["error"])


# ══════════════════════════════════════════════════════════════
#  NUKE UI — STATUS BAR
# ══════════════════════════════════════════════════════════════
class NukeStats:
    def __init__(self):
        self.rounds = 0
        self.names_ok = 0
        self.polls_ok = 0
        self.themes_ok = 0
        self.start_time = time.time()
        self.combo = 0
        self.max_combo = 0

    def uptime(self):
        s = int(time.time() - self.start_time)
        h, r = divmod(s, 3600)
        m, sec = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}"

    def bump(self, target):
        if target == "name":
            self.names_ok += 1
        elif target == "poll":
            self.polls_ok += 1
        elif target == "theme":
            self.themes_ok += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)


def status_bar(stats, frame, thread_id):
    sep = "  " + rgb(80, 25, 15) + "│" + R + "  "
    upt = grad(f"⏱ {stats.uptime()}", 0.02, 0.10, 0.9, 0.95)
    rnd = gradw(f"🔁 Vòng {stats.rounds}", 0.05, 0.12, 0.9,
                base=0.65, amp=0.25, freq=0.5, phase=frame * 0.4)
    box = grad(f"📦 {thread_id[-6:] if len(thread_id) > 6 else thread_id}",
               0.55, 0.65, 0.8, 0.95)
    line1 = "  " + upt + sep + rnd + sep + box

    nm = grad(f"✦ Tên: {stats.names_ok}", 0.02, 0.10, 0.95, 0.95)
    pl = grad(f"◈ Poll: {stats.polls_ok}", 0.78, 0.90, 0.95, 0.95)
    th = grad(f"❋ Theme: {stats.themes_ok}", 0.30, 0.55, 0.95, 0.95)
    line2 = "  " + nm + sep + pl + sep + th

    if stats.combo > 0:
        combo_col = 0.02 + min(stats.combo / 50, 0.10)
        combo_txt = f"🔥 COMBO ×{stats.combo}"
        if stats.combo == stats.max_combo and stats.combo >= 5:
            combo_txt = f"🔥 COMBO MAX ×{stats.combo} 🔥"
        line3 = "  " + gradw(combo_txt, combo_col, combo_col + 0.08,
                             1.0, base=0.7, amp=0.3,
                             freq=0.8, phase=frame * 0.7)
    else:
        line3 = ""

    return [line1, line2, line3]


def weapon_panel(frame, current_weapon, thread_id,
                 group_name, poll_title, poll_opts, theme_name):
    weapons = [
        ("✏️", "NHÂY TÊN", 0.02, "TÊN", group_name),
        ("◈", "POLL", 0.78, "Q", poll_title),
        ("❋", "THEME", 0.30, "T", theme_name),
    ]
    keys = ["name", "poll", "theme"]

    lines = []
    lines.append("  " + rgb(100, 30, 15) + "─" * W + R)

    for i, (icon, label, h, short, val) in enumerate(weapons):
        is_active = (keys[i] == current_weapon)
        if is_active:
            lamp = gradw("◉", h, h + 0.05, 1.0, base=0.9, amp=0.1,
                         freq=0.9, phase=frame * 0.9)
            prefix = "  " + lamp + "  "
        else:
            prefix = "  " + rgb(60, 30, 20) + "○" + R + "  "

        label_col = grad(f"[{i+1}] {icon} {label}",
                         h, h + 0.08, 0.9, 1.0 if is_active else 0.6)

        val_str = (val or "")[:max(15, W - 30)]
        if is_active:
            val_col = gradw(val_str, h, h + 0.08, 0.85,
                            base=0.75, amp=0.25,
                            freq=0.6, phase=frame * 0.6)
        else:
            val_col = rgb(120, 70, 50) + val_str + R

        lines.append(prefix + label_col)
        lines.append("        " + rgb(60, 30, 20) + "↳ " + R + val_col)

    lines.append("  " + rgb(100, 30, 15) + "─" * W + R)
    return lines


def render_frame(frame, stats, thread_id, cookie_hash,
                 current_weapon, group_name, poll_title, poll_opts, theme_name,
                 event_log):
    lines = [""]
    for bl in banner_flame(frame):
        lines.append("  " + bl)
    lines.append("")
    lines.append("  " + flame_strip(W, frame, 0.02))
    lines.append("")

    header = gradw(
        f"  ☢  N U K E   B O X  →  {thread_id}",
        0.02, 0.10, 0.95, base=0.75, amp=0.25,
        freq=0.5, phase=frame * 0.5)
    lines.append(header)
    lines.append("  " + rgb(120, 40, 20) + f"  Cookie: {cookie_hash[:10]}…" + R)
    lines.append("")

    lines.extend(weapon_panel(frame, current_weapon, thread_id,
                              group_name, poll_title, poll_opts, theme_name))
    lines.append("")

    if event_log:
        lines.append("  " + rgb(100, 30, 15) + "╭─ NHẬT KÝ ─────────────────╮" + R)
        for ev in event_log[-3:]:
            lines.append("  " + rgb(100, 30, 15) + "│ " + R + ev[:W - 6])
        lines.append("  " + rgb(100, 30, 15) + "╰───────────────────────────╯" + R)
    lines.append("")

    lines.extend(status_bar(stats, frame, thread_id))
    lines.append("")

    lines.append("  " + flame_strip(W, -frame * 0.7, 0.05))
    lines.append("")
    lines.append("  " + grad("  ▸ Ctrl+C để dừng nuke  ",
                               0.02, 0.08, 0.55, 0.85))
    return lines


# ══════════════════════════════════════════════════════════════
#  INPUT MENU
# ══════════════════════════════════════════════════════════════
def intro_screen(frame):
    lines = [""]
    for bl in banner_flame(frame):
        lines.append("  " + bl)
    lines.append("")
    lines.append("  " + flame_strip(W, frame, 0.02))
    lines.append("")
    sub = "  S I N G U L A R I T Y   E N G I N E   v 1 . 0"
    pad = max((W - len(sub)) // 2, 0)
    lines.append(gradw(sub, 0.02, 0.12, 0.9, base=0.7, amp=0.3,
                       freq=0.4, phase=frame * 0.5))
    lines.append("")
    lines.append("  " + flame_strip(W, -frame, 0.05))
    return lines


def input_menu():
    sys.stdout.write(HC)
    # Intro animation vô hạn 40 frame đầu
    for f in range(40):
        draw(intro_screen(f), hard_clear=(f == 0))
        time.sleep(0.05)

    draw(intro_screen(40))
    sys.stdout.write(SC)

    print()
    print("  " + grad("  ▸ CẤU HÌNH NUKE  ", 0.02, 0.10, 0.95, 1.0))
    print()

    print("  " + grad("  [1] Nhập cookie", 0.02, 0.08, 0.7, 0.95))
    print("      " + rgb(120, 70, 50) + "Mỗi cookie 1 dòng, gõ 'end' để kết thúc" + R)
    cookies = []
    while True:
        try:
            line = input("  " + rgb(200, 60, 30) + "> " + R).strip()
        except EOFError:
            break
        if line.lower() == 'end':
            break
        if line:
            cookies.append(line)

    if not cookies:
        print("  " + grad("  ✗ Chưa có cookie", 0.02, 0.08, 0.9, 1.0))
        sys.exit(1)

    print("  " + grad(f"  ✓ {len(cookies)} cookie", 0.02, 0.08, 0.75, 0.95))
    print()

    print("  " + grad("  [2] Nhập ID box", 0.02, 0.08, 0.7, 0.95))
    print("      " + rgb(120, 70, 50) + "Mỗi ID 1 dòng, gõ 'end' để kết thúc" + R)
    thread_ids = []
    while True:
        try:
            line = input("  " + rgb(200, 60, 30) + "> " + R).strip()
        except EOFError:
            break
        if line.lower() == 'end':
            break
        if line:
            thread_ids.append(line)

    if not thread_ids:
        print("  " + grad("  ✗ Chưa có ID box", 0.02, 0.08, 0.9, 1.0))
        sys.exit(1)

    print("  " + grad(f"  ✓ {len(thread_ids)} box", 0.02, 0.08, 0.75, 0.95))
    print()

    print("  " + grad("  [3] File tên nhóm", 0.02, 0.08, 0.7, 0.95))
    name_file = input("  " + rgb(200, 60, 30) + "> " + R).strip()

    print("  " + grad("  [4] File tiêu đề poll", 0.02, 0.08, 0.7, 0.95))
    poll_title_file = input("  " + rgb(200, 60, 30) + "> " + R).strip()

    print("  " + grad("  [5] File lựa chọn poll", 0.02, 0.08, 0.7, 0.95))
    poll_opts_file = input("  " + rgb(200, 60, 30) + "> " + R).strip()

    print()
    print("  " + grad("  [6] Delay mỗi vũ khí (giây)", 0.02, 0.08, 0.7, 0.95))
    try:
        delay_name = float(input("      " + rgb(150, 80, 50) + "Nhây tên: " + R).strip() or "0.5")
        delay_poll = float(input("      " + rgb(150, 80, 50) + "Poll    : " + R).strip() or "0.5")
        delay_theme = float(input("      " + rgb(150, 80, 50) + "Theme   : " + R).strip() or "0.5")
    except ValueError:
        print("  " + grad("  ✗ Delay phải là số", 0.02, 0.08, 0.9, 1.0))
        sys.exit(1)

    try:
        with open(name_file, 'r', encoding='utf-8') as f:
            group_names = [l.strip() for l in f if l.strip()]
        with open(poll_title_file, 'r', encoding='utf-8') as f:
            poll_titles = [l.strip() for l in f if l.strip()]
        with open(poll_opts_file, 'r', encoding='utf-8') as f:
            poll_options = [l.strip() for l in f if l.strip()]
    except Exception as e:
        print("  " + grad(f"  ✗ Lỗi file: {e}", 0.02, 0.08, 0.9, 1.0))
        sys.exit(1)

    if not group_names or not poll_titles or len(poll_options) < 4:
        print("  " + grad("  ✗ File rỗng hoặc poll < 4 lựa chọn", 0.02, 0.08, 0.9, 1.0))
        sys.exit(1)

    return cookies, thread_ids, group_names, poll_titles, poll_options, \
           delay_name, delay_poll, delay_theme


# ══════════════════════════════════════════════════════════════
#  NUKE LOOP
# ══════════════════════════════════════════════════════════════
def nuke_box(cookies, thread_ids, group_names, poll_titles, poll_options,
             delay_name, delay_poll, delay_theme):

    for cookie in cookies:
        cookie_hash = hashlib.md5(cookie.encode()).hexdigest()

        # ─── Loading vô hạn: khởi tạo account ───
        ok, fb, err = run_with_loading(
            lambda: ngquanghuyakadzi(cookie),
            f"ACCOUNT {cookie_hash[:8]}",
            "NẠP COOKIE / LẤY FB_DTSG"
        )
        if not ok:
            cls()
            print()
            print("  " + grad("  ✗ COOKIE LỖI  ", 0.02, 0.10, 0.95, 1.0))
            print("  " + rgb(200, 80, 60) + f"  {err}" + R)
            print()
            time.sleep(2.5)
            continue

        dataFB = {
            "FacebookID": fb.user_id,
            "fb_dtsg": fb.fb_dtsg,
            "clientRevision": fb.rev,
            "jazoest": fb.jazoest,
            "cookieFacebook": cookie
        }

        # ─── Loading vô hạn: MQTT connect ───
        def _setup():
            fbt = fbTools(dataFB)
            sender = MessageSender(fbt, dataFB)
            sender.get_last_seq_id()
            if not sender.connect_mqtt():
                raise Exception("MQTT connection failed")
            return sender

        ok, sender, err = run_with_loading(
            _setup,
            "MQTT PAYLOAD",
            "KẾT NỐI EDGE-CHAT"
        )
        if not ok:
            cls()
            print()
            print("  " + grad("  ✗ MQTT FAILED  ", 0.02, 0.10, 0.95, 1.0))
            print("  " + rgb(200, 80, 60) + f"  {err}" + R)
            print()
            time.sleep(2)
            continue

        # ─── Nuke loop ───
        for thread_id in thread_ids:
            stats = NukeStats()
            frame = 0
            group_name = poll_title = theme_name = ""
            poll_opts = []
            current_weapon = None
            event_log = []

            def log(msg):
                event_log.append(msg)
                if len(event_log) > 8:
                    event_log.pop(0)

            try:
                while True:
                    stats.rounds += 1

                    # 1/3 NHÂY TÊN
                    group_name = random.choice(group_names)
                    current_weapon = "name"
                    ok_name = tenbox(group_name, thread_id, dataFB)
                    if ok_name:
                        stats.bump("name")
                        log(gradw(f"✓ Tên → {group_name[:30]}",
                                  0.02, 0.10, 0.9, base=0.75, amp=0.25,
                                  freq=0.5, phase=frame * 0.5))
                    else:
                        stats.combo = 0
                        log(rgb(200, 80, 60) + "✗ Tên fail" + R)

                    t_end = time.time() + delay_name
                    while time.time() < t_end:
                        draw(render_frame(frame, stats, thread_id, cookie_hash,
                                          current_weapon, group_name,
                                          poll_title, poll_opts, theme_name,
                                          event_log))
                        frame += 1
                        time.sleep(0.045)

                    # 2/3 POLL
                    poll_title = random.choice(poll_titles)
                    if len(poll_options) >= 4:
                        poll_opts = random.sample(poll_options, 4)
                    else:
                        poll_opts = poll_options
                    current_weapon = "poll"
                    ok_poll = sender.create_poll(poll_title, poll_opts, thread_id)
                    if ok_poll:
                        stats.bump("poll")
                        log(gradw(f"✓ Poll → {poll_title[:30]}",
                                  0.78, 0.90, 0.9, base=0.75, amp=0.25,
                                  freq=0.5, phase=frame * 0.5))
                    else:
                        stats.combo = 0
                        log(rgb(200, 80, 60) + "✗ Poll fail" + R)

                    t_end = time.time() + delay_poll
                    while time.time() < t_end:
                        draw(render_frame(frame, stats, thread_id, cookie_hash,
                                          current_weapon, group_name,
                                          poll_title, poll_opts, theme_name,
                                          event_log))
                        frame += 1
                        time.sleep(0.045)

                    # 3/3 THEME
                    theme = random.choice(sender.THEMES)
                    theme_name = theme["name"]
                    current_weapon = "theme"
                    ok_theme = sender.set_theme(theme["id"], thread_id)
                    if ok_theme:
                        stats.bump("theme")
                        log(gradw(f"✓ Theme → {theme_name[:30]}",
                                  0.30, 0.55, 0.9, base=0.75, amp=0.25,
                                  freq=0.5, phase=frame * 0.5))
                    else:
                        stats.combo = 0
                        log(rgb(200, 80, 60) + "✗ Theme fail" + R)

                    t_end = time.time() + delay_theme
                    while time.time() < t_end:
                        draw(render_frame(frame, stats, thread_id, cookie_hash,
                                          current_weapon, group_name,
                                          poll_title, poll_opts, theme_name,
                                          event_log))
                        frame += 1
                        time.sleep(0.045)

            except KeyboardInterrupt:
                raise
            finally:
                sender.stop()

    return True


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    try:
        data = input_menu()
        cookies, thread_ids, group_names, poll_titles, poll_options, \
            delay_name, delay_poll, delay_theme = data

        print()
        print("  " + grad(f"  ✓ Nạp: {len(group_names)} tên | "
                           f"{len(poll_titles)} poll | "
                           f"{len(poll_options)} opts",
                           0.02, 0.10, 0.9, 1.0))
        time.sleep(1.5)

        sys.stdout.write(HC)
        nuke_box(cookies, thread_ids, group_names, poll_titles, poll_options,
                 delay_name, delay_poll, delay_theme)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(R + SC + E + "2J" + E + "3J" + E + "H")
        sys.stdout.flush()
        print()
        print("  " + grad("  ✦ N U K E   T E R M I N A T E D ✦",
                           0.02, 0.15, 0.9, 1.0))
        print("  " + rgb(120, 60, 40) + "  Hẹn gặp lại." + R)
        print()


if __name__ == "__main__":
    main()