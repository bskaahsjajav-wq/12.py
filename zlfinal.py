# ══════════════════════════════════════════════════════════════
#   ZIN THIÊN ĐẠO - TOOL ZALO
#   Mode 1: Box  |  Mode 2: IB riêng
#   Tag: CHỈ TAG ĐƠN
#   Fake soạn ngầm + delay đúng số nhập, không random
# ══════════════════════════════════════════════════════════════

import os
import sys
import json
import time
import inspect
import multiprocessing
import warnings

warnings.filterwarnings("ignore")

try:
    import pyfiglet
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from zlapi import ZaloAPI
    from zlapi.models import (
        Message, Mention,
        ThreadType, MessageStyle, MultiMsgStyle
    )
    from zlapi._exception import ZaloAPIException
except ImportError as e:
    print(f"[!] Thiếu thư viện: {e}")
    print("[!] Cài: pip install zlapi pyfiglet rich")
    sys.exit(1)

console = Console()
RESET = "\033[0m"


# ══════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════
def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def gradient_text(text, colors=None):
    if colors is None:
        colors = [(255, 0, 100), (255, 100, 0), (255, 220, 0),
                  (0, 220, 100), (0, 150, 255), (150, 0, 255)]
    max_seg = len(colors) - 1
    lines = text.splitlines()
    result = ""
    total = max(sum(len(l) for l in lines) - 1, 1)
    idx = 0
    for li, line in enumerate(lines):
        for ch in line:
            t = idx / total
            seg = int(t * max_seg)
            seg = max(0, min(seg, max_seg))
            c1 = colors[seg]
            c2 = colors[min(seg + 1, max_seg)]
            ratio = (t * max_seg) - seg
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            result += rgb(r, g, b) + ch
            idx += 1
        result += RESET
        if li != len(lines) - 1:
            result += "\n"
    return result + RESET


def print_color(text, color_type="info"):
    colors = {
        "success": "\033[92m", "error": "\033[91m",
        "warning": "\033[93m", "info": "\033[94m",
        "cyan": "\033[96m", "magenta": "\033[95m",
        "reset": RESET
    }
    print(f"{colors.get(color_type, colors['info'])}{text}{colors['reset']}")


def print_gradient(text):
    print(gradient_text(text))


def print_banner():
    banner = pyfiglet.figlet_format("ZIN", font="slant")
    print_gradient(banner + "     ZIN THIÊN ĐẠO - VĨNH HẰNG CHÍ TÔN\n")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_line(char="=", length=60, color="cyan"):
    print_color(char * length, color)


def print_header(text):
    print_line("═", 60, "cyan")
    print_gradient(f" {text} ")
    print_line("═", 60, "cyan")


# ══════════════════════════════════════════════════════════════
#  UTF-16 HELPERS
# ══════════════════════════════════════════════════════════════
def utf16_len(s):
    if not s:
        return 0
    return len(s.encode("utf-16-le")) // 2


def _make_mention(uid, length, offset):
    try:
        sig = inspect.signature(Mention.__init__)
        params = set(sig.parameters.keys())
    except Exception:
        params = {"uid", "length", "offset"}

    kwargs = {"uid": str(uid)}
    if "length" in params:
        kwargs["length"] = length
    elif "len" in params:
        kwargs["len"] = length
    if "offset" in params:
        kwargs["offset"] = offset
    elif "pos" in params:
        kwargs["pos"] = offset

    return Mention(**kwargs)


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
    sig = inspect.signature(ZaloAPI.__init__)
    params = list(sig.parameters.keys())

    base = {}
    if "imei" in params:
        base["imei"] = imei
    if "phone" in params:
        base["phone"] = ""
    if "password" in params:
        base["password"] = ""

    for key in ("session_cookies", "cookies", "cookie", "session_cookie"):
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
    for attr in ("_uid", "uid", "user_id", "userId"):
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
#  EXTRACT GROUP INFO
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

    for key in ["currentMems", "current_mems",
                "updateMems", "update_mems",
                "memberIds", "member_ids",
                "members", "memberList"]:
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
#  FETCH GROUPS
# ══════════════════════════════════════════════════════════════
def fetch_groups_with_name(client):
    try:
        raw = client.fetchAllGroups()
    except Exception as e:
        print_color(f"❌ fetchAllGroups lỗi: {e}", "error")
        return []

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


# ══════════════════════════════════════════════════════════════
#  GET GROUP MEMBERS
# ══════════════════════════════════════════════════════════════
def get_group_members(client, gid):
    raw = None
    try:
        raw = client.fetchGroupInfo(gid)
    except Exception as e:
        raise Exception(f"fetchGroupInfo lỗi: {e}")

    info = _extract_group_info(raw, gid)
    if not info:
        print_color(f"  ⚠️ Không extract được info của {gid}", "warning")
        return []

    uids = _extract_member_uids(info)
    if not uids:
        print_color(f"  ⚠️ Không extract được uid từ info", "warning")
        return []

    names_map = {}
    total = len(uids)
    for i, uid in enumerate(uids, 1):
        try:
            prof = client.fetchUserInfo(uid)
            names_map[uid] = _get_name_from_profiles(prof, uid)
        except Exception:
            names_map[uid] = f"User {uid}"

        if i % 10 == 0 or i == total:
            print_color(f"  → Đã lấy tên {i}/{total}", "info")

    return [{"uid": uid, "name": names_map.get(uid, f"User {uid}")} for uid in uids]


# ══════════════════════════════════════════════════════════════
#  FETCH FRIENDS
# ══════════════════════════════════════════════════════════════
def fetch_friends_with_name(client):
    raw = None
    last_err = None
    for func_name in ("fetchAllFriends", "getAllFriends",
                      "fetchFriendList", "getFriendList"):
        func = getattr(client, func_name, None)
        if not func:
            continue
        try:
            raw = func()
            if raw:
                break
        except Exception as e:
            last_err = e
            continue

    if not raw:
        if last_err:
            print_color(f"❌ Không lấy được bạn bè: {last_err}", "error")
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

    seen = set()
    clean_uids = []
    for u in uids:
        if not u or not str(u).isdigit():
            continue
        if len(str(u)) < 10 or len(str(u)) > 20:
            continue
        if u in seen:
            continue
        seen.add(u)
        clean_uids.append(str(u))

    if not clean_uids:
        return []

    print_color(f"🔄 Đang lấy tên {len(clean_uids)} người bạn...", "info")
    out = []
    total = len(clean_uids)
    for i, uid in enumerate(clean_uids, 1):
        name = f"User {uid}"
        try:
            prof = client.fetchUserInfo(uid)
            name = _get_name_from_profiles(prof, uid)
        except Exception:
            pass
        out.append({"uid": uid, "name": name})

        if i % 10 == 0 or i == total:
            print_color(f"  → Đã lấy {i}/{total}", "info")

    return out


# ══════════════════════════════════════════════════════════════
#  BUILD MESSAGE (CHỈ TAG ĐƠN)
# ══════════════════════════════════════════════════════════════
def build_msg_with_tag(content, tag):
    if not tag:
        return Message(text=content)

    tag_str = f"@{tag['name']}"
    full = content
    if full and not full.endswith(" "):
        full += " "

    offset = utf16_len(full)
    length = utf16_len(tag_str)

    mention_obj = _make_mention(tag["uid"], length, offset)
    full += tag_str

    return Message(text=full, mention=mention_obj)


# ══════════════════════════════════════════════════════════════
#  FAKE SOẠN NGẦM (chạy tự động, không hỏi user)
# ══════════════════════════════════════════════════════════════
def typing_then_sleep(client, thread_id, thread_type, seconds):
    """
    Bật typing → chờ `seconds` giây (refresh mỗi 3s) → tắt typing.
    Đây chính là delay, không random.
    """
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
#  SEND
# ══════════════════════════════════════════════════════════════
def send_group_msg(client, thread_id, content, tag=None, delay=3):
    try:
        typing_then_sleep(client, thread_id, ThreadType.GROUP, delay)
        msg = build_msg_with_tag(content, tag)
        client.send(msg, thread_id=thread_id, thread_type=ThreadType.GROUP)
        return "success"
    except ZaloAPIException as e:
        return f"failed: {e}"
    except Exception as e:
        return f"failed: {e}"


def send_dm_msg(client, user_id, content, delay=3):
    try:
        typing_then_sleep(client, user_id, ThreadType.USER, delay)
        msg = Message(text=content)
        client.send(msg, thread_id=user_id, thread_type=ThreadType.USER)
        return "success"
    except ZaloAPIException as e:
        return f"failed: {e}"
    except Exception as e:
        return f"failed: {e}"


# ══════════════════════════════════════════════════════════════
#  SPAM LOOP - BOX
# ══════════════════════════════════════════════════════════════
def start_spam_box(cookie_str, imei, account_name, uid,
                   thread_ids, thread_infos,
                   delay, message_lines, replace_text, tag):
    try:
        client = create_zalo_client(cookie_str, imei)
        info = get_zalo_user_info(client)
        if info["status"] != "success":
            print_color(f"❌ Xác thực thất bại: {info.get('msg')}", "error")
            return

        real_name = info.get("name", account_name)
        print_color(f"✅ BOX MODE: {real_name} (UID: {info['uid']})", "success")

        idx = 0
        while True:
            for tid in thread_ids:
                tname = thread_infos[tid]
                raw = message_lines[idx]
                content = raw.replace("{name}", replace_text) if "{name}" in raw else raw

                status = send_group_msg(client, tid, content,
                                        tag=tag, delay=delay)

                tag_display = f"🏷️ {tag['name']}" if tag else "🚫 no tag"
                if status == "success":
                    print_color(
                        f"👤 {real_name} | 📦 {tname} | {tag_display} | ✅",
                        "success"
                    )
                else:
                    print_color(f"👤 {real_name} | 📦 {tname} | ❌ {status}", "error")

                idx = (idx + 1) % len(message_lines)
    except Exception as e:
        print_color(f"❌ Lỗi {account_name}: {e}", "error")


# ══════════════════════════════════════════════════════════════
#  SPAM LOOP - DM
# ══════════════════════════════════════════════════════════════
def start_spam_dm(cookie_str, imei, account_name, uid,
                  user_ids, user_infos,
                  delay, message_lines, replace_text):
    try:
        client = create_zalo_client(cookie_str, imei)
        info = get_zalo_user_info(client)
        if info["status"] != "success":
            print_color(f"❌ Xác thực thất bại: {info.get('msg')}", "error")
            return

        real_name = info.get("name", account_name)
        print_color(f"✅ DM MODE: {real_name} (UID: {info['uid']})", "success")

        idx = 0
        while True:
            for tid in user_ids:
                tname = user_infos[tid]
                raw = message_lines[idx]
                content = raw.replace("{name}", replace_text) if "{name}" in raw else raw

                status = send_dm_msg(client, tid, content, delay=delay)

                if status == "success":
                    print_color(f"👤 {real_name} | 💬 {tname} | ✅", "success")
                else:
                    print_color(f"👤 {real_name} | 💬 {tname} | ❌ {status}", "error")

                idx = (idx + 1) % len(message_lines)
    except Exception as e:
        print_color(f"❌ Lỗi {account_name}: {e}", "error")


# ══════════════════════════════════════════════════════════════
#  NHẬP FILE / DELAY
# ══════════════════════════════════════════════════════════════
def input_message_file():
    fp = input(gradient_text("📂 File .txt nội dung: ",
                              [(0, 255, 0), (0, 0, 255)])).strip()
    try:
        with open(fp, "r", encoding="utf-8") as f:
            msg_lines = [l.strip() for l in f if l.strip()]
        if not msg_lines:
            print_color("❌ File trống", "error")
            return None
        print_color(f"✅ {len(msg_lines)} dòng", "success")
        if len(msg_lines) > 200:
            print_color("⚠️ File >200 dòng, Zalo dễ chặn spam!", "warning")
        return msg_lines
    except Exception as e:
        print_color(f"❌ Đọc file: {e}", "error")
        return None


def input_delay():
    try:
        s = input(gradient_text("⏳ Delay (giây, VD: 3): ",
                                 [(0, 255, 0), (0, 0, 255)])).strip()
        d = int(s) if s else 3
        return max(1, d)
    except ValueError:
        print_color("⚠️ Nhập sai, mặc định 3 giây", "warning")
        return 3


# ══════════════════════════════════════════════════════════════
#  MODE BOX
# ══════════════════════════════════════════════════════════════
def config_box(client, info):
    print_color("🔍 Đang lấy danh sách NHÓM...", "info")
    groups = fetch_groups_with_name(client)

    if not groups:
        print_color("⚠️ Không có nhóm nào!", "warning")
        manual = input(gradient_text(
            "🔧 Nhập ID nhóm thủ công (cách nhau dấu phẩy, Enter bỏ qua): ",
            [(0, 255, 0), (0, 0, 255)])).strip()
        if manual:
            for gid in manual.replace(",", " ").split():
                gid = gid.strip()
                if gid:
                    groups.append({"gid": gid, "name": f"Nhóm {gid}"})

    if not groups:
        print_color("❌ Không có nhóm nào", "error")
        return None

    print_color(f"✅ Tìm thấy {len(groups)} nhóm", "success")

    gtable = Table(title=f"📦 NHÓM - {len(groups)}",
                   show_header=True, header_style="bold magenta", box=box.ROUNDED)
    gtable.add_column("STT", style="cyan", width=5, justify="center")
    gtable.add_column("Tên nhóm", style="green")
    gtable.add_column("Group ID", style="yellow")
    for idx, g in enumerate(groups, 1):
        disp = f"{g['name'][:45]}{'...' if len(g['name']) > 45 else ''}"
        gtable.add_row(str(idx), disp, g["gid"])
    console.print(gtable)
    print_line()

    sel = []
    while not sel:
        raw = input(gradient_text("🎯 Chọn nhóm (1,3 / 1 3 / all): ",
                                   [(0, 255, 0), (0, 0, 255)])).strip()
        if raw.lower() == "all":
            sel = list(range(1, len(groups) + 1))
            break
        for p in raw.replace(",", " ").split():
            if p.isdigit():
                k = int(p)
                if 1 <= k <= len(groups):
                    sel.append(k)
        if not sel:
            print_color("❌ Lựa chọn không hợp lệ. Nhập lại!", "error")

    selected_ids = [groups[k - 1]["gid"] for k in sel]
    thread_infos = {gid: groups[sel[i] - 1]["name"]
                    for i, gid in enumerate(selected_ids)}

    print_color("🔄 Lấy thành viên trong nhóm...", "info")
    all_members = []
    for tid in selected_ids:
        try:
            members = get_group_members(client, tid)
            all_members.extend(members)
            print_color(f"✅ Nhóm {tid}: {len(members)} member", "success")
        except Exception as e:
            print_color(f"⚠️ {tid}: {e}", "warning")

    seen = set()
    unique_members = []
    for m in all_members:
        if m["uid"] not in seen:
            seen.add(m["uid"])
            unique_members.append(m)
    all_members = unique_members

    # Chọn tag đơn
    tag = None
    if all_members:
        mtable = Table(title=f"👥 THÀNH VIÊN - {len(all_members)}",
                       show_header=True, header_style="bold blue", box=box.ROUNDED)
        mtable.add_column("STT", style="cyan", width=5, justify="center")
        mtable.add_column("Tên", style="green")
        mtable.add_column("UID", style="yellow")
        for idx, m in enumerate(all_members, 1):
            disp = f"{m['name'][:35]}{'...' if len(m['name']) > 35 else ''}"
            mtable.add_row(str(idx), disp, m["uid"])
        console.print(mtable)
        print_line()

        raw_tag = input(gradient_text(
            "🏷️ Chọn 1 người để tag (STT / khong): ",
            [(0, 255, 0), (0, 0, 255)])).strip()

        if raw_tag.lower() not in ("khong", "k", ""):
            if raw_tag.isdigit():
                k = int(raw_tag)
                if 1 <= k <= len(all_members):
                    tag = all_members[k - 1]
                    print_color(f"✅ Sẽ tag: {tag['name']}", "success")
                else:
                    print_color("⚠️ STT không hợp lệ, không tag", "warning")
            else:
                print_color("⚠️ Nhập không hợp lệ, không tag", "warning")

    msg_lines = input_message_file()
    if not msg_lines:
        return None

    replace_text = input(gradient_text(
        "✏️ Thay {name} bằng (Enter nếu không): ",
        [(0, 255, 0), (0, 0, 255)])).strip()

    delay = input_delay()

    return {
        "mode": "box",
        "selected_ids": selected_ids,
        "thread_infos": thread_infos,
        "tag": tag,
        "msg_lines": msg_lines,
        "replace_text": replace_text,
        "delay": delay,
    }


# ══════════════════════════════════════════════════════════════
#  MODE DM
# ══════════════════════════════════════════════════════════════
def config_dm(client, info):
    print_color("🔍 Đang lấy danh sách BẠN BÈ...", "info")
    friends = fetch_friends_with_name(client)

    if not friends:
        print_color("⚠️ Không lấy được bạn bè tự động!", "warning")
        manual = input(gradient_text(
            "🔧 Nhập UID thủ công (cách nhau dấu phẩy, Enter bỏ qua): ",
            [(0, 255, 0), (0, 0, 255)])).strip()
        if manual:
            for uid_t in manual.replace(",", " ").split():
                uid_t = uid_t.strip()
                if uid_t:
                    friends.append({"uid": uid_t, "name": f"User {uid_t}"})

    if not friends:
        print_color("❌ Không có ai để gửi", "error")
        return None

    print_color(f"✅ Tìm thấy {len(friends)} người bạn", "success")

    ftable = Table(title=f"👥 BẠN BÈ - {len(friends)}",
                   show_header=True, header_style="bold magenta", box=box.ROUNDED)
    ftable.add_column("STT", style="cyan", width=5, justify="center")
    ftable.add_column("Tên", style="green")
    ftable.add_column("UID", style="yellow")
    for idx, f in enumerate(friends, 1):
        disp = f"{f['name'][:40]}{'...' if len(f['name']) > 40 else ''}"
        ftable.add_row(str(idx), disp, f["uid"])
    console.print(ftable)
    print_line()

    sel = []
    while not sel:
        raw = input(gradient_text(
            "🎯 Chọn người để nhắn (1,3 / 1 3 / all): ",
            [(0, 255, 0), (0, 0, 255)])).strip()
        if raw.lower() == "all":
            sel = list(range(1, len(friends) + 1))
            break
        for p in raw.replace(",", " ").split():
            if p.isdigit():
                k = int(p)
                if 1 <= k <= len(friends):
                    sel.append(k)
        if not sel:
            print_color("❌ Lựa chọn không hợp lệ. Nhập lại!", "error")

    selected_ids = [friends[k - 1]["uid"] for k in sel]
    user_infos = {uid_t: friends[k - 1]["name"]
                  for k, uid_t in zip(sel, selected_ids)}

    msg_lines = input_message_file()
    if not msg_lines:
        return None

    replace_text = input(gradient_text(
        "✏️ Thay {name} bằng (Enter nếu không): ",
        [(0, 255, 0), (0, 0, 255)])).strip()

    delay = input_delay()

    return {
        "mode": "dm",
        "selected_ids": selected_ids,
        "user_infos": user_infos,
        "msg_lines": msg_lines,
        "replace_text": replace_text,
        "delay": delay,
    }


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    clear()
    print_banner()
    print_header("𝙕𝙄𝙉 𝙏𝙃𝙄Ê𝙉 ĐẠ𝙊 - 𝙕𝘼𝙇𝙊 𝙏𝙊𝙊𝙇")

    try:
        n = int(input(gradient_text("💠 Số lượng acc: ",
                                     [(0, 255, 0), (0, 0, 255)])))
        if n < 1:
            print_color("❌ Phải > 0", "error")
            return
    except ValueError:
        print_color("❌ Nhập số nguyên", "error")
        return

    processes = []

    for i in range(n):
        print_header(f"📝 TÀI KHOẢN {i + 1}")

        cookie_raw = input(gradient_text("🍪 Cookie Zalo: ",
                                         [(0, 255, 0), (0, 0, 255)])).strip()
        if not cookie_raw:
            print_color("❌ Cookie rỗng", "error")
            continue

        imei = input(gradient_text("📱 IMEI: ",
                                    [(0, 255, 0), (0, 0, 255)])).strip()
        if not imei:
            print_color("❌ IMEI rỗng", "error")
            continue

        print_color("🔍 Kiểm tra kết nối...", "info")
        try:
            client = create_zalo_client(cookie_raw, imei)
            info = get_zalo_user_info(client)
            if info["status"] != "success" or not info.get("uid"):
                print_color(f"❌ Xác thực thất bại: {info.get('msg', 'no uid')}",
                            "error")
                continue
            print_color(f"✅ {info['name']} (UID: {info['uid']})", "success")
        except Exception as e:
            print_color(f"❌ Lỗi kết nối: {e}", "error")
            continue

        print_line()
        print_color("📋 CHỌN CHẾ ĐỘ:", "cyan")
        print_color("   1. Box       (spam nhóm + tag đơn)", "cyan")
        print_color("   2. IB riêng  (DM bạn bè)", "cyan")
        print_line()

        mode = ""
        while mode not in ("1", "2"):
            mode = input(gradient_text("👉 Nhập 1 hoặc 2: ",
                                        [(0, 255, 0), (0, 0, 255)])).strip()
            if mode not in ("1", "2"):
                print_color("❌ Chỉ nhập 1 hoặc 2!", "error")

        if mode == "1":
            print_header(f"📦 BOX MODE - {info['name']}")
            cfg = config_box(client, info)
            if not cfg:
                continue

            print_header(f"🚀 KHAI MỞ BOX - {info['name']}")
            p = multiprocessing.Process(
                target=start_spam_box,
                args=(cookie_raw, imei, info["name"], info["uid"],
                      cfg["selected_ids"], cfg["thread_infos"],
                      cfg["delay"], cfg["msg_lines"], cfg["replace_text"],
                      cfg["tag"])
            )
        else:
            print_header(f"💬 DM MODE - {info['name']}")
            cfg = config_dm(client, info)
            if not cfg:
                continue

            print_header(f"🚀 KHAI MỞ DM - {info['name']}")
            p = multiprocessing.Process(
                target=start_spam_dm,
                args=(cookie_raw, imei, info["name"], info["uid"],
                      cfg["selected_ids"], cfg["user_infos"],
                      cfg["delay"], cfg["msg_lines"], cfg["replace_text"])
            )

        processes.append(p)
        p.start()
        time.sleep(2)

    if not processes:
        print_color("❌ Không có process nào chạy", "error")
        return

    print_header("🎉 ĐANG CHẠY")
    print_color(f"✅ {len(processes)} tài khoản đang chạy", "success")
    print_color("⏹️ Ctrl+C để dừng", "warning")
    print_line()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_color("\n🛑 Đang dừng...", "error")
        for p in processes:
            p.terminate()
        time.sleep(2)
        print_color("✅ Đã dừng", "success")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n🛑 Đã dừng", "error")
    except Exception as e:
        print_color(f"\n❌ Lỗi: {e}", "error")
        import traceback
        traceback.print_exc()