import os
import sys
import time
import ssl
import json
import random
import string
import hashlib
import threading
import re
import gc
import shutil
import warnings
from collections import defaultdict
from urllib.parse import urlparse
import requests
import paho.mqtt.client as mqtt

warnings.filterwarnings("ignore", category=DeprecationWarning)

# =============== BIẾN TOÀN CỤC ===============
active_threads = {}
cookie_attempts = defaultdict(lambda: {
    'count': 0, 'last_reset': time.time(),
    'banned_until': 0, 'permanent_ban': False
})
cleanup_lock = threading.Lock()
_output_lock = threading.Lock()

# Cache membership: cookie_hash -> {thread_id: bool}
thread_membership_cache = {}

# =============== STATUS BAR ===============
_status_cooldowns = {}      # {tag: {'end': ts, 'total': sec}}
_status_lock = threading.Lock()
_status_running = True
_status_visible = False


def status_register(tag, duration):
    with _status_lock:
        _status_cooldowns[tag] = {
            'end': time.time() + duration,
            'total': duration,
        }


def status_unregister(tag):
    with _status_lock:
        _status_cooldowns.pop(tag, None)


# =============== ANSI / LED GRADIENT ===============
RESET = "\033[0m"
CLEAR = "\033[2K\r"


def c256(code, text):
    return f"\033[38;5;{code}m{text}{RESET}"


def hue_to_rgb(h):
    h = h % 360
    c = 255
    x = int(c * (1 - abs((h / 60) % 2 - 1)))
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return r, g, b


def ansi_led(hue, bold=False):
    r, g, b = hue_to_rgb(hue)
    b_part = "1;" if bold else ""
    return f"\033[{b_part}38;2;{r};{g};{b}m"


def led_string(text, hue_base=0.0, hue_span=360.0):
    if not text:
        return ""
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(ch)
        else:
            out.append(ansi_led(hue_base + (i / n) * hue_span) + ch)
    out.append(RESET)
    return "".join(out)


def rainbow(text, offset=0):
    return led_string(text, hue_base=float(offset) * 30.0, hue_span=360.0)


OK   = lambda s: c256(46, s)
ERR  = lambda s: c256(196, s)
WARN = lambda s: c256(220, s)
INFO = lambda s: c256(51, s)


def clear_all():
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[3J\033[2J\033[H")
        sys.stdout.flush()


def term_width():
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except Exception:
        return 80


def safe_print(*args, **kwargs):
    """In log — tự xóa dòng status bar nếu đang hiển thị."""
    global _status_visible
    with _output_lock:
        if _status_visible:
            sys.stdout.write("\033[2K\r")
            sys.stdout.flush()
            _status_visible = False
        print(*args, **kwargs)
        sys.stdout.flush()


def _visual_len(s):
    """Đếm chiều dài hiển thị của string, bỏ ANSI escape."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def status_thread():
    """Thread duy nhất vẽ 1 cooldown bar cho cookie gần xong nhất.
    Format: 🌈 [tag] Cooldown [████████░░░░░░░░░] 02:59:48 (+2)
    """
    global _status_visible
    while _status_running:
        with _status_lock:
            items = dict(_status_cooldowns)

        now = time.time()
        active = {t: i for t, i in items.items() if i['end'] > now}

        if not active:
            with _output_lock:
                if _status_visible:
                    sys.stdout.write("\033[2K\r")
                    sys.stdout.flush()
                    _status_visible = False
            time.sleep(0.15)
            continue

        # Chọn cookie gần xong nhất
        sorted_items = sorted(active.items(), key=lambda kv: kv[1]['end'])
        tag, info = sorted_items[0]
        others = len(sorted_items) - 1

        rem = info['end'] - now
        progress = min(max(1 - rem / info['total'], 0), 1)

        m, s = divmod(int(rem), 60)
        h, m = divmod(m, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        # Tính bar_len theo chiều rộng terminal
        tw = term_width()
        # Prefix: "🌈 tag Cooldown [" — tính thô ~ 20 chars cho tag 8 ký tự
        prefix_len = 4 + len(tag) + 10   # "🌈 " + tag + " Cooldown ["
        suffix_plain = f"] {ts}"
        if others:
            suffix_plain += f" (+{others})"
        suffix_len = len(suffix_plain)

        bar_len = max(6, min(40, tw - prefix_len - suffix_len - 2))

        filled = int(bar_len * progress)
        hue_base = int(now * 80) % 360

        bar = ""
        for i in range(bar_len):
            if i < filled:
                # Hue chạy từ trái sang phải
                bar += ansi_led(hue_base + i * (240 / max(bar_len - 1, 1))) + "█"
            else:
                bar += "\033[38;5;236m░"
        bar += RESET

        line = (f"\033[38;5;{hue_base % 256}m🌈{RESET} "
                f"{c256(51, tag)} Cooldown [{bar}] {c256(245, ts)}")
        if others:
            line += c256(245, f" (+{others})")

        with _output_lock:
            sys.stdout.write("\033[2K\r" + line)
            sys.stdout.flush()
            _status_visible = True

        time.sleep(0.1)


# =============== BANNER ===============
def banner():
    w = min(term_width() - 8, 52)
    title = "T O O L   W A R   M E S S"
    sub   = "Z I N"

    clear_all()
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    def draw(hue_base):
        border = "".join(ansi_led(hue_base + (i / max(w - 1, 1)) * 360) + "─" for i in range(w))
        corner = ansi_led(hue_base) + "◆" + RESET
        title_line = led_string(title.center(w), hue_base + 60, 300)
        sub_line   = led_string(sub.center(w), hue_base + 180, 180)
        lines = [
            f"  {corner}  {border}  {corner}",
            "",
            f"    {title_line}",
            f"    {sub_line}",
            "",
            f"  {corner}  {border}  {corner}",
        ]
        sys.stdout.write("\033[H")
        for ln in lines:
            sys.stdout.write(ln + "\n")
        sys.stdout.flush()

    for f in range(70):
        draw(f * 9)
        time.sleep(0.035)
    draw(70 * 9)
    sys.stdout.write("\n\033[?25h")
    sys.stdout.flush()


def loading_line(duration=1.2, label="Đang khởi động"):
    dots = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    start = time.time()
    i = 0
    while time.time() - start < duration:
        hue = i * 18
        with _output_lock:
            sys.stdout.write(
                f"\r  {ansi_led(hue)}◈{RESET}  {label}  "
                f"{ansi_led(hue + 60)}{dots[i % 10]}{RESET}   "
            )
            sys.stdout.flush()
        time.sleep(0.07)
        i += 1
    with _output_lock:
        sys.stdout.write("\r" + " " * 55 + "\r")
        sys.stdout.flush()


# =============== UTILS ===============
def generate_offline_threading_id():
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    return str(int(bin(ret)[2:] + binary_str, 2))


def generate_session_id():
    return random.randint(1, 2 ** 53)


def generate_client_id():
    g = lambda n: "".join(random.choices(string.ascii_lowercase + string.digits, k=n))
    return f"{g(8)}-{g(4)}-{g(4)}-{g(4)}-{g(12)}"


def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))


def parse_cookie_string(s):
    d = {}
    for c in s.split(";"):
        if "=" in c:
            k, v = c.strip().split("=", 1)
            d[k] = v
    return d


def digitToChar(d):
    return str(d) if d < 10 else chr(ord('a') + d - 10)


def str_base(n, b):
    if n < 0:
        return "-" + str_base(-n, b)
    d, m = divmod(n, b)
    return (str_base(d, b) if d else "") + digitToChar(m)


class Counter:
    def __init__(self, v=0): self.value = v
    def increment(self):
        self.value += 1
        return self.value


def formAll(dataFB, requireGraphql=None):
    global _req_counter
    if '_req_counter' not in globals():
        _req_counter = Counter(0)
    reg = _req_counter.increment()
    f = {
        "fb_dtsg": dataFB["fb_dtsg"],
        "jazoest": dataFB["jazoest"],
        "__a": 1,
        "__user": str(dataFB["FacebookID"]),
        "__req": str_base(reg, 36),
        "__rev": dataFB["clientRevision"],
        "av": dataFB["FacebookID"],
    }
    if requireGraphql is None:
        f["fb_api_caller_class"] = "RelayModern"
        f["server_timestamps"] = "true"
    return f


def mainRequests(url, data, cookies):
    return {
        "url": url,
        "data": data,
        "headers": {
            "authority": "www.facebook.com",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": "https://www.facebook.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        },
        "cookies": parse_cookie_string(cookies),
        "verify": True,
    }


def handle_failed_connection(cookie_hash):
    now = time.time()
    if now - cookie_attempts[cookie_hash]['last_reset'] > 43200:
        cookie_attempts[cookie_hash].update({'count': 0, 'last_reset': now, 'banned_until': 0})
    if cookie_attempts[cookie_hash]['banned_until'] > 0:
        ban_count = cookie_attempts[cookie_hash].get('ban_count', 0) + 1
        cookie_attempts[cookie_hash]['ban_count'] = ban_count
        if ban_count >= 5:
            cookie_attempts[cookie_hash]['permanent_ban'] = True
            safe_print(ERR(f"🚫 {cookie_hash[:10]} ban vĩnh viễn"))
            for key in list(active_threads.keys()):
                if key.startswith(cookie_hash):
                    try:
                        active_threads[key].stop()
                    except Exception:
                        pass
                    del active_threads[key]


# =============== CHECK USER IN THREAD ===============
def check_user_in_thread(user_id, thread_id, dataFB):
    """Trả True/False/None — cache kết quả."""
    ch = hashlib.md5(dataFB['cookieFacebook'].encode()).hexdigest()
    if ch in thread_membership_cache and thread_id in thread_membership_cache[ch]:
        return thread_membership_cache[ch][thread_id]

    try:
        form = {
            "queries": json.dumps({
                "o0": {
                    "doc_id": "3449967031715030",
                    "query_params": {
                        "id": str(thread_id),
                        "message_limit": 0,
                        "load_messages": False,
                        "load_read_receipts": False,
                        "before": None
                    }
                }
            }, separators=(",", ":")),
            "batch_name": "MessengerGraphQLThreadFetcher",
            "fb_dtsg": dataFB["fb_dtsg"],
            "jazoest": dataFB["jazoest"],
            "__user": str(dataFB["FacebookID"]),
            "__a": "1",
            "__req": "1",
            "__rev": dataFB.get("clientRevision", "1015919737")
        }
        headers = {
            "authority": "www.facebook.com",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": "https://www.facebook.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        }
        r = requests.post(
            "https://www.facebook.com/api/graphqlbatch/",
            data=form, headers=headers,
            cookies=parse_cookie_string(dataFB["cookieFacebook"]),
            timeout=10
        )
        txt = r.text
        if txt.startswith("for(;;);"):
            txt = txt[9:]
        first = txt.split("\n")[0]
        data = json.loads(first)
        message_thread = data["o0"]["data"]["message_thread"]
        pids = [str(edge["node"]["messaging_actor"]["id"])
                for edge in message_thread["all_participants"]["edges"]]
        result = str(user_id) in pids

        if ch not in thread_membership_cache:
            thread_membership_cache[ch] = {}
        thread_membership_cache[ch][thread_id] = result
        return result
    except Exception:
        return None


# =============== NHẬP COOKIE ===============
def input_cookies_from_console():
    print(INFO("📋 Dán cookie (mỗi dòng 1 cái, Enter trống để xong):"))
    cookies, empty = [], 0
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if not line:
            empty += 1
            if empty >= 1 and cookies:
                break
            continue
        empty = 0
        cookies.append(line)
    valid = [c for c in cookies if "c_user=" in c and ";" in c]
    if not valid:
        print(ERR("❌ Không có cookie hợp lệ"))
        return []
    print(OK(f"✓ {len(valid)} cookie OK") + "\n")
    return valid


# =============== fbTools ===============
class fbTools:
    def __init__(self, dataFB, threadID="0"):
        self.threadID = threadID
        self.dataFB = dataFB
        self.last_seq_id = None

    def getAllThreadList(self):
        for doc_id in ("23920529507501519", "3336396659757871"):
            try:
                f = formAll(self.dataFB, requireGraphql=0)
                f["queries"] = json.dumps({
                    "o0": {
                        "doc_id": doc_id,
                        "query_params": {
                            "limit": 20, "before": None, "tags": ["INBOX"],
                            "includeDeliveryReceipts": False, "includeSeqID": True,
                        }
                    }
                })
                r = requests.post(
                    **mainRequests("https://www.facebook.com/api/graphqlbatch/",
                                   f, self.dataFB["cookieFacebook"]),
                    timeout=15
                )
                txt = r.text
                if txt.startswith("for(;;);"):
                    txt = txt[9:]
                if not txt.strip():
                    continue
                first = txt.split("\n")[0]
                if not first.strip():
                    continue
                data = json.loads(first)
                seq = (data.get("o0", {}).get("data", {})
                       .get("viewer", {}).get("message_threads", {})
                       .get("sync_sequence_id"))
                if seq:
                    self.last_seq_id = seq
                    return True
                seq = self._find_seq(data)
                if seq:
                    self.last_seq_id = seq
                    return True
            except Exception:
                continue
        self.last_seq_id = "0"
        return True

    def _find_seq(self, obj):
        if isinstance(obj, dict):
            if "sync_sequence_id" in obj and obj["sync_sequence_id"]:
                return obj["sync_sequence_id"]
            for v in obj.values():
                r = self._find_seq(v)
                if r:
                    return r
        elif isinstance(obj, list):
            for item in obj:
                r = self._find_seq(item)
                if r:
                    return r
        return None


# =============== MessageSender ===============
class MessageSender:
    def __init__(self, fbt, dataFB, fb_instance):
        self.fbt = fbt
        self.dataFB = dataFB
        self.fb_instance = fb_instance
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.syncToken = None
        self.lastSeqID = None
        self.req_callbacks = {}
        self.cookie_hash = hashlib.md5(dataFB['cookieFacebook'].encode()).hexdigest()
        self.last_cleanup = time.time()

    def cleanup_memory(self):
        if time.time() - self.last_cleanup > 3600:
            self.req_callbacks.clear()
            gc.collect()
            self.last_cleanup = time.time()

    def get_last_seq_id(self):
        ok = self.fbt.getAllThreadList()
        if ok and self.fbt.last_seq_id:
            self.lastSeqID = self.fbt.last_seq_id
        else:
            self.lastSeqID = "0"
        return True

    def on_disconnect(self, client, userdata, rc):
        now = time.time()
        cookie_attempts[self.cookie_hash]['count'] += 1
        if now - cookie_attempts[self.cookie_hash]['last_reset'] > 43200:
            cookie_attempts[self.cookie_hash]['count'] = 1
            cookie_attempts[self.cookie_hash]['last_reset'] = now
        if cookie_attempts[self.cookie_hash]['count'] >= 20:
            cookie_attempts[self.cookie_hash]['banned_until'] = now + 43200
            return
        if cookie_attempts[self.cookie_hash]['banned_until'] > now:
            return
        if rc != 0:
            try:
                time.sleep(min(cookie_attempts[self.cookie_hash]['count'] * 2, 30))
                client.reconnect()
            except Exception:
                pass

    def _messenger_queue_publish(self, client, userdata, flags, rc):
        if rc != 0:
            return
        client.subscribe([("/t_ms", 0)])
        q = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self.dataFB['FacebookID'],
        }
        if self.syncToken is None:
            topic = "/messenger_sync_create_queue"
            q["initial_titan_sequence_id"] = self.lastSeqID
            q["device_params"] = None
        else:
            topic = "/messenger_sync_get_diffs"
            q["last_seq_id"] = self.lastSeqID
            q["sync_token"] = self.syncToken
        client.publish(topic, json_minimal(q), qos=1, retain=False)

    def connect_mqtt(self):
        if cookie_attempts[self.cookie_hash]['permanent_ban']:
            return False
        now = time.time()
        if now < cookie_attempts[self.cookie_hash]['banned_until']:
            return False
        if not self.lastSeqID:
            self.lastSeqID = "0"

        session_id = generate_session_id()
        user = {
            "u": self.dataFB["FacebookID"], "s": session_id,
            "chat_on": json_minimal(True), "fg": False,
            "d": generate_client_id(), "ct": "websocket",
            "aid": 219994525426954, "mqtt_sid": "", "cp": 3, "ecp": 10,
            "st": ["/t_ms", "/messenger_sync_get_diffs", "/messenger_sync_create_queue"],
            "pm": [], "dc": "", "no_auto_fg": True, "gas": None, "pack": [],
        }
        host = f"wss://edge-chat.messenger.com/chat?region=eag&sid={session_id}"

        try:
            from paho.mqtt.client import CallbackAPIVersion
            self.mqtt = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION1,
                client_id="mqttwsclient", clean_session=True,
                protocol=mqtt.MQTTv31, transport="websockets",
            )
        except (ImportError, AttributeError):
            self.mqtt = mqtt.Client(
                client_id="mqttwsclient", clean_session=True,
                protocol=mqtt.MQTTv31, transport="websockets",
            )

        self.mqtt.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE,
                          tls_version=ssl.PROTOCOL_TLSv1_2)
        self.mqtt.on_connect = self._messenger_queue_publish
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.username_pw_set(username=json_minimal(user))

        p = urlparse(host)
        self.mqtt.ws_set_options(
            path=f"{p.path}?{p.query}",
            headers={
                "Cookie": self.dataFB['cookieFacebook'],
                "Origin": "https://www.messenger.com",
                "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/69.0.3497.100 Mobile Safari/537.36",
                "Referer": "https://www.messenger.com/",
                "Host": "edge-chat.messenger.com",
            },
        )
        try:
            self.mqtt.connect("edge-chat.messenger.com", 443, keepalive=10)
            self.mqtt.loop_start()
            for _ in range(50):
                if self.mqtt.is_connected():
                    return True
                time.sleep(0.1)
            return False
        except Exception:
            cookie_attempts[self.cookie_hash]['count'] += 1
            return False

    def stop(self):
        if self.mqtt:
            try:
                self.mqtt.disconnect()
                self.mqtt.loop_stop()
            except Exception:
                pass
        self.cleanup_memory()

    def send_message(self, text, thread_id):
        if self.mqtt is None:
            return False
        if not self.mqtt.is_connected():
            for _ in range(30):
                if self.mqtt.is_connected():
                    break
                time.sleep(0.1)
            if not self.mqtt.is_connected():
                return False
        if not thread_id or text is None:
            return False

        self.cleanup_memory()
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

        text = str(text)
        if text:
            self.ws_task_number += 1
            content["payload"]["tasks"].append({
                "failure_count": None, "label": "46",
                "payload": json.dumps({
                    "initiating_source": 0, "multitab_env": 0,
                    "otid": generate_offline_threading_id(),
                    "send_type": 1, "skip_url_preview_gen": 0,
                    "source": 0, "sync_group": 1,
                    "text": text, "text_has_links": 0,
                    "thread_id": int(thread_id),
                }, separators=(",", ":")),
                "queue_name": str(thread_id), "task_id": self.ws_task_number,
            })

        self.ws_task_number += 1
        content["payload"]["tasks"].append({
            "failure_count": None, "label": "21",
            "payload": json.dumps({
                "last_read_watermark_ts": int(time.time() * 1000),
                "sync_group": 1, "thread_id": int(thread_id),
            }, separators=(",", ":")),
            "queue_name": str(thread_id), "task_id": self.ws_task_number,
        })

        content["payload"] = json.dumps(content["payload"], separators=(",", ":"))
        try:
            self.mqtt.publish("/ls_req",
                              json.dumps(content, separators=(",", ":")),
                              qos=1, retain=False)
            return True
        except Exception:
            return False


# =============== ngquanghuyakadzi ===============
class ngquanghuyakadzi:
    def __init__(self, cookie, mqtt_broker="broker.hivemq.com", mqtt_port=1883):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.init_params()

    def id_user(self):
        try:
            match = re.search(r"c_user=(\d+)", self.cookie)
            if not match:
                raise Exception("Cookie không hợp lệ")
            return match.group(1)
        except Exception as e:
            raise Exception(f"Lỗi khi lấy user_id: {str(e)}")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
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
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
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
                    return
            except Exception:
                time.sleep(2)
        raise Exception("Không thể lấy được fb_dtsg từ bất kỳ URL nào")


# =============== WORKER CHO TỪNG COOKIE ===============
def cookie_worker(cookie, thread_ids, message_files, delay):
    ch = hashlib.md5(cookie.encode()).hexdigest()
    tag = ch[:8]

    if cookie_attempts[ch]['permanent_ban']:
        return
    if time.time() < cookie_attempts[ch]['banned_until']:
        return

    sender = None
    try:
        fb = ngquanghuyakadzi(cookie)
        dataFB = {
            "FacebookID": fb.user_id, "fb_dtsg": fb.fb_dtsg,
            "clientRevision": fb.rev, "jazoest": fb.jazoest,
            "cookieFacebook": cookie,
        }
        sender = MessageSender(fbTools(dataFB), dataFB, fb)
        sender.get_last_seq_id()

        if not sender.connect_mqtt():
            safe_print(ERR(f"[{tag}] ❌ MQTT fail"))
            handle_failed_connection(ch)
            return

        # Pre-check membership
        in_box = {}
        for tid in thread_ids:
            r = check_user_in_thread(fb.user_id, tid, dataFB)
            in_box[tid] = r

        not_in = [t for t, v in in_box.items() if v is False]
        if not_in:
            safe_print(WARN(f"[{tag}] ⚠️  Không có trong {len(not_in)} box: {', '.join(t[-6:] for t in not_in)}"))
        safe_print(OK(f"[{tag}] ✓ ready"))

        round_n = 0
        while True:
            if cookie_attempts[ch]['banned_until'] > time.time():
                safe_print(ERR(f"[{tag}] 🚫 bị ban, dừng"))
                break

            round_n += 1
            content = ""
            if message_files:
                sel = random.choice(message_files) if len(message_files) > 1 else message_files[0]
                with open(sel, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

            safe_print(rainbow(f"[{tag}] ─── Vòng #{round_n} ───"))

            ok_count = 0
            fail_count = 0
            skip_count = 0

            for tid in thread_ids:
                # Không có trong box → skip, đánh dấu ⚠
                if in_box.get(tid) is False:
                    safe_print(WARN(f"  [{tag}] 📤 {tid}  ⚠  not in box"))
                    skip_count += 1
                    continue

                active_threads[f"{ch}_{tid}"] = sender
                try:
                    ok = sender.send_message(content, tid)
                    if ok:
                        ok_count += 1
                        safe_print(OK(f"  [{tag}] 📤 {tid}  ✓"))
                    else:
                        fail_count += 1
                        safe_print(ERR(f"  [{tag}] 📤 {tid}  ✗"))
                except Exception as e:
                    fail_count += 1
                    safe_print(ERR(f"  [{tag}] 📤 {tid}  ✗ {e}"))
                finally:
                    active_threads.pop(f"{ch}_{tid}", None)

            # Tổng kết vòng
            summary_parts = [OK(f"{ok_count}✓") if ok_count else None,
                             ERR(f"{fail_count}✗") if fail_count else None,
                             WARN(f"{skip_count}⚠") if skip_count else None]
            summary = " ".join(p for p in summary_parts if p)
            safe_print(f"[{tag}] → Vòng #{round_n}: {summary}")

            # Đăng ký status bar
            status_register(tag, delay)

            # Chờ cooldown — status thread vẽ bar
            end_t = time.time() + delay
            while time.time() < end_t:
                if cookie_attempts[ch]['banned_until'] > time.time():
                    break
                time.sleep(0.5)

            status_unregister(tag)
            safe_print(OK(f"[{tag}] ✅ Cooldown xong"))
            gc.collect()

    except KeyboardInterrupt:
        raise
    except Exception as e:
        safe_print(ERR(f"[{tag}] ❌ {e}"))
        handle_failed_connection(ch)
    finally:
        status_unregister(tag)
        if sender:
            try:
                sender.stop()
            except Exception:
                pass


# =============== MODE 1 - MULTI-THREAD ===============
def send_messages_with_cookie(cookies, thread_ids, message_files, delay):
    threads = []
    for i, cookie in enumerate(cookies):
        t = threading.Thread(
            target=cookie_worker,
            args=(cookie, thread_ids, message_files, delay),
            daemon=True,
            name=f"cookie-{i}"
        )
        t.start()
        threads.append(t)
        if i < len(cookies) - 1:
            time.sleep(2)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        safe_print(WARN("\n⏹  Dừng tất cả cookie."))
        return


# =============== MAIN ===============
if __name__ == "__main__":
    try:
        banner()
        loading_line(1.2, "Đang khởi động")

        # Start status thread
        st = threading.Thread(target=status_thread, daemon=True, name="status")
        st.start()

        cookies = input_cookies_from_console()
        if not cookies:
            exit()

        num = int(input(INFO("🔢 Số box: ")).strip())
        thread_ids = []
        for i in range(num):
            tid = input(f"  📦 Box {i+1}: ").strip()
            if tid:
                thread_ids.append(tid)
        if not thread_ids:
            print(ERR("❌ Chưa có box"))
            exit()

        delay = float(input(INFO("⏱️  Delay (s): ")).strip())
        fp = input(INFO("📄 File nội dung: ")).strip()
        if not os.path.isfile(fp):
            print(ERR(f"❌ Không tìm thấy {fp}"))
            exit()

        print()
        safe_print(rainbow(f"🚀 Bắt đầu — {len(cookies)} cookie • {len(thread_ids)} box • {int(delay)}s"))
        print()

        send_messages_with_cookie(cookies, thread_ids, [fp], delay)

    except KeyboardInterrupt:
        print(WARN("\n⏹  Thoát."))
    except Exception as e:
        print(ERR(f"❌ {e}"))