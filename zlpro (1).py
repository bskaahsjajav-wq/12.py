#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
#   ZIN THIÊN ĐẠO - ZALO TOOL v7.4 · NEBULA EDITION
#   4 MODES:
#     1. Treo ngôn     - 1 tin = all dòng (box / user)
#     2. Nhây tag      - TAG THẬT (@1 | @1,3,5 | @All)
#     3. Nuke box      - poll + sticker + msg + NAME + DESC
#     4. Tag + Nuke    - mode 3 + tag
#   v7.4:
#     - Tag gộp prompt: 1 | 1,3,5 | all | khong
#     - Mention nhiều người (JSON array)
#     - @All mention thật (uid="", type=1)
# ══════════════════════════════════════════════════════════════

import os, sys, json, time, re, inspect, multiprocessing, warnings
import math, colorsys, shutil, threading
warnings.filterwarnings("ignore")

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from zlapi import ZaloAPI
    from zlapi.models import (
        Message, Mention, ThreadType, MessageStyle, MultiMsgStyle
    )
    from zlapi._exception import ZaloAPIException
except ImportError as e:
    print(f"[!] Thiếu thư viện: {e}\n[!] pip install zlapi rich")
    sys.exit(1)

console = Console()
RESET = "\033[0m"
E = "\033["


# ══════════════════════════════════════════════════════════════
#  ANSI ENGINE — NEBULA
# ══════════════════════════════════════════════════════════════
def rgb(r, g, b):
    return f"{E}38;2;{r};{g};{b}m"


def hsv(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, max(0.0, min(1.0, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def grad(text, h0=0.0, h1=0.15, sat=1.0, val=1.0):
    n = max(len(text) - 1, 1)
    return "".join(
        rgb(*hsv(h0 + (h1 - h0) * (i / n), sat, val)) + c
        for i, c in enumerate(text)
    ) + RESET


def gradw(text, h0=0.0, h1=0.15, sat=0.95, base=0.62, amp=0.38,
          freq=0.45, phase=0.0):
    n = max(len(text) - 1, 1)
    out = []
    for i, c in enumerate(text):
        h = h0 + (h1 - h0) * (i / n)
        v = base + amp * (0.5 + 0.5 * math.sin(i * freq - phase))
        out.append(rgb(*hsv(h, sat, v)) + c)
    return "".join(out) + RESET


def cls():
    sys.stdout.write(E + "2J" + E + "3J" + E + "H")
    sys.stdout.flush()


try:
    _T = shutil.get_terminal_size((80, 24)).columns
    W = max(40, min(_T - 4, 68))
except Exception:
    W = 62


# ══════════════════════════════════════════════════════════════
#  BANNER — ZIN NEBULA
# ══════════════════════════════════════════════════════════════
ZIN_ART = [
    "  ███████╗██╗███╗   ██╗",
    "  ╚══███╔╝██║████╗  ██║",
    "    ███╔╝ ██║██╔██╗ ██║",
    "   ███╔╝  ██║██║╚██╗██║",
    "  ███████╗██║██║ ╚████║",
    "  ╚══════╝╚═╝╚═╝  ╚═══╝",
]


def banner_frame(frame):
    lines = [""]
    for i, l in enumerate(ZIN_ART):
        row = []
        for j, c in enumerate(l):
            h = 0.50 + (j / max(len(l) - 1, 1)) * 0.06
            if (frame + i * 5 + j) % 53 == 0 and c != " ":
                r, g, b = 255, 30, 120
            else:
                base_v = 0.62 + 0.15 * math.sin(j * 0.4 - frame * 0.5 + i * 0.3)
                spot = (frame * 0.7 + i * 2) % (len(l) + 8) - 4
                d = abs(j - spot)
                v = min(1.0, base_v + math.exp(-(d * d) / 6) * 0.30)
                r, g, b = hsv(h, 0.90, v)
            row.append(rgb(r, g, b) + c)
        lines.append("".join(row) + RESET)
    return lines


def animate_banner(total_frames=36, delay=0.045):
    sys.stdout.write(E + "?25l")
    lines = banner_frame(0)
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()
    for f in range(1, total_frames):
        new = banner_frame(f)
        sys.stdout.write(E + f"{len(lines)}A")
        sys.stdout.write("\n".join(new) + "\n")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(E + "?25h")
    sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  DIVIDER
# ══════════════════════════════════════════════════════════════
def hr(hue=0.5, width=None, frame=0):
    w = width or W
    chars = "·⋅∙•●•∙⋅"
    out = []
    for i in range(w):
        t = i / max(w - 1, 1)
        wave = 0.5 + 0.5 * math.sin(i * 0.30 + frame * 0.5)
        idx = int(wave * (len(chars) - 1))
        v = 0.30 + 0.55 * wave
        r, g, b = hsv(hue + t * 0.35, 0.85, v)
        out.append(rgb(r, g, b) + chars[idx])
    return "".join(out) + RESET


# ══════════════════════════════════════════════════════════════
#  STATS COUNTER
# ══════════════════════════════════════════════════════════════
STATS = None


class Stats:
    def __init__(self):
        self.ok = 0
        self.err = 0
        self.warn = 0
        self._render()

    def _line(self):
        ok_c = grad("✓", 0.32, 0.42, 0.95, 1.0)
        er_c = grad("✗", 0.02, 0.06, 0.95, 1.0)
        wr_c = grad("!", 0.08, 0.14, 0.95, 1.0)
        return (f"  {ok_c} {self.ok}    "
                f"{er_c} {self.err}    "
                f"{wr_c} {self.warn}")

    def _render(self):
        sys.stdout.write("\r" + self._line() + E + "K")
        sys.stdout.flush()

    def inc_ok(self, _=None):
        self.ok += 1
        self._render()

    def inc_err(self, reason=""):
        self.err += 1
        sys.stdout.write("\r" + E + "K")
        line = ("  " + grad("✗", 0.02, 0.06, 0.95, 1.0) + "  "
                + gradw(str(reason)[:120], 0.02, 0.06, 0.80, 0.65,
                        0.20, 0.5, 0))
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        self._render()

    def inc_warn(self, reason=""):
        self.warn += 1
        sys.stdout.write("\r" + E + "K")
        line = ("  " + grad("!", 0.08, 0.14, 0.95, 1.0) + "  "
                + gradw(str(reason)[:120], 0.08, 0.14, 0.80, 0.65,
                        0.20, 0.5, 0))
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        self._render()


# ══════════════════════════════════════════════════════════════
#  LOG HELPERS
# ══════════════════════════════════════════════════════════════
def header(text, hue=0.50, frame=0):
    print()
    print("  " + hr(hue, frame=frame))
    pad = max((W - len(text) - 4) // 2, 0)
    print(" " * pad + gradw(text, hue, hue + 0.15, 0.95,
                            0.70, 0.30, 0.4, frame * 0.5))
    print("  " + hr(hue + 0.2, frame=-frame))
    print()


def divider(hue=0.5, frame=0):
    print("  " + hr(hue, frame=frame))


def ok(text=""):
    if STATS is not None:
        STATS.inc_ok()
    else:
        print("  " + grad("✓", 0.32, 0.42, 0.95, 1.0)
              + "  " + gradw(str(text), 0.32, 0.42, 0.80, 0.70, 0.15, 0.5, 0))


def err(text):
    if STATS is not None:
        STATS.inc_err(text)
    else:
        print("  " + grad("✗", 0.02, 0.06, 0.95, 1.0)
              + "  " + gradw(str(text), 0.02, 0.06, 0.85, 0.70, 0.15, 0.5, 0))


def warn(text):
    if STATS is not None:
        STATS.inc_warn(text)
    else:
        print("  " + grad("!", 0.08, 0.14, 0.95, 1.0)
              + "  " + gradw(str(text), 0.08, 0.14, 0.80, 0.65, 0.15, 0.5, 0))


def info(text, hue=0.50):
    print("  " + grad("▸", hue, hue + 0.05, 0.9, 0.95)
          + "  " + gradw(str(text), hue, hue + 0.10, 0.75, 0.60, 0.20, 0.5, 0))


def ask(text, hue=0.50):
    return input("  " + grad("❯ ", hue, hue + 0.08, 0.95, 1.0)
                 + gradw(text, hue, hue + 0.10, 0.75, 0.65, 0.20, 0.5, 0))


def gradient_text(text, colors=None):
    return gradw(text, 0.50, 0.65, 0.9, 0.70, 0.30, 0.4, 0)


def print_color(text, color_type="info"):
    hue_map = {"success": 0.32, "error": 0.02, "warning": 0.10,
               "info": 0.50, "cyan": 0.50, "magenta": 0.85}
    hue = hue_map.get(color_type, 0.50)
    print("  " + gradw(text, hue, hue + 0.10, 0.75, 0.60, 0.20, 0.5, 0))


def print_gradient(text):
    print(grad(text, 0.50, 0.65, 0.9, 1.0))


def print_banner():
    for l in banner_frame(0):
        print(l)


def print_line(char="", length=None, color="cyan"):
    divider(0.5, 0)


def print_header(text):
    header(text, 0.50, 0)


# ══════════════════════════════════════════════════════════════
#  SPINNER
# ══════════════════════════════════════════════════════════════
def spin(text, fn, hue=0.50):
    stop = threading.Event()
    box = {"ok": False, "val": None, "err": None}

    def _run():
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not stop.is_set():
            sys.stdout.write(
                "\r  " + grad(frames[i % len(frames)], hue, hue + 0.05, 0.95, 1.0)
                + "  " + gradw(text, hue, hue + 0.10, 0.75, 0.55, 0.25, 0.5, i * 0.15)
                + E + "K"
            )
            sys.stdout.flush()
            i += 1
            time.sleep(0.06)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        box["val"] = fn()
        box["ok"] = True
    except Exception as e:
        box["err"] = e
    finally:
        stop.set()
        t.join(timeout=0.3)
        sys.stdout.write("\r" + E + "K")
        sys.stdout.flush()

    if box["ok"]:
        print("  " + grad("✓", 0.32, 0.42, 0.95, 1.0)
              + "  " + gradw(text, 0.32, 0.42, 0.75, 0.65, 0.20, 0.5, 0))
        return box["val"]
    else:
        print("  " + grad("✗", 0.02, 0.06, 0.95, 1.0)
              + "  " + gradw(f"{text} — {str(box['err'])[:60]}",
                             0.02, 0.06, 0.85, 0.65, 0.20, 0.5, 0))
        return None


# ══════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════
NUKE_STICKERS = [23339, 23298, 22665]
STICKER_TYPE  = 1
STICKER_CATE  = 1
NUKE_MESSAGE  = (
    " =)))=)))=))) rain nuke vote 367367367 vcb :; :; "
    "/-thanks /-thanks /-bd /-bd  /-bome /-bome "
)

DEFAULT_NAMES = ["ZIN ĐÃ CHIẾM BOX", "VĨNH HẰNG CHÍ TÔN SÁT LŨ ĐÚ", "NHÂY CHẾT CON MẸ MÀY"]
DEFAULT_DESCS = ["BOX NÀY BỊ ZIN CHIẾM ĐỐNG =)))=)))=)))", "VĨNH HẰNG CHÍ TÔN ĐÃ ĐẾN XỬ CHẾT LŨ ĐÚ NGU NGỤC",
                 "GIẾT SẠCH LŨ NGU"]

POLL_MAX_OPTIONS = 4
POLL_MIN_OPTIONS = 2


# ══════════════════════════════════════════════════════════════
#  UTF-16
# ══════════════════════════════════════════════════════════════
def utf16_len(s):
    return len(s.encode("utf-16-le")) // 2 if s else 0


# ══════════════════════════════════════════════════════════════
#  ZALO CLIENT
# ══════════════════════════════════════════════════════════════
def _normalize_cookies(cookie_input):
    if isinstance(cookie_input, dict):
        return cookie_input
    if isinstance(cookie_input, str):
        s = cookie_input.strip()
        if s.startswith("{"):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass
        cookies = {}
        for pair in s.split(";"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies
    raise ValueError("Cookie phải là dict hoặc chuỗi JSON / 'k=v; k=v'")


def create_zalo_client(cookie_input, imei):
    cookies = _normalize_cookies(cookie_input)
    params = list(inspect.signature(ZaloAPI.__init__).parameters.keys())
    base = {}
    if "imei" in params:
        base["imei"] = imei
    for key in ("cookies", "session_cookies", "cookie", "session_cookie"):
        if key in params:
            kwargs = dict(base)
            kwargs[key] = cookies
            try:
                return ZaloAPI(**kwargs)
            except TypeError:
                kwargs[key] = "; ".join(f"{k}={v}" for k, v in cookies.items())
                return ZaloAPI(**kwargs)
    raise RuntimeError(f"Không tìm thấy tham số cookie. Params: {params}")


def get_client_uid(client):
    val = getattr(client, "uid", None)
    if val is not None and not callable(val):
        return str(val)
    for attr in ("_uid", "user_id", "userId"):
        val = getattr(client, attr, None)
        if val is None:
            continue
        if callable(val):
            try:
                val = val()
            except Exception:
                continue
        if val and not callable(val):
            return str(val)
    state = getattr(client, "_state", None) or getattr(client, "state", None)
    if state:
        for attr in ("uid", "user_id", "userId"):
            val = getattr(state, attr, None)
            if val and not callable(val):
                return str(val)
    try:
        info = client.fetchAccountInfo()
        if isinstance(info, dict):
            uid = info.get("userId") or info.get("uid")
            if uid:
                return str(uid)
        else:
            uid = getattr(info, "userId", None)
            if uid:
                return str(uid)
    except Exception:
        pass
    return None


def get_zalo_user_info(client):
    try:
        uid = get_client_uid(client)
        name = "Unknown"
        if uid:
            try:
                prof = client.fetchUserInfo(uid)
                profiles = getattr(prof, "changed_profiles", None) or {}
                if isinstance(prof, dict):
                    profiles = prof.get("changed_profiles") or profiles
                p = profiles.get(str(uid), {})
                if isinstance(p, dict):
                    name = p.get("zaloName") or p.get("displayName") or "Unknown"
            except Exception:
                pass
        return {"status": "success", "uid": uid, "name": name}
    except Exception as e:
        return {"status": "failed", "msg": str(e)}


def _get_name_from_profiles(prof, uid):
    profiles = getattr(prof, "changed_profiles", None) or {}
    if isinstance(prof, dict):
        profiles = prof.get("changed_profiles") or profiles
    p = profiles.get(str(uid), {})
    if isinstance(p, dict):
        return (p.get("zaloName") or p.get("displayName")
                or p.get("name") or f"User {uid}")
    return f"User {uid}"


# ══════════════════════════════════════════════════════════════
#  EXTRACT
# ══════════════════════════════════════════════════════════════
def _extract_group_info(raw, gid):
    if not raw:
        return None
    gid = str(gid)
    if not isinstance(raw, dict):
        if hasattr(raw, "__dict__"):
            raw = vars(raw)
        else:
            return None
    for key in ("gridInfoMap", "grid_info_map", "gridInfoMapData"):
        grid = raw.get(key)
        if isinstance(grid, dict):
            info = grid.get(gid)
            if info:
                if hasattr(info, "__dict__") and not isinstance(info, dict):
                    info = vars(info)
                return info
    if gid in raw:
        info = raw[gid]
        if hasattr(info, "__dict__") and not isinstance(info, dict):
            info = vars(info)
        return info
    if len(raw) == 1:
        v = list(raw.values())[0]
        if isinstance(v, dict) and ("name" in v or "groupId" in v or "memberIds" in v):
            return v
    return None


def _extract_name(info):
    if not info:
        return None
    if not isinstance(info, dict):
        if hasattr(info, "__dict__"):
            info = vars(info)
        else:
            return None
    for k in ("name", "groupName", "group_name", "gridName"):
        v = info.get(k)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, dict):
            for kk in ("name", "groupName"):
                if kk in v and v[kk]:
                    return str(v[kk])
    return None


def _extract_member_uids(info):
    if not info:
        return []
    if not isinstance(info, dict):
        if hasattr(info, "__dict__"):
            info = vars(info)
        else:
            return []
    uids = set()
    mem_ver = info.get("memVerList") or info.get("mem_ver_list")
    if mem_ver and isinstance(mem_ver, (list, tuple, dict)):
        items = mem_ver.values() if isinstance(mem_ver, dict) else mem_ver
        for item in items:
            if not isinstance(item, str):
                item = str(item)
            uid = item.split("_")[0].strip()
            if uid.isdigit() and 12 <= len(uid) <= 20:
                uids.add(uid)
    for key in ["currentMems", "current_mems", "updateMems", "update_mems",
                "memberIds", "member_ids", "members", "memberList"]:
        val = info.get(key)
        if not val:
            continue
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, (str, int)) and str(v).isdigit():
                    s = str(v)
                    if 12 <= len(s) <= 20:
                        uids.add(s)
                elif isinstance(v, dict):
                    for uk in ("id", "uid", "userId", "user_id"):
                        if uk in v and v[uk]:
                            uids.add(str(v[uk]))
                            break
                if isinstance(k, str) and k.isdigit() and 12 <= len(k) <= 20:
                    uids.add(k)
        elif isinstance(val, (list, tuple)):
            for item in val:
                if isinstance(item, (str, int)):
                    s = str(item)
                    s = s.split("_")[0] if "_" in s else s
                    if s.isdigit() and 12 <= len(s) <= 20:
                        uids.add(s)
                elif isinstance(item, dict):
                    for uk in ("id", "uid", "userId", "user_id"):
                        if uk in item and item[uk]:
                            uids.add(str(item[uk]))
                            break
        elif isinstance(val, str):
            for p in val.replace(",", " ").split():
                p = p.split("_")[0] if "_" in p else p
                if p.isdigit() and 12 <= len(p) <= 20:
                    uids.add(p)
    return list(uids)


# ══════════════════════════════════════════════════════════════
#  FETCHERS
# ══════════════════════════════════════════════════════════════
def fetch_groups_with_name(client):
    def _inner():
        try:
            return client.fetchAllGroups()
        except Exception:
            return None
    raw = spin("Đang tải danh sách nhóm", _inner, 0.50)
    if not raw:
        return []
    gids = []
    if isinstance(raw, dict):
        for key in ("gridVerMap", "gridInfoMap", "grid_info_map"):
            sub = raw.get(key)
            if isinstance(sub, dict):
                gids = [str(g) for g in sub.keys()]
                break
        if not gids:
            meta = {"version", "gridVerMap", "gridInfoMap", "grid_info_map"}
            gids = [str(k) for k in raw.keys() if k not in meta and str(k).isdigit()]
    elif isinstance(raw, list):
        for g in raw:
            if isinstance(g, dict):
                gid = g.get("groupId") or g.get("group_id") or g.get("id")
            else:
                gid = (getattr(g, "groupId", None)
                       or getattr(g, "group_id", None)
                       or getattr(g, "id", None))
            if gid:
                gids.append(str(gid))
    if not gids:
        return []
    out = []
    for gid in gids:
        name = None
        try:
            r = client.fetchGroupInfo(gid)
            info = _extract_group_info(r, gid)
            name = _extract_name(info)
        except Exception:
            pass
        out.append({"gid": gid, "name": name or f"Nhóm {gid}"})
    return out


def get_group_members(client, gid):
    raw = spin(f"Đang lấy members box ...{gid[-6:]}",
               lambda: client.fetchGroupInfo(gid), 0.55)
    info = _extract_group_info(raw, gid)
    if not info:
        return []
    uids = _extract_member_uids(info)
    if not uids:
        return []
    out = []
    for uid in uids:
        try:
            prof = client.fetchUserInfo(uid)
            name = _get_name_from_profiles(prof, uid)
        except Exception:
            name = f"User {uid}"
        out.append({"uid": uid, "name": name})
    return out


def fetch_friends_with_name(client):
    def _inner():
        for func_name in ("fetchAllFriends", "getAllFriends",
                          "fetchFriendList", "getFriendList"):
            func = getattr(client, func_name, None)
            if not func:
                continue
            try:
                r = func()
                if r:
                    return r
            except Exception:
                continue
        return None
    raw = spin("Đang tải danh sách bạn bè", _inner, 0.50)
    if not raw:
        return []
    uids = []
    if isinstance(raw, dict):
        for key in ("friends", "data", "userIds", "user_ids"):
            sub = raw.get(key)
            if isinstance(sub, list):
                for x in sub:
                    if isinstance(x, str):
                        uids.append(x)
                    elif isinstance(x, dict):
                        uid = x.get("userId") or x.get("uid") or x.get("id")
                        if uid:
                            uids.append(str(uid))
                break
            elif isinstance(sub, dict):
                uids.extend(str(k) for k in sub.keys())
                break
        else:
            for k, v in raw.items():
                if isinstance(k, str) and k.isdigit() and 10 <= len(k) <= 20:
                    uids.append(k)
                elif isinstance(v, dict):
                    uid = v.get("userId") or v.get("uid") or v.get("id")
                    if uid:
                        uids.append(str(uid))
    elif isinstance(raw, list):
        for x in raw:
            if isinstance(x, str):
                uids.append(x)
            elif isinstance(x, dict):
                uid = x.get("userId") or x.get("uid") or x.get("id")
                if uid:
                    uids.append(str(uid))
    seen, clean = set(), []
    for u in uids:
        if not u or not str(u).isdigit():
            continue
        if len(str(u)) < 10 or len(str(u)) > 20:
            continue
        if u in seen:
            continue
        seen.add(u)
        clean.append(str(u))
    if not clean:
        return []
    out = []
    for uid in clean:
        name = f"User {uid}"
        try:
            prof = client.fetchUserInfo(uid)
            name = _get_name_from_profiles(prof, uid)
        except Exception:
            pass
        out.append({"uid": uid, "name": name})
    return out


# ══════════════════════════════════════════════════════════════
#  FAKE SOẠN NGẦM
# ══════════════════════════════════════════════════════════════
def typing_then_sleep(client, thread_id, thread_type, seconds):
    if seconds <= 0:
        return
    try:
        client.sendTyping(thread_id, thread_type, typing=True)
    except Exception:
        pass
    end = time.time() + seconds
    while True:
        remain = end - time.time()
        if remain <= 0:
            break
        time.sleep(min(3, remain))
        try:
            client.sendTyping(thread_id, thread_type, typing=True)
        except Exception:
            pass
    try:
        client.sendTyping(thread_id, thread_type, typing=False)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
#  TAG / MENTION — JSON STRING, hỗ trợ nhiều người + @All
# ══════════════════════════════════════════════════════════════
def build_msg_with_mentions(content, mentions):
    """
    mentions: list [{"uid": str, "name": str, "type": int}]
    - type=0 → tag người bình thường
    - type=1 → tag @All (uid rỗng)
    Build Message với JSON mention array.
    """
    if not mentions:
        return Message(text=content)

    # Strip @Tên ở đầu content (tránh double)
    content_clean = content.strip()
    changed = True
    while changed:
        changed = False
        for m in mentions:
            prefix = f"@{m['name']}"
            if content_clean.startswith(prefix):
                content_clean = content_clean[len(prefix):].lstrip()
                changed = True
    content_clean = re.sub(r"^@\S+\s+", "", content_clean).strip()

    if content_clean:
        full = content_clean + " "
        cursor = utf16_len(full)
    else:
        full = ""
        cursor = 0

    entries = []
    for i, m in enumerate(mentions):
        tag_str = f"@{m['name']}"
        length = utf16_len(tag_str)
        entries.append({
            "pos": cursor,
            "len": length,
            "uid": str(m.get("uid", "")),
            "type": int(m.get("type", 0)),
        })
        full += tag_str
        cursor += length
        if i < len(mentions) - 1:
            full += " "
            cursor += 1

    return Message(text=full, mention=json.dumps(entries))


def build_msg_with_tag(content, tag):
    """Compat cũ — wrap 1 tag thành list."""
    if not tag:
        return Message(text=content)
    return build_msg_with_mentions(content, [{
        "uid": tag.get("uid", ""),
        "name": tag["name"],
        "type": tag.get("type", 0),
    }])


def _make_all_mention():
    """@All mention thật — uid rỗng, type=1."""
    return [{"uid": "-1", "name": "All", "type": 1}]


def _pick_tag_config(all_members):
    """
    Gộp prompt vào bảng member:
      - 1 số       → tag 1 người
      - 1,3,5      → tag nhiều người
      - all        → @All (mention thật)
      - khong / k  → bỏ tag
    """
    if not all_members:
        info("Không có member — tag @All?", 0.50)
        c = ask("Tag @All? (y/n): ", 0.50).strip().lower()
        if c in ("y", "yes", "c", "co", "có"):
            return "all", _make_all_mention()
        return None, None

    table = Table(title="CHỌN NGƯỜI ĐỂ TAG", box=box.ROUNDED)
    table.add_column("STT", style="cyan", width=5, justify="center")
    table.add_column("Tên", style="green")
    table.add_column("UID", style="yellow")
    for idx, m in enumerate(all_members, 1):
        nm = m.get("name", "?")
        disp = f"{nm[:45]}{'...' if len(nm) > 45 else ''}"
        table.add_row(str(idx), disp, str(m["uid"]))
    console.print(table)
    divider(0.5)

    info("STT | 1,3,5 (nhiều người) | all (@All) | khong (bỏ tag)", 0.45)

    while True:
        raw = ask("Chọn: ", 0.50).strip().lower()
        if raw in ("khong", "k", "skip", ""):
            return None, None
        if raw == "all":
            return "all", _make_all_mention()

        picks = []
        for p in raw.replace(",", " ").split():
            if p.isdigit():
                k = int(p)
                if 1 <= k <= len(all_members):
                    picks.append(k)

        if not picks:
            err("Sai! Nhập lại (VD: 1 hoặc 1,3,5 hoặc all).")
            continue

        mlist = [{
            "uid": all_members[k - 1]["uid"],
            "name": all_members[k - 1]["name"],
            "type": 0,
        } for k in picks]
        mode = "single" if len(mlist) == 1 else "multi"
        return mode, mlist


# ══════════════════════════════════════════════════════════════
#  SEND HELPERS
# ══════════════════════════════════════════════════════════════
def send_sticker(client, sticker_id, thread_id, thread_type, delay=0):
    if delay > 0:
        time.sleep(delay)
    fn = getattr(client, "sendSticker", None)
    if fn is None:
        return "noapi"
    try:
        fn(STICKER_TYPE, sticker_id, STICKER_CATE, thread_id, thread_type)
        return "success"
    except Exception as e:
        return f"error:{e}"


def create_poll(client, question, options, thread_id, thread_type, delay=0,
                fake_typing=True):
    if fake_typing and delay > 0:
        typing_then_sleep(client, thread_id, thread_type, delay)
    elif delay > 0:
        time.sleep(delay)
    fn = getattr(client, "createPoll", None)
    if fn is None:
        return "noapi"
    try:
        fn(question, options, thread_id)
        return "success"
    except Exception as e:
        return f"error:{e}"


def change_group_name(client, group_id, new_name, delay=0):
    if delay > 0:
        time.sleep(delay)
    fn = getattr(client, "changeGroupName", None)
    if fn is None:
        return "noapi"
    try:
        fn(new_name, group_id)
        return "success"
    except Exception as e:
        return f"error:{e}"


def change_group_desc(client, group_id, new_desc, delay=0, group_name=None):
    if delay > 0:
        time.sleep(delay)
    ep = "https://tt-group-wpa.chat.zalo.me/api/group/updateinfo"
    params = {"zpw_ver": 647, "zpw_type": 30}
    cur_name = group_name or ""
    if not cur_name:
        try:
            raw = client.fetchGroupInfo(group_id)
            info = _extract_group_info(raw, group_id)
            cur_name = _extract_name(info) or ""
        except Exception:
            pass
    imei = getattr(client, "_imei", "")
    for v in (
        {"gname": cur_name, "gdesc": new_desc, "grid": str(group_id),
         "imei": imei},
        {"gname": cur_name, "gdesc": new_desc, "grid": str(group_id)},
        {"gdesc": new_desc, "grid": str(group_id)},
    ):
        try:
            payload = {"params": client._encode(v)}
            r = client._post(ep, params=params, data=payload)
            data = r.json()
            if data.get("error_code") == 0:
                return "success"
        except Exception:
            continue
    return "error:desc"


def handle_result(res, label):
    if res == "success":
        ok()
    elif res == "noapi":
        warn(f"{label}: thiếu API")
    else:
        err(f"{label}: {res}")


# ══════════════════════════════════════════════════════════════
#  INPUT HELPERS
# ══════════════════════════════════════════════════════════════
def input_message_file(prompt="File .txt nội dung: "):
    fp = ask(prompt, 0.50).strip()
    if not fp:
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f if l.strip()]
        if not lines:
            err("File trống")
            return None
        ok(f"{len(lines)} dòng")
        return lines
    except Exception as e:
        err(f"Đọc file: {e}")
        return None


def input_delay_float(prompt, default=1.0, min_delay=0.1):
    try:
        s = ask(prompt, 0.50).strip()
        if not s:
            return default
        d = float(s)
        return max(min_delay, d)
    except ValueError:
        warn(f"Sai, dùng mặc định {default}")
        return default


def input_delay_mode():
    info("CHỌN KIỂU DELAY", 0.50)
    info("1. Delay chung  (1 delay cho tất cả)", 0.45)
    info("2. Delay riêng  (delay từng thao tác)", 0.45)
    while True:
        c = ask("Chọn 1/2: ", 0.50).strip()
        if c == "1":
            return "shared"
        if c == "2":
            return "separate"
        err("Chỉ 1 hoặc 2!")


def parse_question(line):
    q = line.strip()
    if not q:
        return None, "rỗng"
    return q, None


def build_options_groups(lines):
    groups, buffer, skipped = [], [], []
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        buffer.append(line)
        if len(buffer) == POLL_MAX_OPTIONS:
            groups.append(buffer)
            buffer = []
    if buffer:
        skipped.append(("cuối file", f"còn dư {len(buffer)} dòng, không đủ 4"))
    return groups, skipped


def select_from_list(items, id_key, title, prompt, single=False):
    if not items:
        return [], {}
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("STT", style="cyan", width=5, justify="center")
    table.add_column("Tên", style="green")
    table.add_column("ID", style="yellow")
    for idx, item in enumerate(items, 1):
        nm = item.get("name", "?")
        disp = f"{nm[:45]}{'...' if len(nm) > 45 else ''}"
        table.add_row(str(idx), disp, str(item[id_key]))
    console.print(table)
    divider(0.5)

    sel = []
    while not sel:
        raw = ask(prompt, 0.50).strip()
        if not single and raw.lower() == "all":
            sel = list(range(1, len(items) + 1))
            break
        for p in raw.replace(",", " ").split():
            if p.isdigit():
                k = int(p)
                if 1 <= k <= len(items):
                    sel.append(k)
                if single and sel:
                    break
        if not sel:
            err("Sai! Nhập lại.")

    selected = [items[k - 1] for k in sel]
    infos = {str(s[id_key]): s.get("name", "") for s in selected}
    return selected, infos


# ══════════════════════════════════════════════════════════════
#  LOAD POLL + NAMES + DESCS
# ══════════════════════════════════════════════════════════════
def _load_poll_names_descs():
    info("File TIÊU ĐỀ poll (mỗi dòng 1 tiêu đề):", 0.50)
    q_raw = input_message_file("File tiêu đề: ")
    if not q_raw:
        return None
    questions, skipped_q = [], 0
    for i, line in enumerate(q_raw, 1):
        q, reason = parse_question(line)
        if q:
            questions.append(q)
        else:
            skipped_q += 1
            warn(f"Tiêu đề dòng {i}: bỏ — {reason}")
    if skipped_q:
        warn(f"Bỏ {skipped_q} tiêu đề")
    if not questions:
        err("Không có tiêu đề hợp lệ!")
        return None
    ok(f"{len(questions)} tiêu đề OK")

    info("File PHƯƠNG ÁN (mỗi dòng 1 đáp án, 4 dòng = 1 nhóm):", 0.50)
    o_raw = input_message_file("File phương án: ")
    if not o_raw:
        return None
    options_list, skipped_o = build_options_groups(o_raw)
    for idx, reason in skipped_o:
        warn(f"Dòng {idx}: bỏ — {reason}")
    if not options_list:
        err("Không có nhóm phương án hợp lệ!")
        return None
    ok(f"{len(options_list)} nhóm phương án OK")

    polls = []
    n = max(len(questions), len(options_list))
    for i in range(n):
        polls.append((
            questions[i % len(questions)],
            options_list[i % len(options_list)]
        ))
    ok(f"Tổng {len(polls)} poll sẽ chạy")

    info("File TÊN BOX (Enter = dùng tên mặc định ZIN):", 0.50)
    names_input = ask("File tên: ", 0.50).strip()
    if names_input:
        try:
            with open(names_input, "r", encoding="utf-8") as f:
                names = [l.strip() for l in f if l.strip()]
        except Exception as e:
            err(f"{e}")
            return None
    else:
        names = list(DEFAULT_NAMES)
    ok(f"{len(names)} tên box")

    info("File MÔ TẢ BOX (Enter = dùng mô tả mặc định ZIN):", 0.50)
    descs_input = ask("File mô tả: ", 0.50).strip()
    if descs_input:
        try:
            with open(descs_input, "r", encoding="utf-8") as f:
                descs = [l.strip() for l in f if l.strip()]
        except Exception as e:
            err(f"{e}")
            return None
    else:
        descs = list(DEFAULT_DESCS)
    ok(f"{len(descs)} mô tả box")

    return {
        "polls": polls,
        "names": names,
        "descs": descs,
    }


# ══════════════════════════════════════════════════════════════
#  MODE 1 — TREO NGÔN
# ══════════════════════════════════════════════════════════════
def config_treo_ngon(client, info_d):
    info("CHỌN ĐỐI TƯỢNG:", 0.50)
    info("1. Box", 0.45)
    info("2. User (bạn bè)", 0.45)
    choice = ""
    while choice not in ("1", "2"):
        choice = ask("Chọn 1/2: ", 0.50).strip()
        if choice not in ("1", "2"):
            err("Chỉ 1/2!")

    if choice == "1":
        targets = fetch_groups_with_name(client)
        id_key = "gid"
        title = "CHỌN BOX"
    else:
        targets = fetch_friends_with_name(client)
        id_key = "uid"
        title = "CHỌN USER"

    if not targets:
        err("Không có đối tượng!")
        return None

    selected, infos = select_from_list(targets, id_key, title,
                                       "Chọn (1,3 / all): ")
    if not selected:
        return None

    msg_lines = input_message_file("File .txt (sẽ gộp thành 1 tin): ")
    if not msg_lines:
        return None
    content = "\n".join(msg_lines)
    delay = input_delay_float("Delay (giây, VD 1.5): ", 2.0)

    return {
        "type": choice,
        "selected_ids": [str(s[id_key]) for s in selected],
        "selected_infos": infos,
        "content": content,
        "delay": delay,
    }


def worker_treo_ngon(cookie_str, imei, account_name, uid, cfg):
    global STATS
    try:
        client = create_zalo_client(cookie_str, imei)
        info_d = get_zalo_user_info(client)
        if info_d["status"] != "success":
            err(f"{account_name}: auth failed")
            return
        real_name = info_d.get("name", account_name)
        print("  " + grad("▶", 0.50, 0.55, 0.95, 1.0)
              + "  " + gradw(real_name, 0.50, 0.60, 0.80, 0.70, 0.20, 0.5, 0))

        STATS = Stats()
        thread_type = ThreadType.GROUP if cfg["type"] == "1" else ThreadType.USER

        while True:
            for tid in cfg["selected_ids"]:
                try:
                    typing_then_sleep(client, tid, thread_type, cfg["delay"])
                    msg = Message(text=cfg["content"])
                    client.send(msg, thread_id=tid, thread_type=thread_type)
                    ok()
                except Exception as e:
                    err(f"{cfg['selected_infos'].get(tid, tid)}: {str(e)[:80]}")
    except Exception as e:
        err(f"{account_name}: {str(e)[:80]}")
    finally:
        if STATS is not None:
            sys.stdout.write("\n")
            sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  MODE 2 — NHÂY TAG
# ══════════════════════════════════════════════════════════════
def config_nhay_tag(client, info_d):
    info("CHỌN CÁCH LẤY:", 0.50)
    info("1. Box → Member", 0.45)
    info("2. DM User", 0.45)
    choice = ""
    while choice not in ("1", "2"):
        choice = ask("Chọn 1/2: ", 0.50).strip()
        if choice not in ("1", "2"):
            err("Chỉ 1/2!")

    if choice == "1":
        groups = fetch_groups_with_name(client)
        if not groups:
            return None
        selected_boxes, box_infos = select_from_list(
            groups, "gid", "CHỌN BOX", "Chọn box (1,3 / all): ")
        if not selected_boxes:
            return None
        selected_ids = [str(b["gid"]) for b in selected_boxes]

        info("Lấy member...", 0.50)
        all_members = []
        for tid in selected_ids:
            try:
                ms = get_group_members(client, tid)
                all_members.extend(ms)
                ok(f"Box {tid}: {len(ms)} mem")
            except Exception as e:
                warn(f"{tid}: {e}")
        seen, unique = set(), []
        for m in all_members:
            if m["uid"] not in seen:
                seen.add(m["uid"])
                unique.append(m)
        all_members = unique

        tag_mode, tag_mentions = _pick_tag_config(all_members)
        if tag_mode is None and tag_mentions is None:
            # User chọn 'khong' — vẫn cho tiếp tục (không tag)
            tag_mode, tag_mentions = None, []

        msg_lines = input_message_file("File .txt nội dung tag: ")
        if not msg_lines:
            return None
        delay = input_delay_float("Delay (giây): ", 2.0)

        return {
            "sub": "box",
            "selected_ids": selected_ids,
            "thread_infos": box_infos,
            "tag_mode": tag_mode,
            "tag_mentions": tag_mentions,
            "msg_lines": msg_lines,
            "delay": delay,
        }
    else:
        friends = fetch_friends_with_name(client)
        if not friends:
            return None
        selected, user_infos = select_from_list(
            friends, "uid", "CHỌN USER", "Chọn (1,3 / all): ")
        if not selected:
            return None
        msg_lines = input_message_file("File .txt nội dung: ")
        if not msg_lines:
            return None
        delay = input_delay_float("Delay (giây): ", 2.0)
        return {
            "sub": "dm",
            "selected_ids": [str(u["uid"]) for u in selected],
            "user_infos": user_infos,
            "msg_lines": msg_lines,
            "delay": delay,
        }


def worker_nhay_tag(cookie_str, imei, account_name, uid, cfg):
    global STATS
    try:
        client = create_zalo_client(cookie_str, imei)
        info_d = get_zalo_user_info(client)
        if info_d["status"] != "success":
            err(f"auth {account_name}")
            return
        real_name = info_d.get("name", account_name)
        print("  " + grad("▶", 0.50, 0.55, 0.95, 1.0)
              + "  " + gradw(real_name, 0.50, 0.60, 0.80, 0.70, 0.20, 0.5, 0))

        STATS = Stats()
        idx = 0
        while True:
            for tid in cfg["selected_ids"]:
                raw = cfg["msg_lines"][idx % len(cfg["msg_lines"])]
                idx += 1
                if cfg["sub"] == "box":
                    try:
                        typing_then_sleep(client, tid, ThreadType.GROUP,
                                          cfg["delay"])
                        mlist = cfg.get("tag_mentions", []) or []
                        if mlist:
                            msg = build_msg_with_mentions(raw, mlist)
                            client.sendMentionMessage(msg, tid)
                        else:
                            msg = Message(text=raw)
                            client.send(msg, thread_id=tid,
                                        thread_type=ThreadType.GROUP)
                        ok()
                    except Exception as e:
                        err(f"{cfg['thread_infos'].get(tid, tid)}: {str(e)[:80]}")
                else:
                    try:
                        typing_then_sleep(client, tid, ThreadType.USER,
                                          cfg["delay"])
                        msg = Message(text=raw)
                        client.send(msg, thread_id=tid,
                                    thread_type=ThreadType.USER)
                        ok()
                    except Exception as e:
                        err(f"{cfg['user_infos'].get(tid, tid)}: {str(e)[:80]}")
    except Exception as e:
        err(f"{account_name}: {str(e)[:80]}")
    finally:
        if STATS is not None:
            sys.stdout.write("\n")
            sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  MODE 3 & 4 — NUKE
# ══════════════════════════════════════════════════════════════
def _config_nuke_common(client, need_tag=False):
    groups = fetch_groups_with_name(client)
    if not groups:
        err("Không có nhóm!")
        return None

    selected, infos = select_from_list(
        groups, "gid", "CHỌN BOX (NUKE)", "Chọn box (1,3 / all): ")
    if not selected:
        return None
    selected_ids = [str(g["gid"]) for g in selected]

    d_mode = input_delay_mode()
    if d_mode == "shared":
        d = input_delay_float("Delay chung (giây): ", 0.5)
        delays = {"poll": d, "sticker": d, "message": d,
                  "name": d, "desc": d, "tag": d}
    else:
        delays = {
            "poll":    input_delay_float("Delay poll: ", 0.5),
            "sticker": input_delay_float("Delay sticker: ", 0.3),
            "message": input_delay_float("Delay nuke msg: ", 0.5),
            "name":    input_delay_float("Delay đổi tên box: ", 0.5),
            "desc":    input_delay_float("Delay đổi mô tả box: ", 0.3),
            "tag":     input_delay_float("Delay tag: ", 0.5) if need_tag else 0.5,
        }

    cfg = _load_poll_names_descs()
    if cfg is None:
        return None

    cfg["selected_ids"] = selected_ids
    cfg["selected_infos"] = infos
    cfg["delays"] = delays

    if need_tag:
        info("Lấy member để tag...", 0.50)
        all_members = []
        for tid in selected_ids:
            try:
                ms = get_group_members(client, tid)
                all_members.extend(ms)
                ok(f"Box {tid}: {len(ms)} mem")
            except Exception as e:
                warn(f"{tid}: {e}")
        seen, unique = set(), []
        for m in all_members:
            if m["uid"] not in seen:
                seen.add(m["uid"])
                unique.append(m)
        all_members = unique

        tag_mode, tag_mentions = _pick_tag_config(all_members)
        if tag_mode is None and not tag_mentions:
            tag_mentions = []
        cfg["tag_mode"] = tag_mode
        cfg["tag_mentions"] = tag_mentions

        tag_lines = input_message_file("File .txt cho TAG: ")
        if not tag_lines:
            return None
        cfg["tag_lines"] = tag_lines

    return cfg


def config_nuke(client, info_d):
    return _config_nuke_common(client, need_tag=False)


def config_nuke_tag(client, info_d):
    return _config_nuke_common(client, need_tag=True)


def worker_nuke(cookie_str, imei, account_name, uid, cfg, do_tag=False):
    global STATS
    try:
        client = create_zalo_client(cookie_str, imei)
        info_d = get_zalo_user_info(client)
        if info_d["status"] != "success":
            err(f"auth {account_name}")
            return
        real_name = info_d.get("name", account_name)
        print("  " + grad("▶", 0.50, 0.55, 0.95, 1.0)
              + "  " + gradw(real_name, 0.50, 0.60, 0.80, 0.70, 0.20, 0.5, 0))

        STATS = Stats()

        poll_idx = 0
        name_idx = 0
        desc_idx = 0
        tag_idx = 0
        tag_lines = cfg.get("tag_lines", [])
        tag_mentions = cfg.get("tag_mentions", []) or []

        while True:
            for tid in cfg["selected_ids"]:
                tname = cfg["selected_infos"].get(tid, tid)

                # 1. POLL
                q, opts = cfg["polls"][poll_idx % len(cfg["polls"])]
                poll_idx += 1
                try:
                    res = create_poll(client, q, opts, tid,
                                      ThreadType.GROUP,
                                      cfg["delays"]["poll"], True)
                    handle_result(res, f"{tname} · poll")
                except Exception as e:
                    err(f"{tname} · poll: {str(e)[:70]}")

                # 2. STICKER
                for sid in NUKE_STICKERS:
                    try:
                        res = send_sticker(client, sid, tid,
                                           ThreadType.GROUP,
                                           cfg["delays"]["sticker"])
                        handle_result(res, f"{tname} · sticker {sid}")
                    except Exception as e:
                        err(f"{tname} · sticker {sid}: {str(e)[:70]}")

                # 3. NUKE MSG
                try:
                    typing_then_sleep(client, tid, ThreadType.GROUP,
                                      cfg["delays"]["message"])
                    msg = Message(text=NUKE_MESSAGE)
                    client.send(msg, thread_id=tid,
                                thread_type=ThreadType.GROUP)
                    ok()
                except Exception as e:
                    err(f"{tname} · nuke: {str(e)[:70]}")

                # 4. NAME
                new_name = cfg["names"][name_idx % len(cfg["names"])]
                name_idx += 1
                try:
                    res = change_group_name(client, tid, new_name,
                                            cfg["delays"]["name"])
                    handle_result(res, f"{tname} · name")
                except Exception as e:
                    err(f"{tname} · name: {str(e)[:70]}")

                # 5. DESC
                new_desc = cfg["descs"][desc_idx % len(cfg["descs"])]
                desc_idx += 1
                try:
                    res = change_group_desc(client, tid, new_desc,
                                            cfg["delays"]["desc"],
                                            group_name=new_name)
                    handle_result(res, f"{tname} · desc")
                except Exception as e:
                    err(f"{tname} · desc: {str(e)[:70]}")

                # 6. TAG (mode 4)
                if do_tag and tag_lines:
                    raw = tag_lines[tag_idx % len(tag_lines)]
                    tag_idx += 1
                    try:
                        typing_then_sleep(
                            client, tid, ThreadType.GROUP,
                            cfg["delays"].get("tag", cfg["delays"]["message"])
                        )
                        if tag_mentions:
                            msg = build_msg_with_mentions(raw, tag_mentions)
                            client.sendMentionMessage(msg, tid)
                        else:
                            msg = Message(text=raw)
                            client.send(msg, thread_id=tid,
                                        thread_type=ThreadType.GROUP)
                        ok()
                    except Exception as e:
                        err(f"{tname} · tag: {str(e)[:70]}")
    except Exception as e:
        err(f"{account_name}: {str(e)[:80]}")
    finally:
        if STATS is not None:
            sys.stdout.write("\n")
            sys.stdout.flush()


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    cls()
    print()
    animate_banner(40, 0.04)
    header("Z I N   T H I Ê N   Đ Ạ O", 0.50, frame=0)
    info("Siêu Cấp Cường Giả Zalo Tộc", 0.50)
    divider(0.55)
    print()

    try:
        n = int(ask("Số lượng acc: ", 0.50))
        if n < 1:
            err("Phải > 0")
            return
    except ValueError:
        err("Nhập số nguyên")
        return

    processes = []

    for i in range(n):
        header(f"T À I   K H O Ả N   {i + 1}", 0.55, frame=i * 2)

        cookie_raw = ask("Cookie Zalo: ", 0.50).strip()
        if not cookie_raw:
            err("Cookie rỗng")
            continue
        imei = ask("IMEI: ", 0.50).strip()
        if not imei:
            err("IMEI rỗng")
            continue

        info("Kiểm tra kết nối...", 0.50)
        try:
            client = create_zalo_client(cookie_raw, imei)
            info_d = get_zalo_user_info(client)
            if info_d["status"] != "success" or not info_d.get("uid"):
                err(f"{info_d.get('msg', 'no uid')}")
                continue
            ok(f"{info_d['name']} (UID: {info_d['uid']})")
        except Exception as e:
            err(f"Lỗi kết nối: {e}")
            continue

        divider(0.55)
        info("CHỌN MODE:", 0.50)
        info("1. Treo ngôn", 0.45)
        info("2. Nhây tag", 0.45)
        info("3. Nuke box", 0.45)
        info("4. Nhây tag + Nuke PoE", 0.45)
        divider(0.55)

        mode = ""
        while mode not in ("1", "2", "3", "4"):
            mode = ask("Chọn mode: ", 0.50).strip()
            if mode not in ("1", "2", "3", "4"):
                err("Chỉ 1-4!")

        target = None
        args_extra = ()

        if mode == "1":
            cfg = config_treo_ngon(client, info_d)
            if cfg:
                target = worker_treo_ngon
                args_extra = (cfg,)
        elif mode == "2":
            cfg = config_nhay_tag(client, info_d)
            if cfg:
                target = worker_nhay_tag
                args_extra = (cfg,)
        elif mode == "3":
            cfg = config_nuke(client, info_d)
            if cfg:
                target = worker_nuke
                args_extra = (cfg, False)
        else:
            cfg = config_nuke_tag(client, info_d)
            if cfg:
                target = worker_nuke
                args_extra = (cfg, True)

        if target is None:
            continue

        p = multiprocessing.Process(
            target=target,
            args=(cookie_raw, imei, info_d["name"], info_d["uid"]) + args_extra
        )
        processes.append(p)
        p.start()
        time.sleep(2)

    if not processes:
        err("Không có process nào chạy")
        return

    header("Đ A N G   C H Ạ Y", 0.32, frame=0)
    ok(f"{len(processes)} acc đang chạy")
    warn("Ctrl+C để dừng")
    divider(0.32)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        err("Đang dừng...")
        for p in processes:
            p.terminate()
        time.sleep(2)
        print()
        ok("Đã dừng")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        err("\nĐã dừng")
    except Exception as e:
        err(f"\nLỗi: {e}")
        import traceback
        traceback.print_exc()