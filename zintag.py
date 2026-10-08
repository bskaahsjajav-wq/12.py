#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
#   ZIN THIÊN ĐẠO - FACEBOOK WAR MESS · VĨNH HẰNG NHÂY TAG
#   Gradient 7 màu + Wave animation
# ══════════════════════════════════════════════════════════════

import multiprocessing
import requests
import os
import re
import json
import time
import math
import random
import threading
import ssl
import warnings
import sys
import subprocess

try:
    import paho.mqtt.client as mqtt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt"])
    import paho.mqtt.client as mqtt

from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

warnings.filterwarnings("ignore", category=DeprecationWarning)
console = Console()

RESET = "\033[0m"
E = "\033["


# ══════════════════════════════════════════════════════════════
#  BẢNG MÀU 7 SẮC — ĐỎ CAM VÀNG LỤC LAM CHÀM TÍM
# ══════════════════════════════════════════════════════════════
RB = [
    (255,   0,   0),   # đỏ
    (255, 127,   0),   # cam
    (255, 255,   0),   # vàng
    (  0, 255,   0),   # lục
    (  0, 128, 255),   # lam
    ( 75,   0, 130),   # chàm
    (148,   0, 211),   # tím
]


def rgb(r, g, b):
    return f"{E}38;2;{int(r)};{int(g)};{int(b)}m"


def _lerp(c1, c2, t):
    return (c1[0] + (c2[0] - c1[0]) * t,
            c1[1] + (c2[1] - c1[1]) * t,
            c1[2] + (c2[2] - c1[2]) * t)


def rainbow(text, offset=0.0):
    """Gradient 7 màu thuần, có thể dịch offset để chạy."""
    n = max(len(text) - 1, 1)
    seg_count = len(RB)
    out = []
    for i, ch in enumerate(text):
        t = ((i / n) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        c = _lerp(RB[s], RB[(s + 1) % seg_count], ratio)
        out.append(rgb(*c) + ch)
    return "".join(out) + RESET


def wave(text, phase=0.0, base=0.55, amp=0.45, freq=0.35,
         sat=1.0, offset=0.0):
    """Gradient 7 màu + sóng sáng chạy qua."""
    n = max(len(text) - 1, 1)
    seg_count = len(RB)
    out = []
    for i, ch in enumerate(text):
        t = ((i / n) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB[s], RB[(s + 1) % seg_count], ratio)
        v = base + amp * (0.5 + 0.5 * math.sin(i * freq - phase))
        r = max(0, min(255, int(r * v + (1 - v) * 40)))
        g = max(0, min(255, int(g * v + (1 - v) * 40)))
        b = max(0, min(255, int(b * v + (1 - v) * 40)))
        out.append(rgb(r, g, b) + ch)
    return "".join(out) + RESET


def wave_border(width=60, phase=0.0, char="═", offset=0.0):
    """Đường border wave 7 màu."""
    seg_count = len(RB)
    out = []
    for i in range(width):
        t = ((i / max(width - 1, 1)) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB[s], RB[(s + 1) % seg_count], ratio)
        v = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(i * 0.25 - phase))
        r = int(r * v)
        g = int(g * v)
        b = int(b * v)
        out.append(rgb(r, g, b) + char)
    return "".join(out) + RESET


def wave_dots(width=60, phase=0.0, offset=0.0):
    """Dải sao nhỏ có wave."""
    chars = "·⋅∙•●•∙⋅"
    seg_count = len(RB)
    out = []
    for i in range(width):
        t = ((i / max(width - 1, 1)) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB[s], RB[(s + 1) % seg_count], ratio)
        v = 0.5 + 0.5 * math.sin(i * 0.30 - phase)
        idx = int(v * (len(chars) - 1))
        rv = int(r * (0.35 + 0.65 * v))
        gv = int(g * (0.35 + 0.65 * v))
        bv = int(b * (0.35 + 0.65 * v))
        out.append(rgb(rv, gv, bv) + chars[idx])
    return "".join(out) + RESET


# ══════════════════════════════════════════════════════════════
#  BANNER — ZIN SLANT + WAVE ANIMATION
# ══════════════════════════════════════════════════════════════
ZIN_BANNER = r"""
   _____ _____ _   _ 
  |__  /_ _| \ | |
    / / | ||  \| |
   / /_ | || |\  |
  /____|___|_| \_|
"""


def _clear():
    sys.stdout.write(E + "2J" + E + "3J" + E + "H")
    sys.stdout.flush()


def animate_banner(frames=36, delay=0.04):
    """Banner ZIN với gradient 7 màu chạy + wave."""
    lines = [l for l in ZIN_BANNER.strip("\n").split("\n")]
    tagline = "  ZIN THIÊN ĐẠO  ·  VĨNH HẰNG CHÍ TÔN"
    sub = "  ⚔  FACEBOOK WAR MESS · TAG THẬT  ⚔"

    sys.stdout.write(E + "?25l")
    # in khung đầu
    print()
    for l in lines:
        print(rainbow(l, offset=0.0))
    print(wave(tagline, 0.0, offset=0.0))
    print(wave(sub, 0.0, offset=0.0))
    print()
    sys.stdout.flush()

    total = len(lines) + 2
    for f in range(1, frames):
        t = f / max(frames - 1, 1)
        offset = -t * 0.85
        phase = f * 0.55

        new_lines = []
        for i, l in enumerate(lines):
            new_lines.append(rainbow(l, offset=offset + i * 0.02))
        new_lines.append(wave(tagline, phase, offset=offset))
        new_lines.append(wave(sub, phase * 1.3, offset=offset))

        sys.stdout.write(E + f"{total}A")
        for l in new_lines:
            sys.stdout.write(l + E + "K\n")
        sys.stdout.flush()
        time.sleep(delay)

    # khung cuối tĩnh
    final = []
    for i, l in enumerate(lines):
        final.append(rainbow(l, offset=i * 0.02))
    final.append(wave(tagline, 0.0, offset=0.0))
    final.append(wave(sub, 1.5, offset=0.0))

    sys.stdout.write(E + f"{total}A")
    for l in final:
        sys.stdout.write(l + E + "K\n")
    sys.stdout.flush()
    sys.stdout.write(E + "?25h")
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  LOG HELPERS
# ══════════════════════════════════════════════════════════════
def print_color(text, color_type="info"):
    """Giữ API cũ — map sang wave."""
    phase = time.time() * 2.0
    hue_offset = {
        "success": 0.30, "error": 0.85, "warning": 0.10,
        "info": 0.55, "cyan": 0.50, "magenta": 0.75,
    }.get(color_type, 0.55)
    print(wave(str(text), phase, offset=hue_offset))


def print_gradient(text, colors=None):
    phase = time.time() * 2.5
    print(wave(str(text), phase, offset=0.0))


def print_banner():
    for l in ZIN_BANNER.strip("\n").split("\n"):
        print(rainbow(l, 0.0))
    print(wave("  ZIN THIÊN ĐẠO  ·  VĨNH HẰNG CHÍ TÔN", 0, offset=0.0))
    print(wave("  ⚔  FACEBOOK WAR MESS · TAG THẬT  ⚔", 0, offset=0.3))


def gradient_text(text, colors=None):
    """Compat với code cũ — trả về chuỗi wave."""
    return wave(str(text), time.time() * 2.0, offset=0.0)


def print_line(char="=", length=60, color="cyan"):
    print("  " + wave_border(length, time.time() * 1.5, char or "═",
                              offset=0.0))


def print_header(text):
    phase = time.time() * 1.8
    print()
    print("  " + wave_border(60, phase, "═", offset=0.0))
    pad = max((60 - len(text)) // 2, 0)
    print(" " * pad + wave(text, phase, offset=0.3))
    print("  " + wave_border(60, phase + 1.5, "═", offset=0.5))
    print()


def clear():
    os.system("cls" if os.name == "nt" else "clear")


# ══════════════════════════════════════════════════════════════
#  LOGIC — GIỮ NGUYÊN
# ══════════════════════════════════════════════════════════════
def check_live(cookie):
    try:
        if "c_user=" not in cookie:
            return {"status": "failed", "msg": "Cookie không chứa user_id"}
        user_id = cookie.split("c_user=")[1].split(";")[0]
        headers = {
            "authority": "m.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "vi-VN,vi;q=0.9",
            "cache-control": "max-age=0",
            "cookie": cookie,
            "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"0.1.0"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        }
        profile_response = requests.get(
            f"https://m.facebook.com/profile.php?id={user_id}",
            headers=headers, timeout=30)
        name = profile_response.text.split("<title>")[1].split("<")[0].strip()
        return {"status": "success", "name": name,
                "user_id": user_id, "msg": "successful"}
    except Exception as e:
        return {"status": "failed", "msg": f"Lỗi xảy ra: {str(e)}"}


def load_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            raise Exception(f"File {file_path} trống!")
        return lines
    except Exception as e:
        raise Exception(f"Lỗi đọc file {file_path}: {str(e)}")


def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(",")]
        return [n for n in numbers if 1 <= n <= max_index]
    except Exception:
        print_color("❌ Định dạng không hợp lệ!", "error")
        return []


def generate_offline_threading_id():
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))


def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))


def generate_session_id():
    return random.randint(1, 2 ** 53)


def generate_client_id():
    import string

    def gen(length):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    return gen(8) + "-" + gen(4) + "-" + gen(4) + "-" + gen(4) + "-" + gen(12)


# ══════════════════════════════════════════════════════════════
#  MQTT MANAGER
# ══════════════════════════════════════════════════════════════
class MQTTManager:
    def __init__(self, cookie, user_id):
        self.cookie = cookie
        self.user_id = user_id
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.connected = False

    def connect(self):
        try:
            chat_on = json_minimal(True)
            session_id = generate_session_id()
            user = {
                "u": self.user_id,
                "s": session_id,
                "chat_on": chat_on,
                "fg": False,
                "d": generate_client_id(),
                "ct": "websocket",
                "aid": 219994525426954,
                "mqtt_sid": "",
                "cp": 3,
                "ecp": 10,
                "st": ["/t_ms", "/messenger_sync_get_diffs",
                       "/messenger_sync_create_queue"],
                "pm": [],
                "dc": "",
                "no_auto_fg": True,
                "gas": None,
                "pack": [],
            }

            host = f"wss://edge-chat.facebook.com/chat?region=eag&sid={session_id}"
            options = {
                "client_id": "mqttwsclient",
                "username": json_minimal(user),
                "clean": True,
                "ws_options": {
                    "headers": {
                        "Cookie": self.cookie,
                        "Origin": "https://www.facebook.com",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
                        "Referer": "https://www.facebook.com/",
                        "Host": "edge-chat.facebook.com",
                    },
                },
                "keepalive": 10,
            }

            try:
                self.mqtt = mqtt.Client(
                    client_id="mqttwsclient",
                    clean_session=True,
                    protocol=mqtt.MQTTv31,
                    transport="websockets",
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                )
            except Exception:
                self.mqtt = mqtt.Client(
                    client_id="mqttwsclient",
                    clean_session=True,
                    protocol=mqtt.MQTTv31,
                    transport="websockets",
                )

            self.mqtt.tls_set(certfile=None, keyfile=None,
                              cert_reqs=ssl.CERT_NONE,
                              tls_version=ssl.PROTOCOL_TLSv1_2)
            self.mqtt.on_connect = self._on_connect
            self.mqtt.on_disconnect = self._on_disconnect
            self.mqtt.username_pw_set(username=options["username"])
            parsed_host = urlparse(host)
            self.mqtt.ws_set_options(
                path=f"{parsed_host.path}?{parsed_host.query}",
                headers=options["ws_options"]["headers"],
            )

            print(wave("  ⟳ Đang khai mở linh mạch...", time.time() * 2, offset=0.55))
            self.mqtt.connect(
                host=options["ws_options"]["headers"]["Host"],
                port=443,
                keepalive=options["keepalive"],
            )
            self.mqtt.loop_start()
            time.sleep(3)
            return self.connected

        except Exception as e:
            print(wave(f"  ✗ Lỗi kết nối MQTT: {e}", 0, offset=0.85))
            return False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
        else:
            print(wave(f"  ✗ Kết nối MQTT thất bại với mã: {rc}", 0, offset=0.85))
            self.connected = False

    def _on_disconnect(self, client, userdata, rc, properties=None):
        print(wave(f"  ⟳ Ngắt kết nối MQTT với mã: {rc}", time.time(), offset=0.10))
        self.connected = False

    def send_typing(self, thread_id, is_typing=True):
        if not self.connected or not self.mqtt:
            return False
        self.ws_req_number += 1
        try:
            task_payload = {
                "thread_key": thread_id,
                "is_group_thread": 1,
                "is_typing": 1 if is_typing else 0,
                "attribution": 0,
            }
            content = {
                "app_id": "2220391788200892",
                "payload": json.dumps({
                    "label": "3",
                    "payload": json.dumps(task_payload),
                    "version": "25393437286970779",
                }),
                "request_id": self.ws_req_number,
                "type": 4,
            }
            self.mqtt.publish("/ls_req",
                              json.dumps(content, separators=(",", ":")),
                              qos=1, retain=False)
            return True
        except Exception as e:
            print(wave(f"  ✗ Lỗi gửi typing: {e}", 0, offset=0.85))
            return False

    def send_message_with_mentions(self, thread_id, text, mentions_data):
        if not self.connected or not self.mqtt:
            return False
        self.ws_req_number += 1
        content = {
            "app_id": "2220391788200892",
            "payload": {
                "data_trace_id": None,
                "epoch_id": int(generate_offline_threading_id()),
                "tasks": [],
                "version_id": "7545284305482586",
            },
            "request_id": self.ws_req_number,
            "type": 3,
        }
        if text:
            self.ws_task_number += 1
            task_payload = {
                "initiating_source": 0,
                "multitab_env": 0,
                "otid": generate_offline_threading_id(),
                "send_type": 1,
                "skip_url_preview_gen": 0,
                "source": 0,
                "sync_group": 1,
                "text": text,
                "text_has_links": 0,
                "thread_id": int(thread_id),
            }
            if mentions_data and len(mentions_data) > 0:
                valid_mentions = []
                current_offset = 0
                for mention in mentions_data:
                    if "id" in mention and "tag" in mention:
                        tag_text = f"@{mention['tag']}"
                        find = text.find(tag_text, current_offset)
                        if find != -1:
                            valid_mentions.append({
                                "i": mention["id"],
                                "o": find,
                                "l": len(tag_text),
                            })
                            current_offset = find + len(tag_text)
                if valid_mentions:
                    task_payload["mention_data"] = {
                        "mention_ids": ",".join(str(x["i"]) for x in valid_mentions),
                        "mention_lengths": ",".join(str(x["l"]) for x in valid_mentions),
                        "mention_offsets": ",".join(str(x["o"]) for x in valid_mentions),
                        "mention_types": ",".join("p" for _ in valid_mentions),
                    }
            task = {
                "failure_count": None,
                "label": "46",
                "payload": json.dumps(task_payload, separators=(",", ":")),
                "queue_name": str(thread_id),
                "task_id": self.ws_task_number,
            }
            content["payload"]["tasks"].append(task)
            self.ws_task_number += 1
            task_mark_payload = {
                "last_read_watermark_ts": int(time.time() * 1000),
                "sync_group": 1,
                "thread_id": int(thread_id),
            }
            task_mark = {
                "failure_count": None,
                "label": "21",
                "payload": json.dumps(task_mark_payload, separators=(",", ":")),
                "queue_name": str(thread_id),
                "task_id": self.ws_task_number,
            }
            content["payload"]["tasks"].append(task_mark)
        content["payload"] = json.dumps(content["payload"], separators=(",", ":"))
        try:
            self.mqtt.publish("/ls_req",
                              json.dumps(content, separators=(",", ":")),
                              qos=1, retain=False)
            return True
        except Exception as e:
            print(wave(f"  ✗ Lỗi gửi tin nhắn: {e}", 0, offset=0.85))
            return False

    def disconnect(self):
        if self.mqtt:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()


# ══════════════════════════════════════════════════════════════
#  MESSENGER
# ══════════════════════════════════════════════════════════════
class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.mqtt_manager = None
        self.init_params()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        ]
        self.connect_mqtt()

    def connect_mqtt(self):
        try:
            self.mqtt_manager = MQTTManager(self.cookie, self.user_id)
            if self.mqtt_manager.connect():
                print(wave("  ✓ Zin Thiên Đạo - Linh Mạch Đã Thông",
                           time.time() * 2, offset=0.30))
                return True
            else:
                print(wave("  ⚠ Không thể kết nối MQTT, dùng phương thức thường",
                           time.time() * 2, offset=0.10))
                return False
        except Exception as e:
            print(wave(f"  ✗ Lỗi kết nối MQTT: {e}", 0, offset=0.85))
            return False

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except Exception:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        urls = [
            "https://www.facebook.com",
            "https://mbasic.facebook.com",
            "https://m.facebook.com",
        ]
        for url in urls:
            try:
                print(wave(f"  ⟳ Thử lấy fb_dtsg từ {url}",
                           time.time() * 2, offset=0.55))
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                fb_dtsg_patterns = [
                    r'"token":"(.*?)"',
                    r'name="fb_dtsg" value="(.*?)"',
                    r'"fb_dtsg":"(.*?)"',
                    r'fb_dtsg=([^&"]+)',
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
                    print(wave(f"  ✓ fb_dtsg OK · jazoest {self.jazoest} · rev {self.rev}",
                               time.time() * 2, offset=0.30))
                    return
            except Exception:
                time.sleep(2)
        raise Exception("Không thể lấy được fb_dtsg")

    def get_thread_list(self, limit=100):
        headers = {
            "Cookie": self.cookie,
            "User-Agent": random.choice(self.user_agents),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-FB-Friendly-Name": "MessengerThreadListQuery",
            "X-FB-LSD": "null",
        }
        form_data = {
            "av": self.user_id,
            "__user": self.user_id,
            "__a": "1",
            "__req": "1b",
            "__hs": "19234.HYP:comet_pkg.2.1..2.1",
            "dpr": "1",
            "__ccg": "EXCELLENT",
            "__rev": self.rev if self.rev else "1015919737",
            "__comet_req": "15",
            "fb_dtsg": self.fb_dtsg,
            "jazoest": self.jazoest,
            "lsd": "null",
            "__spin_r": "",
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3336396659757871",
                    "query_params": {
                        "limit": limit,
                        "before": None,
                        "tags": ["INBOX"],
                        "includeDeliveryReceipts": False,
                        "includeSeqID": True,
                    },
                }
            }),
        }
        try:
            response = requests.post(
                "https://www.facebook.com/api/graphqlbatch/",
                data=form_data, headers=headers, timeout=15)
            if response.status_code != 200:
                return {"error": f"HTTP Error: {response.status_code}"}
            response_text = response.text.split('{"successful_results"')[0]
            data = json.loads(response_text)
            if "o0" not in data:
                return {"error": "Không tìm thấy dữ liệu thread list"}
            if "errors" in data["o0"]:
                return {"error": f"FB API Error: {data['o0']['errors'][0]['summary']}"}
            threads = data["o0"]["data"]["viewer"]["message_threads"]["nodes"]
            thread_list = []
            for thread in threads:
                if not thread.get("thread_key") or not thread["thread_key"].get("thread_fbid"):
                    continue
                thread_list.append({
                    "thread_id": thread["thread_key"]["thread_fbid"],
                    "thread_name": thread.get("name", "Không có tên"),
                })
            return {"success": True, "thread_count": len(thread_list),
                    "threads": thread_list}
        except json.JSONDecodeError as e:
            return {"error": f"Lỗi parse JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi không xác định: {str(e)}"}

    def get_group_members(self, thread_id):
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "python-http/0.27.0",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Host": "www.facebook.com",
            "Referer": "https://www.facebook.com/",
        }
        payload = {
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3449967031715030",
                    "query_params": {
                        "id": thread_id,
                        "message_limit": 0,
                        "load_messages": False,
                        "load_read_receipts": False,
                        "before": None,
                    },
                }
            }),
            "batch_name": "MessengerGraphQLThreadFetcher",
            "fb_dtsg": self.fb_dtsg,
            "jazoest": self.jazoest,
        }
        try:
            response = requests.post(
                "https://www.facebook.com/api/graphqlbatch/",
                headers=headers, data=payload)
            content = response.text
            if content.startswith("for(;;);"):
                content = content[9:]
            json_objects = []
            current_json = ""
            in_quotes = False
            escape_next = False
            brackets = 0
            for char in content:
                if escape_next:
                    current_json += char
                    escape_next = False
                    continue
                if char == "\\" and not escape_next:
                    current_json += char
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_quotes = not in_quotes
                if not in_quotes:
                    if char == "{":
                        brackets += 1
                    elif char == "}":
                        brackets -= 1
                        if brackets == 0:
                            current_json += char
                            json_objects.append(current_json)
                            current_json = ""
                            continue
                if brackets > 0:
                    current_json += char
            if json_objects:
                data = json.loads(json_objects[0])
                thread_data = data.get("o0", {}).get("data", {}).get("message_thread", {})
                all_participants = thread_data.get("all_participants", {}).get("edges", [])
                members = []
                for participant in all_participants:
                    user = participant.get("node", {}).get("messaging_actor", {})
                    members.append({"name": user.get("name"), "id": user.get("id")})
                return {"success": True, "members": members}
            else:
                return {"error": "Không tìm thấy dữ liệu thành viên"}
        except Exception as e:
            return {"error": f"Lỗi lấy danh sách thành viên: {str(e)}"}

    def send_typing_indicator(self, thread_id, is_typing=True):
        if self.mqtt_manager and self.mqtt_manager.connected:
            return self.mqtt_manager.send_typing(thread_id, is_typing)
        return False

    def send_message_with_real_mentions(self, thread_id, content, tag_ids, tag_names):
        if self.mqtt_manager and self.mqtt_manager.connected:
            mentions_data = []
            full_message = content
            for tag_id, tag_name in zip(tag_ids, tag_names):
                mentions_data.append({"id": tag_id, "tag": tag_name})
                full_message += f" @{tag_name}"
            self.send_typing_indicator(thread_id, True)
            time.sleep(1)
            success = self.mqtt_manager.send_message_with_mentions(
                thread_id, full_message, mentions_data)
            self.send_typing_indicator(thread_id, False)
            return "success" if success else "failed"
        else:
            return self.send_message_old_method(thread_id, content, tag_ids, tag_names)

    def send_message_old_method(self, thread_id, content, tag_ids, tag_names):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Cookie": self.cookie,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": f"https://www.facebook.com/messages/t/{thread_id}",
        }
        tag_parts = []
        mentions = []
        offset = len(content) + 1
        for i in range(len(tag_ids)):
            name = tag_names[i]
            tag_text = f"@{name}"
            tag_parts.append(tag_text)
            mentions.append({
                f"profile_xmd[{i}][id]": tag_ids[i],
                f"profile_xmd[{i}][offset]": offset,
                f"profile_xmd[{i}][length]": len(tag_text),
                f"profile_xmd[{i}][type]": "p",
            })
            offset += len(tag_text) + 1
        full_message = f"{content} {' '.join(tag_parts)}"
        ts = str(int(time.time() * 1000))
        payload = {
            "thread_fbid": thread_id,
            "action_type": "ma-type:user-generated-message",
            "body": full_message,
            "client": "mercury",
            "author": f"fbid:{self.user_id}",
            "timestamp": ts,
            "offline_threading_id": ts,
            "message_id": ts,
            "source": "source:chat:web",
            "ephemeral_ttl_mode": "0",
            "__user": self.user_id,
            "__a": "1",
            "__req": "1b",
            "__rev": self.rev if self.rev else "1015919737",
            "fb_dtsg": self.fb_dtsg,
            "source_tags[0]": "source:chat",
        }
        for mention in mentions:
            payload.update(mention)
        try:
            response = requests.post(
                "https://www.facebook.com/messaging/send/",
                headers=headers, data=payload, timeout=10)
            return "success" if response.status_code == 200 else "failed"
        except Exception:
            return "failed"

    def send_message(self, recipient_id, content, list_tag, list_name_tag):
        if list_tag and list_name_tag:
            return self.send_message_with_real_mentions(
                recipient_id, content, list_tag, list_name_tag)
        else:
            return self.send_message_old_method(recipient_id, content, [], [])


# ══════════════════════════════════════════════════════════════
#  WORKER — chạy trên process riêng, có counter realtime
# ══════════════════════════════════════════════════════════════
def start_spam(cookie, account_name, user_id, thread_ids, thread_names,
               delay, message_lines, replace_text, tag_ids, tag_names):
    try:
        messenger = Messenger(cookie)
        message_index = 0

        print()
        print("  " + wave_border(60, time.time(), "═", offset=0.0))
        print("  " + wave(f"▶ TU SĨ: {account_name}", time.time(),
                          offset=0.55))
        print("  " + wave_border(60, time.time() + 1, "═", offset=0.5))
        print()

        ok_count = 0
        fail_count = 0
        phase = 0.0

        while True:
            for thread_id, thread_name in zip(thread_ids, thread_names):
                if "{name}" in message_lines[message_index]:
                    content = message_lines[message_index].replace("{name}", replace_text)
                else:
                    content = message_lines[message_index]

                status = messenger.send_message(thread_id, content,
                                                tag_ids, tag_names)

                phase += 0.5
                if status == "success":
                    ok_count += 1
                    tag_line = (f"  ✓ {account_name[:14]:<14} · "
                                f"{thread_name[:20]:<20} · "
                                f"tag {len(tag_names):>3} · "
                                f"✓ {ok_count:<4} ✗ {fail_count}")
                    print("\r" + wave(tag_line, phase, offset=0.30)
                          + E + "K", end="", flush=True)
                else:
                    fail_count += 1
                    # in lý do riêng
                    print("\r" + E + "K")
                    print(wave(f"  ✗ {account_name[:14]} · "
                               f"{thread_name[:20]} · status={status}",
                               phase, offset=0.85))
                    # in lại counter
                    tag_line = (f"  ✓ {account_name[:14]:<14} · "
                                f"{thread_name[:20]:<20} · "
                                f"tag {len(tag_names):>3} · "
                                f"✓ {ok_count:<4} ✗ {fail_count}")
                    print(wave(tag_line, phase, offset=0.30),
                          end="", flush=True)

                message_index = (message_index + 1) % len(message_lines)
                time.sleep(delay)
    except Exception as e:
        print()
        print(wave(f"  ✗ Lỗi tài khoản {account_name}: {str(e)}",
                   0, offset=0.85))


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def start_multiple_accounts():
    clear()
    animate_banner(36, 0.04)
    print()

    print_header("Z I N   T H I Ê N   Đ Ạ O   ·   W A R   M E S S")

    try:
        raw = input("  " + wave("❯ Số lượng acc muốn chạy: ",
                                time.time(), offset=0.55)).strip()
        num_accounts = int(raw)
        if num_accounts < 1:
            print_color("  ✗ Số lượng phải > 0", "error")
            return
    except ValueError:
        print_color("  ✗ Phải nhập số nguyên", "error")
        return

    processes = []

    for i in range(num_accounts):
        print_header(f"T À I   K H O Ả N   {i + 1}")

        cookie = input("  " + wave("❯ Cookie: ",
                                    time.time(), offset=0.55)).strip()
        if not cookie:
            print_color("  ✗ Cookie rỗng, bỏ qua", "error")
            continue

        print_color("  ⟳ Đang kiểm tra linh thức...", "info")
        cl = check_live(cookie)
        if cl["status"] == "success":
            print_color(f"  ✓ Tu sĩ: {cl['name']} (ID: {cl['user_id']})", "success")
        else:
            print_color(f"  ✗ Lỗi: {cl['msg']}", "error")
            continue

        try:
            messenger = Messenger(cookie)
            print_color("  ⟳ Đang quét động phủ...", "info")
            result = messenger.get_thread_list(limit=100)
            if "error" in result:
                print_color(f"  ✗ {result['error']}", "error")
                continue
            threads_list = result["threads"]
            if not threads_list:
                print_color("  ✗ Không có động phủ nào", "error")
                continue

            table = Table(title=f"📦 DANH SÁCH ĐỘNG PHỦ — {len(threads_list)}",
                          show_header=True, header_style="bold magenta",
                          box=box.ROUNDED)
            table.add_column("STT", style="cyan", width=5, justify="center")
            table.add_column("Tên Động Phủ", style="green")
            table.add_column("ID", style="yellow")
            for idx, thread in enumerate(threads_list, 1):
                tn = thread.get("thread_name", "Không có tên") or "Không có tên"
                disp = f"{tn[:45]}{'...' if len(tn) > 45 else ''}"
                table.add_row(str(idx), disp, thread["thread_id"])
            console.print(table)

            raw = input("  " + wave("❯ Chọn động phủ (1,3 / all): ",
                                     time.time(), offset=0.55)).strip()
            if raw.lower() == "all":
                selected = list(range(1, len(threads_list) + 1))
            else:
                selected = parse_selection(raw, len(threads_list))
            if not selected:
                print_color("  ✗ Chưa chọn động phủ nào", "error")
                continue

            selected_ids = [threads_list[i - 1]["thread_id"] for i in selected]
            selected_names = [threads_list[i - 1]["thread_name"] or "Không có tên"
                              for i in selected]

            print_color("  ⟳ Đang triệu hồi danh sách đệ tử...", "info")
            members = []
            for thread_id in selected_ids:
                result = messenger.get_group_members(thread_id)
                if result.get("success"):
                    members.extend(result["members"])
                else:
                    print_color(f"  ⚠ {thread_id}: {result['error']}", "warning")

            if not members:
                print_color("  ✗ Không có đệ tử nào", "error")
                continue

            # dedupe
            seen, unique = set(), []
            for m in members:
                if m["id"] in seen:
                    continue
                seen.add(m["id"])
                unique.append(m)
            members = unique

            mtable = Table(title=f"👥 DANH SÁCH ĐỆ TỬ — {len(members)}",
                           show_header=True, header_style="bold blue",
                           box=box.ROUNDED)
            mtable.add_column("STT", style="cyan", width=5, justify="center")
            mtable.add_column("Tên", style="green")
            mtable.add_column("ID", style="yellow")
            for idx, member in enumerate(members, 1):
                mn = (member["name"] or "?")[:40]
                disp = f"{mn}{'...' if len(mn) > 40 else ''}"
                mtable.add_row(str(idx), disp, member["id"])
            console.print(mtable)

            raw_tags = input("  " + wave("❯ Tag đệ tử (1,2,3 / all / khong): ",
                                          time.time(), offset=0.55)).strip()
            tag_ids, tag_names = [], []
            if raw_tags.lower() != "khong":
                if raw_tags.lower() == "all":
                    selected_tags = list(range(1, len(members) + 1))
                else:
                    selected_tags = parse_selection(raw_tags, len(members))
                if not selected_tags:
                    print_color("  ✗ Chưa chọn đệ tử nào", "error")
                    continue
                tag_ids = [members[i - 1]["id"] for i in selected_tags]
                tag_names = [members[i - 1]["name"] for i in selected_tags]
                print_color(f"  ✓ Đã chọn {len(tag_ids)} đệ tử", "success")

            file_txt = input("  " + wave("❯ File .txt pháp quyết: ",
                                          time.time(), offset=0.55)).strip()
            try:
                message_lines = load_file(file_txt)
                print_color(f"  ✓ Tải {len(message_lines)} dòng", "success")
            except Exception as e:
                print_color(f"  ✗ {e}", "error")
                continue

            replace_text = input("  " + wave("❯ Nội dung thay {name} (Enter bỏ qua): ",
                                              time.time(), offset=0.55)).strip()

            try:
                delay = int(input("  " + wave("❯ Delay (giây): ",
                                               time.time(), offset=0.55)))
                if delay < 1:
                    print_color("  ✗ Delay phải >= 1", "error")
                    continue
            except ValueError:
                print_color("  ✗ Delay phải là số nguyên", "error")
                continue

            print_header(f"K H A I   M Ở   ·   {cl['name']}")
            if tag_ids:
                print_color(f"  ⟡ Tag {len(tag_ids)} người: "
                            f"{', '.join(tag_names[:3])}"
                            f"{'...' if len(tag_names) > 3 else ''}", "cyan")
            if messenger.mqtt_manager and messenger.mqtt_manager.connected:
                print_color("  ✓ MQTT sẵn sàng", "success")
            else:
                print_color("  ⚠ Dùng HTTP thường", "warning")

            p = multiprocessing.Process(
                target=start_spam,
                args=(cookie, cl["name"], cl["user_id"],
                      selected_ids, selected_names, delay,
                      message_lines, replace_text, tag_ids, tag_names),
            )
            processes.append(p)
            p.start()
            time.sleep(2)
        except Exception as e:
            print_color(f"  ✗ Lỗi tài khoản {cl['name']}: {e}", "error")
            continue

    if not processes:
        print_color("  ✗ Không có process nào chạy", "error")
        return

    print_header("Đ A N G   C H Ạ Y")
    print_color(f"  ✓ {len(processes)} acc đang chạy", "success")
    print_color("  ⟡ Ctrl+C để dừng", "warning")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print_color("  ⟳ Đang dừng...", "warning")
        for p in processes:
            p.terminate()
        time.sleep(2)
        print_color("  ✓ Đã dừng tất cả", "success")


if __name__ == "__main__":
    try:
        start_multiple_accounts()
    except KeyboardInterrupt:
        print_color("\n  ⟡ Đã dừng", "info")
    except Exception as e:
        print_color(f"\n  ✗ Lỗi: {e}", "error")
        import traceback
        traceback.print_exc()