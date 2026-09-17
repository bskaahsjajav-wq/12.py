# ═══════════════════════════════════════════════════════════════
#   ZIN  ✦  Vô Tận Pháp Lực  ✦  FB AUTO COMMENT
#   watermark: ZIN  •  ascii-safe engine  •  press any key
# ═══════════════════════════════════════════════════════════════

import base64, json, re, uuid, time, sys, os, random, math, threading

try:
    import requests
except ImportError:
    print("[!] pip install requests"); sys.exit(1)

# ─────────── PALETTE ───────────
class C:
    P1='\033[38;5;93m';  P2='\033[38;5;129m'; P3='\033[38;5;165m'
    P4='\033[38;5;171m'; P5='\033[38;5;207m'
    B1='\033[38;5;33m';  B2='\033[38;5;39m';  B3='\033[38;5;45m'
    K1='\033[38;5;51m';  K2='\033[38;5;87m';  K3='\033[38;5;123m'
    G1='\033[38;5;46m';  G2='\033[38;5;118m'
    Y1='\033[38;5;226m'; Y2='\033[38;5;220m'
    O1='\033[38;5;208m'; O2='\033[38;5;214m'
    R1='\033[38;5;203m'; R2='\033[38;5;196m'
    W ='\033[38;5;231m'; D1='\033[38;5;247m'
    D2='\033[38;5;242m'; D3='\033[38;5;238m'
    RST='\033[0m'; B='\033[1m'

_RB = [C.P5, C.P4, C.P3, C.P2, C.P1, C.B1, C.B2, C.B3,
       C.K1, C.K2, C.K3, C.G2, C.G1, C.Y1, C.O2, C.O1, C.R1]

# ─────────── ENGINE (ASCII-SAFE, NO-WRAP) ───────────
W = 20       # canvas width — chỉ ASCII/narrow, chắc chắn 1 cột
H = 4        # canvas height
PAD = "  "

_start = threading.Event()
_canvas_ready = [False]

def _render(rows):
    """Vẽ H dòng canvas. Frame đầu in mới, các frame sau move up + redraw."""
    if _canvas_ready[0]:
        sys.stdout.write(f"\033[{H}A")
    else:
        _canvas_ready[0] = True
    sys.stdout.write("".join("\r\033[K" + PAD + r + "\n" for r in rows))
    sys.stdout.flush()

def _grid_to_rows(grid):
    """grid[r][i] = (char, color). char==' ' -> space, else wrap với color."""
    out = []
    for r in range(H):
        s = ""
        for ch, col in grid[r]:
            s += (f"{col}{ch}" if ch != " " else " ")
        out.append(s)
    return out

def _w(content):
    sys.stdout.write("\r\033[K" + PAD + content); sys.stdout.flush()

def _end():
    sys.stdout.write("\n"); sys.stdout.flush()

# ─────────── ANY-KEY LISTENER ───────────
def _getch():
    try:
        import termios, tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        try:
            import msvcrt
            return msvcrt.getch().decode('utf-8', 'ignore')
        except Exception:
            return sys.stdin.readline()

def _listen_anykey():
    try: _getch()
    except Exception: pass
    _start.set()

# ─────────── HEADER (căn giữa 20 cột, chỉ ASCII + box đơn) ───────────
def _header():
    print()
    print(f"  {C.P4}{C.B}--------------------{C.RST}"); time.sleep(0.05)
    print(f"  {C.P4}{C.B}|{C.RST}     {C.P5}{C.B}Z  I  N{C.RST}      {C.P4}{C.B}|{C.RST}"); time.sleep(0.05)
    print(f"  {C.P4}{C.B}--------------------{C.RST}"); time.sleep(0.18)
    print()
    print(f"  {C.Y1}{C.B}  Vô Tận Pháp Lực  {C.RST}"); time.sleep(0.08)
    print(f"  {C.P3}--------------------{C.RST}"); time.sleep(0.08)
    print()
    print(f"  {C.K1}{C.B} > nhấn phím vào tool < {C.RST}"); time.sleep(0.08)
    print(f"  {C.P3}--------------------{C.RST}"); time.sleep(0.08)
    print()

# ═══════════════ 8 ANIMATIONS — ASCII ONLY ═══════════════

def _a_matrix(dur):
    """Mưa ký tự Matrix — head sáng + trail tối dần."""
    cols = W
    heads  = [random.uniform(-H, H) for _ in range(cols)]
    speeds = [random.uniform(0.3, 0.7) for _ in range(cols)]
    glyphs = "01|!@#$%&"
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        for i in range(cols):
            heads[i] += speeds[i]
            if heads[i] >= H + 1.5:
                heads[i] = random.uniform(-1.5, -0.5)
                speeds[i] = random.uniform(0.3, 0.7)
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(cols):
                d = r - heads[i]
                if -0.5 <= d < 0.5:
                    grid[r][i] = (random.choice(glyphs), C.W + C.B)
                elif 0.5 <= d < 1.5:
                    grid[r][i] = (random.choice(glyphs), C.G2)
                elif 1.5 <= d < 2.5:
                    grid[r][i] = (".", C.G1)
        _render(_grid_to_rows(grid))
        time.sleep(0.06)

def _a_sine(dur):
    """Sóng sin 4 dòng lệch pha, density ký tự tăng theo biên độ."""
    chars = " .:-=+*#"
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(W):
                v = math.sin(i * 0.55 - t * 3.5 + r * 1.3)
                if v > 0.1:
                    idx = max(0, min(len(chars)-1, int((v + 1) / 2 * (len(chars)-1))))
                    col = _RB[(i + r * 3 + int(t * 5)) % len(_RB)]
                    grid[r][i] = (chars[idx], col)
        _render(_grid_to_rows(grid))
        time.sleep(0.05)

def _a_ripple(dur):
    """Sóng tròn lan từ tâm — ký tự sáng dần theo vành."""
    cx, cy = W / 2, H / 2
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(W):
                dx, dy = i - cx, (r - cy) * 2
                rad = math.hypot(dx, dy)
                v = math.sin(rad * 1.4 - t * 5)
                if v > 0.55:
                    grid[r][i] = ("*", _RB[int(rad * 4 + t * 6) % len(_RB)] + C.B)
                elif v > 0.15:
                    grid[r][i] = ("+", _RB[int(rad * 4 + t * 6) % len(_RB)])
                elif v > -0.15:
                    grid[r][i] = (".", C.D2)
        _render(_grid_to_rows(grid))
        time.sleep(0.05)

def _a_vortex(dur):
    """Xoáy ốc — góc + bán kính tạo sin xoay, màu theo góc."""
    cx, cy = W / 2, H / 2
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(W):
                dx, dy = i - cx, (r - cy) * 2
                ang, rad = math.atan2(dy, dx), math.hypot(dx, dy)
                v = math.sin(ang * 2 + rad * 0.8 - t * 4.5)
                if v > 0.55:
                    grid[r][i] = ("@", _RB[int(ang * 3 + t * 6) % len(_RB)] + C.B)
                elif v > 0.15:
                    grid[r][i] = ("*", _RB[int(ang * 3 + t * 6) % len(_RB)])
                elif v > -0.15:
                    grid[r][i] = (".", C.D2)
        _render(_grid_to_rows(grid))
        time.sleep(0.05)

def _a_ekg(dur):
    """Nhịp tim EKG — đường nền + chấm sáng chạy + đuôi."""
    mid = H // 2
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for i in range(W):
            grid[mid][i] = (".", C.G1)
        pos = int(t * 14) % W
        for k in range(5):
            p = (pos - k) % W
            if   k == 0: grid[mid][p] = ("*", C.W + C.B)
            elif k == 1: grid[mid][p] = ("+", C.P5)
            elif k == 2: grid[mid][p] = ("+", C.P3)
            elif k == 3: grid[mid][p] = (".", C.G2)
        _render(_grid_to_rows(grid))
        time.sleep(0.05)

def _a_star(dur):
    """Starfield — sao bay ra từ tâm theo z."""
    N = 22
    stars = [[random.uniform(-1, 1), random.uniform(-1, 1),
              random.uniform(0.15, 1.0)] for _ in range(N)]
    cx, cy = W / 2, H / 2
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for s in stars:
            s[2] -= 0.045
            if s[2] <= 0.08:
                s[0] = random.uniform(-1, 1)
                s[1] = random.uniform(-1, 1)
                s[2] = 1.0
            px = int(cx + s[0] * W * 0.5 / s[2])
            py = int(cy + s[1] * H * 0.55 / s[2])
            if 0 <= px < W and 0 <= py < H:
                if   s[2] > 0.6: ch, col = (".", C.D1)
                elif s[2] > 0.3: ch, col = ("+", C.K2)
                else:            ch, col = ("*", C.W)
                grid[py][px] = (ch, col)
        _render(_grid_to_rows(grid))
        time.sleep(0.06)

def _a_dna(dur):
    """Xoắn kép — 2 chuỗi O/0 lệch pha π, cầu nối = khi giao."""
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(W):
                phase = i * 0.5 + r * 0.9 + t * 3.2
                a = math.sin(phase); b = math.sin(phase + math.pi)
                if   a >  0.72: grid[r][i] = ("O", C.P4 + C.B)
                elif b >  0.72: grid[r][i] = ("0", C.K2 + C.B)
                elif abs(a) < 0.3: grid[r][i] = ("=", C.Y1)
                elif a * b > 0: grid[r][i] = (".", C.D2)
        _render(_grid_to_rows(grid))
        time.sleep(0.055)

def _a_plasma(dur):
    """Plasma — 4 sóng sin giao thoa, density ký tự theo giá trị."""
    chars = " .:-=+*#%@"
    t0 = time.time()
    while time.time() - t0 < dur and not _start.is_set():
        t = time.time() - t0
        grid = [[(" ", "") for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for i in range(W):
                v = (math.sin(i * 0.45 + t * 2.6) +
                     math.sin(r * 0.9 - t * 1.8) +
                     math.sin((i + r) * 0.35 + t * 2.2) +
                     math.sin(math.hypot(i - W/2, (r - H/2) * 1.6) * 0.7 - t * 2.4)) / 4
                idx = max(0, min(len(chars)-1, int((v + 1) / 2 * (len(chars)-1))))
                col = _RB[int(i * 0.6 + r * 3 + t * 6) % len(_RB)]
                grid[r][i] = (chars[idx], col)
        _render(_grid_to_rows(grid))
        time.sleep(0.05)

# ─────────── TOOL UTILITIES ───────────
def _boot_step(text, dur=0.7, color=C.K1):
    frames = "|/-\\"
    t0 = time.time(); i = 0
    while time.time() - t0 < dur:
        _w(f"{color}{C.B}{frames[i % 4]}{C.RST} {C.W}{text}{C.RST}")
        i += 1; time.sleep(0.07)
    _w(f"{C.G2}{C.B}+{C.RST} {C.W}{text}{C.RST}"); _end()

def _pulse(text, times=1):
    seq = [C.P1, C.P2, C.P3, C.P4, C.P5, C.P4, C.P3]
    msg = f"= {text} ="
    for _ in range(times):
        for col in seq:
            _w(f"{col}{C.B}{msg}{C.RST}"); time.sleep(0.045)
    _w(f"{C.K2}{C.B}{msg}{C.RST}"); _end()

def _glitch(text, times=3):
    text = text[:24]
    glyphs = "!@#$%&*<>?/\\|"
    for _ in range(times):
        g = "".join(random.choice(glyphs) if random.random() < 0.35 else ch for ch in text)
        _w(f"{C.R2}{C.B}x{C.RST} {C.R1}{g}{C.RST}"); time.sleep(0.06)
    _w(f"{C.R2}{C.B}x{C.RST} {C.R1}{text}{C.RST}"); _end()

def _spinner_wait(sec, label="nghi"):
    sym = "|/-\\"; n = 12
    t0 = time.time(); i = 0
    while True:
        el = time.time() - t0
        if el >= sec: break
        pct = min(el / sec, 1.0); filled = int(n * pct)
        bar = ""
        for k in range(n):
            if k < filled:
                col = C.P5 if k < n * 0.33 else C.P3 if k < n * 0.66 else C.K2
                bar += f"{col}="
            else: bar += f"{C.D3}."
        bar += C.RST
        _w(f"{C.P4}{C.B}{sym[i%4]}{C.RST} {C.D1}{label}{C.RST} [{bar}] {C.W}{int(pct*100):3d}%{C.RST}")
        i += 1; time.sleep(0.07)
    _w(f"{C.G2}{C.B}+{C.RST} {C.D1}{label}{C.RST} {C.G1}{C.B}done{C.RST}"); _end()

def _divider(label=None, col=C.P4):
    if label:
        print(f"  {C.D3}--{C.RST} {col}{C.B}* {label} *{C.RST} {C.D3}--{C.RST}")
    else:
        print(f"  {C.D3}{'-' * 26}{C.RST}")

def _badge(num, text, total=5):
    print()
    print(f"  {C.P5}{C.B}[{num}/{total}]{C.RST}  {C.W}{C.B}{text}{C.RST}")

def _prompt():
    return input(f"  {C.P5}> {C.RST}")

# ─────────── CORE ───────────
def parse_cookies(s):
    return {k.strip(): v.strip()
            for it in s.split(";") if "=" in it
            for k, v in [it.split("=", 1)]}

def extract_dtsg(html):
    pats = [
        r'\["DTSGInitialData",\s*\[\],\s*\{"token":"([^"]+)"',
        r'"DTSGInitialData"[^}]*?"token":"([^"]+)"',
        r'"DTSGInitData"[^}]*?"token":"([^"]+)"',
        r'name="fb_dtsg"\s+value="([^"]+)"',
        r'"token":"(NA[^"]+)"', r'"token":"(AQ[^"]+)"', r'"token":"([^"]+)"',
    ]
    for s in re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', html):
        if "DTSG" in s:
            m = re.search(r'"token":"([^"]+)"', s)
            if m: return m.group(1)
    for p in pats:
        m = re.search(p, html)
        if m: return m.group(1)
    return ""

def get_post_id(session, target):
    target = str(target).strip()
    if target.isdigit(): return target
    m = re.search(r'(?:/posts/|/videos/|/reel/|story_fbid=|fbid=)(\d+)', target)
    if m: return m.group(1)
    try:
        r = session.get(target, allow_redirects=False, timeout=8)
        m = re.search(r'(?:/posts/|/videos/|/reel/|story_fbid=|fbid=)(\d+)',
                      r.headers.get("Location", ""))
        if m: return m.group(1)
    except Exception: pass
    r = session.get(target, allow_redirects=True, timeout=15)
    m = (re.search(r'(?:/posts/|/videos/|/reel/|story_fbid=|fbid=)(\d+)', r.url)
         or re.search(r'"post_id":"(\d+)"', r.text))
    return m.group(1) if m else target

def read_comments_file(path):
    path = path.strip().strip('"').strip("'")
    if not os.path.exists(path): return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception as e:
        _glitch(f"doc file: {e}"); return None

class FBCommenter:
    def __init__(self, cookie_str):
        self.cookie_str = cookie_str.strip()
        self.session = requests.Session()
        self.c_user = self.fb_dtsg = self.jazoest = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1", "Cookie": self.cookie_str,
        }
    def init(self):
        ck = parse_cookies(self.cookie_str)
        self.c_user = ck.get("c_user") or ck.get("i_user")
        if not self.c_user:
            m = re.search(r'(?:c_user|i_user)=(\d+)', self.cookie_str)
            self.c_user = m.group(1) if m else None
        if not self.c_user: raise ValueError("khong co c_user trong cookie")
        for k, v in ck.items():
            self.session.cookies.set(k, v, domain=".facebook.com")
        self.session.headers.update(self.headers)
        page = self.session.get("https://www.facebook.com/", timeout=25)
        self.fb_dtsg = extract_dtsg(page.text)
        if not self.fb_dtsg:
            page = self.session.get("https://m.facebook.com/", timeout=25)
            self.fb_dtsg = extract_dtsg(page.text)
        if not self.fb_dtsg: raise RuntimeError("khong lay duoc fb_dtsg")
        self.jazoest = "2" + str(sum(ord(c) for c in self.fb_dtsg))
        return True
    def send_comment(self, post_id, message, ranges=None, feedback_id=None):
        feedback_id = feedback_id or base64.b64encode(f"feedback:{post_id}".encode()).decode()
        variables = {
            "feedLocation": "NEWSFEED", "feedbackSource": 1, "groupID": None,
            "input": {
                "client_mutation_id": "1", "actor_id": self.c_user,
                "attachments": [], "feedback_id": feedback_id,
                "message": {"ranges": ranges or [], "text": message},
                "reply_comment_parent_fbid": None,
                "is_tracking_encrypted": True, "tracking": [],
                "feedback_source": "NEWS_FEED",
                "idempotence_token": f"client:{uuid.uuid4()}",
                "session_id": str(uuid.uuid4()),
            },
            "scale": 1, "useDefaultActor": False,
        }
        payload = {
            "av": self.c_user, "__user": self.c_user, "__a": "1", "__req": "1",
            "__rev": "1019000000", "fb_dtsg": self.fb_dtsg, "jazoest": self.jazoest,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useCometUFICreateCommentMutation",
            "variables": json.dumps(variables),
            "server_timestamps": "true", "doc_id": "6993516810709754",
        }
        hdrs = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/",
            "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-FB-Friendly-Name": "useCometUFICreateCommentMutation",
        }
        res = self.session.post("https://www.facebook.com/api/graphql/",
                                data=payload, headers=hdrs, timeout=30)
        clean = re.sub(r"^for\s*\(\s*;\s*;\s*\)\s*;\s*", "", res.text.strip())
        try: data = json.loads(clean)
        except Exception: return {"error": "response khong phai JSON", "raw": clean[:200]}
        if isinstance(data, dict) and data.get("errors"):
            return {"error": data["errors"][0].get("message", "unknown")}
        return data

# ─────────── INPUT ───────────
def ask_input():
    _divider("CAU HINH", C.K1)
    _badge(1, "Cookie Facebook (1 dong)")
    cookie = _prompt()
    if not cookie: _glitch("cookie trong"); return None

    _badge(2, "Target (link/ID, cach dau phay)")
    raw_t = _prompt()
    if not raw_t: _glitch("can it nhat 1 target"); return None
    targets = [t.strip() for t in raw_t.split(",") if t.strip()]

    _badge(3, "Duong dan file comments.txt")
    print(f"  {C.D1}VD: /storage/downloads/comments.txt{C.RST}")
    path = _prompt()
    comments = read_comments_file(path)
    if comments is None: _glitch("khong tim thay file"); return None
    if not comments: _glitch("file rong"); return None
    print(f"  {C.G2}*{C.RST} nap {C.W}{C.B}{len(comments)}{C.RST} comment")

    _badge(4, "Delay (giay, so nguyen)")
    raw_d = _prompt()
    try: delay = max(1, int(raw_d))
    except Exception:
        print(f"  {C.Y1}!{C.RST} dung mac dinh 30s"); delay = 30

    _badge(5, "Tag -> Ten|UID (Enter de bo qua)")
    print(f"  {C.D1}VD: Nguyen Van A|100012345678{C.RST}")
    raw_tag = _prompt()
    tag_name, tag_uid = "", ""
    if raw_tag and "|" in raw_tag:
        p = raw_tag.split("|", 1)
        tag_name = p[0].strip().lstrip("@").strip()
        tag_uid = p[1].strip()
    elif raw_tag:
        print(f"  {C.Y1}!{C.RST} thieu dau | -> bo qua tag")

    return {"cookie": cookie, "targets": targets, "comments": comments,
            "delay": delay, "tag_name": tag_name, "tag_uid": tag_uid}

# ─────────── CINEMATIC INTRO ───────────
def cinematic_intro():
    threading.Thread(target=_listen_anykey, daemon=True).start()
    _header()
    while not _start.is_set():
        _a_matrix(2.0)
        if _start.is_set(): break
        _a_sine(2.0)
        if _start.is_set(): break
        _a_ripple(2.0)
        if _start.is_set(): break
        _a_vortex(2.0)
        if _start.is_set(): break
        _a_ekg(2.0)
        if _start.is_set(): break
        _a_star(2.2)
        if _start.is_set(): break
        _a_dna(2.0)
        if _start.is_set(): break
        _a_plasma(2.2)
        if _start.is_set(): break
    # cursor đang ở đầu dòng dưới canvas
    print()
    _pulse("vao tool", 1)
    print()

# ─────────── MAIN ───────────
def main():
    os.system("cls" if os.name == "nt" else "clear")
    cinematic_intro()

    _boot_step("khoi dong loi ZIN", 0.6, C.P4)
    _boot_step("nap module network", 0.5, C.K1)
    _boot_step("san sang", 0.3, C.G2)

    cfg = ask_input()
    if not cfg: return

    tag_name, tag_uid = cfg["tag_name"], cfg["tag_uid"]
    has_tag = bool(tag_name and tag_uid)
    tag_text = f"@{tag_name}" if has_tag else ""
    total = len(cfg["targets"]) * len(cfg["comments"])

    _divider("XAC NHAN", C.P5)
    print(f"  {C.K2}>{C.RST} Targets : {C.W}{C.B}{len(cfg['targets'])}{C.RST}")
    print(f"  {C.K2}>{C.RST} Comments: {C.W}{C.B}{len(cfg['comments'])}{C.RST}")
    print(f"  {C.K2}>{C.RST} Delay   : {C.W}{C.B}{cfg['delay']}s{C.RST}")
    if has_tag:
        print(f"  {C.K2}>{C.RST} Tag     : {C.P4}@{tag_name}{C.RST}")
    else:
        print(f"  {C.K2}>{C.RST} Tag     : {C.D1}khong{C.RST}")
    print(f"  {C.K2}>{C.RST} Tong cmt: {C.Y1}{C.B}{total}{C.RST}")
    print(f"  {C.D3}{'-' * 26}{C.RST}")

    if input(f"  {C.Y1}> chay? (y/n): {C.RST}").strip().lower() != "y":
        _pulse("da huy", 1); return

    _divider("KET NOI", C.K1)
    _boot_step("mo session", 0.8, C.B3)
    fb = FBCommenter(cfg["cookie"])
    try:
        fb.init()
    except Exception as e:
        _glitch(f"init: {e}"); return
    _pulse(f"login OK - {fb.c_user}", 1)
    print()

    _divider("CHAY", C.G2)
    idx = ok = fail = 0
    delay = cfg["delay"]

    for target in cfg["targets"]:
        try:
            post_id = get_post_id(fb.session, target)
            print(f"  {C.K2}*{C.RST} post_id {C.W}{C.B}{post_id}{C.RST}")
        except Exception as e:
            _glitch(f"bo qua target: {e}"); continue

        fb_id = base64.b64encode(f"feedback:{post_id}".encode()).decode()

        for cmt in cfg["comments"]:
            idx += 1
            if has_tag:
                msg = f"{tag_text} {cmt}"
                ranges = [{"entity": {"id": tag_uid}, "offset": 0, "length": len(tag_text)}]
            else:
                msg = cmt; ranges = []

            print(f"  {C.P4}>{C.RST} {C.D1}[{idx}/{total}]{C.RST} {C.W}{msg[:40]}{C.RST}")
            try:
                res = fb.send_comment(post_id, msg, ranges=ranges, feedback_id=fb_id)
                if isinstance(res, dict) and res.get("error"):
                    fail += 1; _glitch(res["error"], 2)
                else:
                    ok += 1
                    print(f"  {C.G2}*{C.RST} {C.G1}{C.B}da gui{C.RST}")
            except Exception as e:
                fail += 1; _glitch(f"exception: {e}", 2)

            if idx < total:
                _spinner_wait(delay, "nghi")

    print()
    _divider("KET QUA", C.P5)
    print(f"  {C.G2}*{C.RST} thanh cong: {C.G1}{C.B}{ok}{C.RST}")
    print(f"  {C.R2}x{C.RST} that bai  : {C.R1}{C.B}{fail}{C.RST}")
    print(f"  {C.K2}*{C.RST} tong      : {C.W}{C.B}{total}{C.RST}")
    print(f"  {C.D3}{'-' * 26}{C.RST}")
    _pulse("hoan tat", 1)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {C.R2}| dung{C.RST}\n")