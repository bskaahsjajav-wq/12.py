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
import gzip
import zlib
import warnings
from collections import defaultdict
from urllib.parse import urlparse
import requests
import paho.mqtt.client as mqtt

from rich.console import Console
from rich.table import Table
from rich import box as rich_box

console = Console()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# =============== BIẾN TOÀN CỤC ===============
active_threads = {}
cookie_attempts = defaultdict(lambda: {
    'count': 0, 'last_reset': time.time(),
    'banned_until': 0, 'permanent_ban': False
})
cleanup_lock = threading.Lock()
_output_lock = threading.Lock()
thread_membership_cache = {}

# =============== STATUS BAR ===============
_status_cooldowns = {}
_status_lock = threading.Lock()
_status_running = True
_status_visible = False


def status_register(tag, duration):
    with _status_lock:
        _status_cooldowns[tag] = {'end': time.time() + duration, 'total': duration}


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
    global _status_visible
    with _output_lock:
        if _status_visible:
            sys.stdout.write("\033[2K\r")
            sys.stdout.flush()
            _status_visible = False
        print(*args, **kwargs)
        sys.stdout.flush()


def status_thread():
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

        sorted_items = sorted(active.items(), key=lambda kv: kv[1]['end'])
        tag, info = sorted_items[0]
        others = len(sorted_items) - 1

        rem = info['end'] - now
        progress = min(max(1 - rem / info['total'], 0), 1)

        m, s = divmod(int(rem), 60)
        h, m = divmod(m, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        tw = term_width()
        prefix_len = 4 + len(tag) + 10
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


def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(",")]
        return [n for n in numbers if 1 <= n <= max_index]
    except Exception:
        return []


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


# =============== DECODE HELPERS ===============
def decode_response_content(response: requests.Response) -> str:
    content = response.content
    enc = response.headers.get('Content-Encoding', '').lower()
    if not enc:
        if content.startswith(b'\x1f\x8b'):
            enc = 'gzip'
        elif content.startswith(b'\x78\x9c') or content.startswith(b'\x78\x01') or content.startswith(b'\x78\xda'):
            enc = 'deflate'
    if enc:
        try:
            if 'gzip' in enc:
                content = gzip.decompress(content)
            elif 'deflate' in enc:
                try:
                    content = zlib.decompress(content)
                except zlib.error:
                    content = zlib.decompress(content, -zlib.MAX_WBITS)
        except Exception:
            pass
    encoding = response.encoding
    if not encoding or encoding.lower() == 'iso-8859-1':
        apparent = response.apparent_encoding
        encoding = apparent if apparent and apparent.lower() != 'iso-8859-1' else 'utf-8'
    try:
        return content.decode(encoding, errors='replace')
    except Exception:
        return content.decode('utf-8', errors='replace')


def decode_name(name: str) -> str:
    if not name:
        return name
    try:
        if '\\u' in name or '\\x' in name:
            return name.encode('utf-8').decode('unicode_escape')
    except Exception:
        pass
    return name


# =============== CHECK USER IN THREAD ===============
def check_user_in_thread(user_id, thread_id, dataFB):
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


# =============== ngquanghuyakadzi (FIX với fallback doc_id) ===============
class ngquanghuyakadzi:
    FALLBACK_DOC_IDS = [
        "1349387578499440",
        "3336396659757871",
        "23920529507501519",
        "7234662549190201",
        "7447696054558260",
        "8911057564852391",
    ]
    FALLBACK_FRIENDLY = "ThreadListQuery"

    def __init__(self, cookie, mqtt_broker="broker.hivemq.com", mqtt_port=1883):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.thread_list_doc_id = None
        self.thread_list_friendly_name = None
        self.session = requests.Session()
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
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Referer': 'https://www.facebook.com/',
        }
        self.session.headers.update(headers)

        html = ""
        for url in ('https://www.facebook.com/messages/t/',
                    'https://www.facebook.com/messages/',
                    'https://www.facebook.com/'):
            try:
                r = self.session.get(url,
                                     cookies=parse_cookie_string(self.cookie),
                                     allow_redirects=True, timeout=15)
                if '/login' in r.url or '/checkpoint' in r.url:
                    continue
                if r.status_code != 200:
                    continue
                html = decode_response_content(r)
                if not html:
                    continue
                if re.search(r'"dtsg":\{"token":"([^"]+)"', html) or \
                   re.search(r'name="fb_dtsg" value="([^"]+)"', html) or \
                   re.search(r'"fb_dtsg":\{"token":"([^"]+)"', html):
                    break
            except Exception:
                continue

        if not html:
            raise Exception("Không thể load bất kỳ trang FB nào (cookie die/checkpoint?)")

        # ---- fb_dtsg ----
        patterns = [
            r'"dtsg":\{"token":"([^"]+)"',
            r'DTSGInitialData.*?setToken\("([^"]+)"\)',
            r'name="fb_dtsg" value="([^"]+)"',
            r'"fb_dtsg":\{"token":"([^"]+)"',
            r'\["fb_dtsg","([^"]+)"',
            r'"token":"(AQ[^"]{20,})"',
        ]
        fb_dtsg = None
        for pat in patterns:
            m = re.search(pat, html, re.DOTALL)
            if m:
                fb_dtsg = m.group(1)
                break
        if not fb_dtsg:
            raise Exception("Không tìm thấy fb_dtsg trong HTML")
        self.fb_dtsg = fb_dtsg

        # ---- jazoest ----
        jz = None
        for pat in [r'"jazoest":"(\d+)"', r'name="jazoest" value="(\d+)"', r'jazoest=(\d+)']:
            m = re.search(pat, html)
            if m:
                jz = m.group(1)
                break
        self.jazoest = jz if jz else ""

        # ---- __rev ----
        rev = None
        m = re.search(r'"__rev":"(\d+)"', html)
        if m:
            rev = m.group(1)
        self.rev = rev if rev else "1015919737"

        # ---- doc_id ----
        doc_id = None
        friendly_name = None
        thread_query_patterns = [
            r'"doc_id":"(\d+)"[^}]{0,500}?"queryName":"(ThreadListQuery|MessengerThreadListQuery)"',
            r'"queryName":"(ThreadListQuery|MessengerThreadListQuery)"[^}]{0,500}?"doc_id":"(\d+)"',
            r'"friendly_name":"(ThreadListQuery|MessengerThreadListQuery)"[^}]{0,800}?"doc_id":"(\d+)"',
            r'"doc_id":"(\d+)"[^}]{0,800}?"friendly_name":"(ThreadListQuery|MessengerThreadListQuery)"',
        ]
        for pat in thread_query_patterns:
            m = re.search(pat, html, re.DOTALL)
            if m:
                g1, g2 = m.group(1), m.group(2)
                if g1.isdigit():
                    doc_id, friendly_name = g1, g2
                else:
                    friendly_name, doc_id = g1, g2
                break

        if not doc_id:
            self.thread_list_doc_id = None
            self.thread_list_friendly_name = self.FALLBACK_FRIENDLY
        else:
            self.thread_list_doc_id = doc_id
            self.thread_list_friendly_name = friendly_name or self.FALLBACK_FRIENDLY

    def get_thread_list(self, limit=100):
        url = 'https://www.facebook.com/api/graphql/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.facebook.com/messages/t/',
            'Origin': 'https://www.facebook.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-FB-Friendly-Name': self.thread_list_friendly_name or 'ThreadListQuery',
            'X-FB-LSD': self.fb_dtsg or '',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        variables = {
            "count": limit,
            "cursor": None,
            "filter": {},
            "include_self": True,
            "threadType": "INBOX",
            "limit": limit,
        }

        doc_ids_to_try = []
        if self.thread_list_doc_id:
            doc_ids_to_try.append(self.thread_list_doc_id)
        for did in self.FALLBACK_DOC_IDS:
            if did not in doc_ids_to_try:
                doc_ids_to_try.append(did)

        last_error = None
        for doc_id in doc_ids_to_try:
            data = {
                "fb_dtsg": self.fb_dtsg,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": self.thread_list_friendly_name or 'ThreadListQuery',
                "variables": json.dumps(variables, separators=(",", ":")),
                "doc_id": doc_id,
                "dpr": "1",
                "__a": "1",
                "__req": "1",
                "__rev": self.rev,
                "fb_api_analytics_tags": "[]",
                "fb_api_req_app_id": "0",
                "fb_api_req_user_agent": headers['User-Agent'],
                "fb_api_req_referrer": "https://www.facebook.com/messages/t/",
                "fb_api_req_display": "popup",
                "fb_api_req_source": "www",
            }

            try:
                r = self.session.post(url, cookies=parse_cookie_string(self.cookie),
                                      headers=headers, data=data, timeout=20)
            except Exception as e:
                last_error = f"Request fail doc_id={doc_id}: {e}"
                continue

            if r.status_code != 200:
                last_error = f"HTTP {r.status_code} doc_id={doc_id}"
                continue

            decoded = decode_response_content(r)
            json_data = None
            try:
                json_data = json.loads(decoded)
            except json.JSONDecodeError:
                m = re.search(r'<pre[^>]*>(.*?)</pre>', decoded, re.DOTALL)
                if m:
                    try:
                        json_data = json.loads(m.group(1).strip())
                    except Exception:
                        pass

            if json_data is None:
                last_error = f"Parse fail doc_id={doc_id}. Raw: {decoded[:120]}"
                continue

            if 'errors' in json_data:
                msgs = [err.get('message', 'Unknown') for err in json_data['errors']]
                last_error = f"GraphQL doc_id={doc_id}: " + "; ".join(msgs)
                continue

            threads = []
            seen_ids = set()

            def extract_participants(thread_dict):
                participants = []
                for key in ['all_participants', 'participants']:
                    if key in thread_dict and isinstance(thread_dict[key], dict):
                        nodes = thread_dict[key].get('nodes', [])
                        if isinstance(nodes, list):
                            for p in nodes:
                                if isinstance(p, dict):
                                    uid = p.get('id')
                                    name = decode_name(p.get('name', p.get('short_name', 'Không tên')))
                                    if uid:
                                        participants.append((name, uid))
                return participants

            try:
                nodes = (json_data.get('data', {}).get('viewer', {})
                         .get('message_threads', {}).get('nodes')) or []
                for thread in nodes:
                    if not isinstance(thread, dict):
                        continue
                    tk = thread.get('thread_key') or {}
                    thread_fbid = tk.get('thread_fbid')
                    other_user_id = tk.get('other_user_id')
                    tid = thread_fbid or other_user_id
                    if not tid:
                        continue
                    tname = thread.get('name')
                    if tname:
                        tname = decode_name(tname)
                    else:
                        plist = extract_participants(thread)
                        tname = plist[0][0] if plist else 'Không tên'
                    if tid not in seen_ids:
                        seen_ids.add(tid)
                        threads.append({
                            "thread_id": tid,
                            "thread_name": tname,
                        })
            except Exception as e:
                last_error = f"Parse threads fail doc_id={doc_id}: {e}"
                continue

            if threads:
                self.thread_list_doc_id = doc_id
                return {"success": True, "thread_count": len(threads), "threads": threads}
            else:
                last_error = f"Nodes rỗng doc_id={doc_id}"
                continue

        return {"error": last_error or "Tất cả doc_id đều fail"}


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

        in_box = {}
        for tid in thread_ids:
            r = check_user_in_thread(fb.user_id, tid, dataFB)
            in_box[tid] = r

        not_in = [t for t, v in in_box.items() if v is False]
        if not_in:
            safe_print(WARN(f"[{tag}] ⚠️  Không có trong {len(not_in)} box: "
                            f"{', '.join(t[-6:] for t in not_in)}"))
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

            summary_parts = [OK(f"{ok_count}✓") if ok_count else None,
                             ERR(f"{fail_count}✗") if fail_count else None,
                             WARN(f"{skip_count}⚠") if skip_count else None]
            summary = " ".join(p for p in summary_parts if p)
            safe_print(f"[{tag}] → Vòng #{round_n}: {summary}")

            status_register(tag, delay)

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


# =============== MULTI-THREAD ===============
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


# =============== CHỌN BOX TƯƠNG TÁC ===============
def select_threads_interactive(cookies):
    fb = None
    result = None
    for ck in cookies:
        try:
            print(INFO(f"📦 Đang lấy danh sách box... (thử cookie {ck[:25]}...)"))
            fb = ngquanghuyakadzi(ck)
            print(INFO(f"   → fb_dtsg={fb.fb_dtsg[:25]}... | rev={fb.rev} | "
                       f"jazoest={fb.jazoest[:10]} | doc_id={fb.thread_list_doc_id}"))
            result = fb.get_thread_list(limit=100)
            if "error" not in result and result.get("threads"):
                break
            else:
                print(WARN(f"  ⚠ {result.get('error', 'empty')}, thử cookie khác"))
        except Exception as e:
            print(WARN(f"  ⚠ {e}, thử cookie khác"))
            continue

    if not fb or not result or "error" in result or not result.get("threads"):
        print(ERR("❌ Không thể lấy danh sách box từ bất kỳ cookie nào"))
        return []

    threads_list = result["threads"]

    table = Table(title=f"📦 DANH SÁCH BOX — {len(threads_list)}",
                  show_header=True, header_style="bold magenta",
                  box=rich_box.ROUNDED)
    table.add_column("STT", style="cyan", width=5, justify="center")
    table.add_column("Tên Box", style="green")
    table.add_column("ID", style="yellow")
    for idx, thread in enumerate(threads_list, 1):
        tn = thread.get("thread_name", "Không có tên") or "Không có tên"
        disp = f"{tn[:45]}{'...' if len(tn) > 45 else ''}"
        table.add_row(str(idx), disp, thread["thread_id"])
    console.print(table)

    raw = input(INFO("❯ Chọn box (1,3,5 / all): ")).strip()
    if raw.lower() == "all":
        selected = list(range(1, len(threads_list) + 1))
    else:
        selected = parse_selection(raw, len(threads_list))
    if not selected:
        print(ERR("❌ Chưa chọn box nào"))
        return []

    thread_ids = [threads_list[i - 1]["thread_id"] for i in selected]
    print(OK(f"✓ Đã chọn {len(thread_ids)} box"))
    return thread_ids


# =============== MAIN ===============
if __name__ == "__main__":
    try:
        banner()
        loading_line(1.2, "Đang khởi động")

        st = threading.Thread(target=status_thread, daemon=True, name="status")
        st.start()

        cookies = input_cookies_from_console()
        if not cookies:
            exit()

        thread_ids = select_threads_interactive(cookies)
        if not thread_ids:
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