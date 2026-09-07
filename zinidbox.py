import requests
import json
import re
import gzip
import zlib
from typing import Dict, List, Tuple, Optional

# ================================
# TIỆN ÍCH MÀU SẮC (ANSI 24-bit RGB)
# ================================
RESET = '\033[0m'
def rgb_text(r: int, g: int, b: int, text: str) -> str:
    return f'\033[38;2;{r};{g};{b}m{text}{RESET}'

def rgb_bg(r: int, g: int, b: int, text: str) -> str:
    return f'\033[48;2;{r};{g};{b}m{text}{RESET}'

def gradient_text(text: str, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]) -> str:
    result = ''
    n = len(text)
    if n == 0:
        return ''
    for i, ch in enumerate(text):
        ratio = i / max(n - 1, 1)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        result += f'\033[38;2;{r};{g};{b}m{ch}{RESET}'
    return result

def gradient_text_7(text: str) -> str:
    """Gradient 7 màu cận dịu (tươi hơn pastel 20%)."""
    colors = [
        (255, 80, 80),     # Đỏ
        (255, 160, 0),     # Cam
        (255, 220, 0),     # Vàng
        (100, 220, 100),   # Lục
        (80, 160, 255),    # Lam
        (140, 100, 255),   # Chàm
        (220, 80, 220)     # Tím
    ]
    result = ''
    n = len(text)
    if n == 0:
        return ''
    segments = len(colors) - 1
    for i, ch in enumerate(text):
        ratio = i / max(n - 1, 1)
        seg = ratio * segments
        idx = int(seg)
        if idx >= segments:
            idx = segments - 1
        local_ratio = seg - idx
        r = int(colors[idx][0] + (colors[idx+1][0] - colors[idx][0]) * local_ratio)
        g = int(colors[idx][1] + (colors[idx+1][1] - colors[idx][1]) * local_ratio)
        b = int(colors[idx][2] + (colors[idx+1][2] - colors[idx][2]) * local_ratio)
        result += f'\033[38;2;{r};{g};{b}m{ch}{RESET}'
    return result

# Các màu dịu nhẹ
PINK        = (255, 105, 180)
LIGHT_PINK  = (255, 182, 193)
CORAL       = (255, 127, 80)
ORANGE      = (255, 165, 0)
GOLD        = (255, 215, 0)
MINT        = (152, 251, 152)
LIGHT_GREEN = (144, 238, 144)
AQUA        = (127, 255, 212)
SKY_BLUE    = (135, 206, 235)
LIGHT_BLUE  = (173, 216, 230)
LAVENDER    = (230, 230, 250)
PLUM        = (221, 160, 221)
SALMON      = (250, 128, 114)

# ================================
# HÀM GIẢI MÃ RESPONSE AN TOÀN
# ================================
def decode_response_content(response: requests.Response) -> str:
    content = response.content
    enc = response.headers.get('Content-Encoding', '').lower()
    if not enc:
        if content.startswith(b'\x1f\x8b'):
            enc = 'gzip'
        elif content.startswith(b'\x78\x9c') or content.startswith(b'\x78\x01') or content.startswith(b'\x78\xda'):
            enc = 'deflate'
        elif content.startswith(b'\x1b\x6b'):
            enc = 'br'

    if enc:
        try:
            if 'gzip' in enc:
                content = gzip.decompress(content)
            elif 'deflate' in enc:
                try:
                    content = zlib.decompress(content)
                except zlib.error:
                    content = zlib.decompress(content, -zlib.MAX_WBITS)
            elif 'br' in enc:
                try:
                    import brotli
                    content = brotli.decompress(content)
                except ImportError:
                    pass
        except Exception:
            pass

    encoding = response.encoding
    if not encoding or encoding.lower() == 'iso-8859-1':
        apparent = response.apparent_encoding
        if apparent and apparent.lower() != 'iso-8859-1':
            encoding = apparent
        else:
            encoding = 'utf-8'
    try:
        html = content.decode(encoding, errors='replace')
    except:
        html = content.decode('utf-8', errors='replace')
    return html

# ================================
# HÀM DECODE TÊN UNICODE (FIX LỖI HIỂN THỊ)
# ================================
def decode_name(name: str) -> str:
    """Xử lý tên có chứa escape unicode."""
    if not name:
        return name
    try:
        if '\\u' in name:
            return name.encode('utf-8').decode('unicode_escape')
        if '\\x' in name:
            return name.encode('utf-8').decode('unicode_escape')
    except Exception:
        pass
    return name

# ================================
# HÀM PARSE JSON LINH HOẠT CHO GRAPHQLBATCH
# ================================
def parse_graphqlbatch_response(text: str):
    """Parse response có thể có prefix for(;;); hoặc nhiều JSON object."""
    text = text.strip()
    for prefix in ['for(;;);', 'for (;;);']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(text)
        return obj
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None

# ================================
# BƯỚC 1: NHẬP COOKIE
# ================================
def input_cookie() -> str:
    print(rgb_text(*LIGHT_BLUE, "➤ Nhập cookie (hoặc 'q' để thoát): "))
    return input().strip()

# ================================
# BƯỚC 2: CHUYỂN COOKIE THÀNH DICT
# ================================
def parse_cookie(cookie_str: str) -> Dict[str, str]:
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    if 'c_user' not in cookies:
        print(rgb_text(*SALMON, "⚠️  Cảnh báo: Cookie thiếu 'c_user'."))
    return cookies

# ================================
# LẤY THÔNG TIN TỪ TRANG MESSAGES (fb_dtsg, jazoest, thread_list doc_id)
# ================================
def get_graphql_info(session: requests.Session, cookies: Dict[str, str]):
    url = 'https://www.facebook.com/messages/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
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
    session.headers.update(headers)
    response = session.get(url, cookies=cookies, allow_redirects=True, timeout=15)

    final_url = response.url
    if '/login' in final_url or '/checkpoint' in final_url:
        raise Exception("Cookie không hợp lệ hoặc đã hết hạn.")
    if response.status_code != 200:
        raise Exception(f"Không thể truy cập trang messages (HTTP {response.status_code}).")

    html = decode_response_content(response)

    patterns = [
        r'"dtsg":{"token":"([^"]+)"',
        r'DTSGInitialData.*?setToken\("([^"]+)"\)',
        r'name="fb_dtsg" value="([^"]+)"',
        r'"fb_dtsg":{"token":"([^"]+)"',
        r'\["fb_dtsg","([^"]+)"',
    ]
    fb_dtsg = None
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            fb_dtsg = match.group(1)
            break

    if not fb_dtsg:
        response_home = session.get('https://www.facebook.com/', cookies=cookies, allow_redirects=True, timeout=15)
        if response_home.status_code == 200:
            html_home = decode_response_content(response_home)
            for pattern in patterns:
                match = re.search(pattern, html_home, re.DOTALL)
                if match:
                    fb_dtsg = match.group(1)
                    break
        if not fb_dtsg:
            raise Exception("Không tìm thấy fb_dtsg.")

    jazoest = None
    jazoest_patterns = [
        r'"jazoest":"(\d+)"',
        r'name="jazoest" value="(\d+)"',
        r'jazoest=(\d+)',
    ]
    for pattern in jazoest_patterns:
        match = re.search(pattern, html)
        if match:
            jazoest = match.group(1)
            break
    if not jazoest:
        jazoest = ''

    doc_id = None
    friendly_name = None
    thread_query_patterns = [
        r'"doc_id":"(\d+)"[^}]*?"queryName":"(ThreadListQuery|MessengerThreadListQuery)"',
        r'"queryName":"(ThreadListQuery|MessengerThreadListQuery)"[^}]*?"doc_id":"(\d+)"',
        r'ThreadListQuery[^}]*?doc_id["\']?\s*:\s*["\']?(\d+)',
        r'MessengerThreadListQuery[^}]*?doc_id["\']?\s*:\s*["\']?(\d+)',
    ]
    for pattern in thread_query_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            if len(match.groups()) == 2:
                if match.group(1).isdigit():
                    doc_id = match.group(1)
                    friendly_name = match.group(2)
                else:
                    friendly_name = match.group(1)
                    doc_id = match.group(2)
            else:
                doc_id = match.group(1)
                name_match = re.search(r'"(?:queryName|friendly_name)"\s*:\s*"([^"]+)"', html[match.start()-500:match.end()+500])
                if name_match:
                    friendly_name = name_match.group(1)
            break

    if not doc_id or not friendly_name:
        doc_ids = re.findall(r'"doc_id":"(\d+)"', html)
        query_names = re.findall(r'"queryName":"([^"]+)"', html)
        for qn in query_names:
            if 'Thread' in qn:
                idx = html.find(f'"queryName":"{qn}"')
                if idx != -1:
                    before = html[max(0, idx-1000):idx]
                    after = html[idx:idx+1000]
                    doc_match_before = re.search(r'"doc_id":"(\d+)"', before)
                    doc_match_after = re.search(r'"doc_id":"(\d+)"', after)
                    if doc_match_before:
                        doc_id = doc_match_before.group(1)
                        friendly_name = qn
                        break
                    elif doc_match_after:
                        doc_id = doc_match_after.group(1)
                        friendly_name = qn
                        break

    if not doc_id:
        doc_id = "1349387578499440"
    if not friendly_name:
        friendly_name = "ThreadListQuery"

    session.thread_list_doc_id = doc_id
    session.thread_list_friendly_name = friendly_name
    session.fb_dtsg = fb_dtsg
    session.jazoest = jazoest
    session.participants_cache = {}

    return fb_dtsg

# ================================
# GỌI GRAPHQL LẤY DANH SÁCH THREAD
# ================================
def get_thread_list(session: requests.Session, cookies: Dict[str, str],
                    fb_dtsg: str, limit: int = 50) -> List[Dict[str, str]]:
    url = 'https://www.facebook.com/api/graphql/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.facebook.com/messages/',
        'Origin': 'https://www.facebook.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    session.headers.update(headers)

    variables = {
        "count": limit,
        "cursor": None,
        "filter": {},
        "include_self": True,
        "threadType": "INBOX",
        "limit": limit,
    }
    data = {
        "fb_dtsg": fb_dtsg,
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": session.thread_list_friendly_name,
        "variables": json.dumps(variables),
        "doc_id": session.thread_list_doc_id,
        "dpr": "1",
        "__a": "1",
        "__req": "1",
        "__rev": "1",
        "fb_api_analytics_tags": "[]",
        "fb_api_req_app_id": "0",
        "fb_api_req_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "fb_api_req_referrer": "https://www.facebook.com/messages/",
        "fb_api_req_display": "popup",
        "fb_api_req_source": "www",
    }

    response = session.post(url, cookies=cookies, data=data, timeout=20)
    if response.status_code != 200:
        raise Exception(f"GraphQL trả mã lỗi {response.status_code}")

    decoded_text = decode_response_content(response)
    json_data = None
    try:
        json_data = json.loads(decoded_text)
    except json.JSONDecodeError:
        match = re.search(r'<pre[^>]*>(.*?)</pre>', decoded_text, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1).strip())
            except:
                pass
        if json_data is None:
            raise Exception("Không parse được JSON từ GraphQL.")

    if 'errors' in json_data:
        error_messages = [f"{err.get('message', 'Unknown')}" for err in json_data['errors']]
        raise Exception("GraphQL trả lỗi: " + "; ".join(error_messages))

    threads = []
    seen_ids = set()

    def extract_participants_from_thread(thread_dict):
        participants = []
        for key in ['all_participants', 'participants']:
            if key in thread_dict and isinstance(thread_dict[key], dict):
                nodes = thread_dict[key].get('nodes', [])
                if isinstance(nodes, list):
                    for p in nodes:
                        if isinstance(p, dict):
                            uid = p.get('id')
                            name = p.get('name', p.get('short_name', 'Không tên'))
                            name = decode_name(name)
                            if uid:
                                participants.append((name, uid))
        return participants

    try:
        nodes = json_data.get('data', {}).get('viewer', {}).get('message_threads', {}).get('nodes')
        if nodes:
            for thread in nodes:
                if not isinstance(thread, dict):
                    continue
                thread_key = thread.get('thread_key') or {}
                thread_fbid = thread_key.get('thread_fbid')
                other_user_id = thread_key.get('other_user_id')
                thread_id = thread_fbid or other_user_id
                if not thread_id:
                    continue
                thread_name = thread.get('name')
                if not thread_name:
                    participant_list = extract_participants_from_thread(thread)
                    thread_name = participant_list[0][0] if participant_list else 'Không tên'
                else:
                    thread_name = decode_name(thread_name)
                if thread_id not in seen_ids:
                    seen_ids.add(thread_id)
                    thread_info = {
                        'name': thread_name,
                        'thread_id': thread_id,
                        'thread_fbid': thread_fbid,
                        'other_user_id': other_user_id,
                        'participants': extract_participants_from_thread(thread)
                    }
                    threads.append(thread_info)
    except Exception:
        pass

    if not threads:
        def extract_threads(obj):
            if isinstance(obj, dict):
                if 'threads' in obj:
                    for thread in obj['threads']:
                        thread_key = thread.get('thread_key', {})
                        thread_fbid = thread_key.get('thread_fbid')
                        other_user_id = thread_key.get('other_user_id')
                        thread_id = thread_fbid or other_user_id
                        if thread_id:
                            thread_name = thread.get('name')
                            if thread_name:
                                thread_name = decode_name(thread_name)
                            else:
                                thread_name = 'Không tên'
                            if thread_name == 'Không tên':
                                participants = extract_participants_from_thread(thread)
                                thread_name = participants[0][0] if participants else 'Không tên'
                            if thread_id not in seen_ids:
                                seen_ids.add(thread_id)
                                thread_info = {
                                    'name': thread_name,
                                    'thread_id': thread_id,
                                    'thread_fbid': thread_fbid,
                                    'other_user_id': other_user_id,
                                    'participants': extract_participants_from_thread(thread)
                                }
                                threads.append(thread_info)
                for value in obj.values():
                    extract_threads(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_threads(item)
        extract_threads(json_data)

    return threads

# ================================
# LẤY THÀNH VIÊN BẰNG GRAPHQLBATCH (doc_id cố định)
# ================================
def get_thread_participants(session: requests.Session, cookies: Dict[str, str],
                            fb_dtsg: str, thread_info: Dict[str, str],
                            limit: int = 200) -> List[Tuple[str, str]]:
    if 'participants' in thread_info and thread_info['participants']:
        return [(decode_name(name), uid) for name, uid in thread_info['participants']]

    thread_fbid = thread_info.get('thread_fbid')
    other_user_id = thread_info.get('other_user_id')
    thread_id_param = thread_fbid if thread_fbid else other_user_id
    if not thread_id_param:
        return []

    cache = getattr(session, 'participants_cache', {})
    if thread_id_param in cache:
        return cache[thread_id_param]

    jazoest = getattr(session, 'jazoest', '')

    url = 'https://www.facebook.com/api/graphqlbatch/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.facebook.com',
        'Referer': 'https://www.facebook.com/messages/',
        'Connection': 'keep-alive',
    }

    queries = {
        'o0': {
            'doc_id': '3449967031715030',
            'query_params': {
                'id': thread_id_param,
                'message_limit': 0,
                'load_messages': False,
                'load_read_receipts': False,
                'before': None
            }
        }
    }

    data = {
        'queries': json.dumps(queries),
        'batch_name': 'MessengerGraphQLThreadFetcher',
        'fb_dtsg': fb_dtsg,
        'jazoest': jazoest,
    }

    try:
        response = session.post(url, cookies=cookies, headers=headers, data=data, timeout=15)
        if response.status_code != 200:
            print(rgb_text(*SALMON, f"Lỗi HTTP {response.status_code} khi gọi graphqlbatch"))
            return []

        decoded_text = decode_response_content(response)
        json_data = parse_graphqlbatch_response(decoded_text)
        if json_data is None:
            print(rgb_text(*SALMON, "Không parse được JSON từ graphqlbatch"))
            print(rgb_text(*SALMON, "\n--- DEBUG: Raw response (1000 ký tự đầu) ---"))
            print(decoded_text[:1000])
            print(rgb_text(*SALMON, "--- Kết thúc debug ---\n"))
            return []

        participants = []
        seen_uids = set()

        def extract_participants(obj):
            if isinstance(obj, dict):
                if 'message_thread' in obj:
                    thread = obj['message_thread']
                    all_participants = thread.get('all_participants', {})
                    edges = all_participants.get('edges', [])
                    for edge in edges:
                        node = edge.get('node', {})
                        actor = node.get('messaging_actor', node)
                        uid = actor.get('id')
                        name = actor.get('name', 'Không tên')
                        name = decode_name(name)
                        if uid and uid not in seen_uids:
                            seen_uids.add(uid)
                            participants.append((name, uid))
                for value in obj.values():
                    extract_participants(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_participants(item)

        extract_participants(json_data)

        if participants:
            result = participants
            session.participants_cache[thread_id_param] = result
            return result

        print(rgb_text(*SALMON, "\n--- DEBUG: Raw graphqlbatch response (1000 ký tự đầu) ---"))
        print(decoded_text[:1000])
        print(rgb_text(*SALMON, "--- Kết thúc debug ---\n"))
        return []

    except Exception as e:
        print(rgb_text(*SALMON, f"Lỗi khi gọi graphqlbatch: {e}"))
        return []

# ================================
# HIỂN THỊ KẾT QUẢ ĐẸP MẮT (Gradient 7 màu cận dịu + gạch phân cách)
# ================================
def display_threads(threads: List[Dict[str, str]]):
    if not threads:
        print(rgb_text(*ORANGE, "Không tìm thấy thread nào."))
        return

    print()
    print(gradient_text("─" * 40, LIGHT_PINK, LIGHT_BLUE))
    print(rgb_text(*MINT, f"✨ Đã tìm thấy {len(threads)} cuộc trò chuyện:"))
    print(gradient_text("─" * 40, LIGHT_BLUE, LIGHT_PINK))
    print()
    for idx, thread in enumerate(threads, 1):
        if idx > 1:
            print(f"   {'─' * 30}")
        line_text = f"{idx:>3}. {thread['name']} → {thread['thread_id']}"
        print(f"  {gradient_text_7(line_text)}")
    print()

def display_participants(participants: List[Tuple[str, str]]):
    if not participants:
        print(rgb_text(*ORANGE, "Không tìm thấy thành viên nào."))
        return

    max_name_len = max(len(name) for name, _ in participants) if participants else 0
    max_name_len = min(max_name_len, 40)

    print()
    print(gradient_text("─" * 40, LIGHT_GREEN, LIGHT_BLUE))
    print(rgb_text(*MINT, f"👥 Danh sách thành viên ({len(participants)} người):"))
    print(gradient_text("─" * 40, LIGHT_BLUE, LIGHT_GREEN))
    print()
    for idx, (name, uid) in enumerate(participants, 1):
        if idx > 1:
            print(f"   {'─' * 30}")
        name_padded = name.ljust(max_name_len)
        line_text = f"{idx:>3}. {name_padded} → {uid}"
        print(f"  {gradient_text_7(line_text)}")
    print()

# ================================
# HÀM CHÍNH
# ================================
def main():
    print()
    print(gradient_text("═" * 60, PINK, GOLD))
    print()
    print(gradient_text("   ZIN - THIÊN ĐẠO  ", PINK, GOLD))
    print()
    print(rgb_text(*LAVENDER, "   Nhập cookie để lấy danh sách ID box  "))
    print()
    print(gradient_text("═" * 60, GOLD, PINK))
    print()

    summary = []
    cookie_count = 0
    while True:
        cookie_count += 1
        print(rgb_text(*SKY_BLUE, f"\n══════════════ COOKIE #{cookie_count} ══════════════"))
        try:
            cookie_str = input_cookie()
            if cookie_str.lower() in ['q', 'quit', 'exit']:
                print(rgb_text(*CORAL, "👋 Tạm biệt!"))
                break
            if not cookie_str.strip():
                print(rgb_text(*SALMON, "⚠️  Cookie rỗng, vui lòng nhập lại."))
                cookie_count -= 1
                continue

            cookies = parse_cookie(cookie_str)
            session = requests.Session()

            print(rgb_text(*LIGHT_GREEN, "⏳ Đang xử lý..."))
            fb_dtsg = get_graphql_info(session, cookies)
            threads = get_thread_list(session, cookies, fb_dtsg, limit=50)

            display_threads(threads)

            if threads:
                while True:
                    choice = input(rgb_text(*LIGHT_BLUE, "Nhập số thứ tự thread để xem thành viên (hoặc 'b' để bỏ qua, 'q' để thoát): ")).strip()
                    if choice.lower() in ['q', 'quit', 'exit']:
                        print(rgb_text(*CORAL, "👋 Tạm biệt!"))
                        return
                    if choice.lower() == 'b':
                        break
                    if not choice.isdigit():
                        print(rgb_text(*SALMON, "⚠️  Vui lòng nhập số."))
                        continue
                    idx = int(choice)
                    if 1 <= idx <= len(threads):
                        selected = threads[idx - 1]
                        print(rgb_text(*GOLD, f"\n🔍 Đang lấy thành viên của: {selected['name']}"))
                        try:
                            participants = get_thread_participants(session, cookies, fb_dtsg, selected)
                            display_participants(participants)
                        except Exception as e:
                            print(rgb_text(*SALMON, f"❌ Lỗi khi lấy thành viên: {e}"))
                    else:
                        print(rgb_text(*SALMON, "⚠️  Số không hợp lệ."))

            summary.append((cookie_count, "SUCCESS", f"{len(threads)} threads"))

        except Exception as e:
            print(rgb_text(*SALMON, f"❌ Lỗi: {e}"))
            summary.append((cookie_count, "FAILED", str(e)))

    if summary:
        print(rgb_text(*GOLD, "\n════════════════ SUMMARY ════════════════"))
        for idx, status, msg in summary:
            if status == "SUCCESS":
                print(rgb_text(*MINT, f"  Cookie #{idx}: ✅ SUCCESS - {msg}"))
            else:
                print(rgb_text(*SALMON, f"  Cookie #{idx}: ❌ FAILED - {msg}"))
        print(rgb_text(*GOLD, "════════════════════════════════════════"))

if __name__ == "__main__":
    main()