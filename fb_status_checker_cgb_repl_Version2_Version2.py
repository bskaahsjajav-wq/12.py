#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fb_status_checker_cgb_repl_Version2.py
CGB - Công cụ kiểm tra trạng thái Facebook (REPL)
- Chạy: python3 fb_status_checker_cgb_repl_Version2.py
- Hoặc: python3 fb_status_checker_cgb_repl_Version2.py "UID_or_URL"  (chạy 1 lần rồi exit)
Yêu cầu: Python 3.8+, pip install requests beautifulsoup4
Bản quyền: CGB (2026)
"""
from __future__ import annotations
import re
import sys
import json
import argparse
from typing import Optional, Tuple

# Thử import; nếu thiếu, báo rõ cho user cài
try:
    import requests
    from bs4 import BeautifulSoup
except Exception as e:
    sys.stderr.write("Thiếu module. Chạy:\n  python3 -m pip install requests beautifulsoup4\n")
    sys.exit(1)

from urllib.parse import urlparse, parse_qs

# ------------------ Cấu hình ------------------
USER_AGENT = "Mozilla/5.0 (CGB FBChecker)"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "vi-VN,vi;q=0.9"}
REQUEST_TIMEOUT = 12

# Open patterns (mở rộng để dò nhiều trạng thái)
PHRASES = {
    "disabled": [
        "this account has been disabled", "account disabled", "tài khoản đã bị vô hiệu hóa",
        "tài khoản bị vô hiệu hóa", "account deactivated", "deactivated account",
        "đã bị vô hiệu hóa"
    ],
    "content_unavailable": [
        "this content isn't available", "this content isn't available right now",
        "nội dung này không khả dụng", "the link you followed may be broken"
    ],
    "checkpoint": [
        "confirm your identity", "security check", "we noticed unusual activity",
        "we detected", "checkpoint", "xác minh danh tính", "security checkpoint"
    ],
    "login_required": [
        "log in to facebook", "please log in", "you must log in", "đăng nhập facebook",
        "vui lòng đăng nhập"
    ],
    "page_indicators": [
        "people who like this", "about ·", "page ·", "likes ·", "fan page"
    ],
    "memorialized": [
        "remembering", "in memory of", "để tưởng nhớ", "đã qua đời", "this timeline is no longer available"
    ],
    "age_restricted": [
        "you must be at least", "age restricted", "tuổi", "phải đủ tuổi"
    ],
    "limited": [
        "limited functionality", "has limited access", "giới hạn"
    ],
    "verification_required": [
        "verification required", "verify your account", "xác minh tài khoản"
    ],
    "policy_violation": [
        "violat", "policy", "vi phạm chính sách", "disagree with our community standards"
    ],
    "two_factor": [
        "two-factor", "two step", "xác thực hai yếu tố", "two step verification"
    ],
    "suspended": [
        "suspended", "tạm ngưng", "suspension"
    ],
}

# Danh sách mã trạng thái (mở rộng). Key = số mã do bạn quy ước.
STATUS_CODE_MAP = {
    100: ("active_public", "Hoạt động công khai"),
    110: ("private_login", "Riêng tư - cần đăng nhập"),
    120: ("page", "Trang (Page) chứ không phải profile cá nhân"),
    200: ("disabled", "Bị vô hiệu hóa (không rõ thời hạn)"),
    281: ("disabled_30d", "Bị vô hiệu hóa ~30 ngày"),
    282: ("disabled_180d", "Bị vô hiệu hóa ~180 ngày"),
    283: ("disabled_365d", "Bị vô hiệu hóa ~365 ngày"),
    250: ("checkpoint", "Checkpoint - cần xác minh"),
    251: ("checkpoint_sms", "Checkpoint - gợi ý SMS"),
    252: ("checkpoint_id", "Checkpoint - gợi ý ID"),
    260: ("verification_required", "Cần xác minh (verification)"),
    270: ("two_factor_required", "Yêu cầu xác thực 2 lớp"),
    300: ("content_unavailable", "Nội dung không khả dụng / bị gỡ"),
    310: ("memorialized", "Tưởng niệm (Memorialized)"),
    320: ("age_restricted", "Giới hạn độ tuổi"),
    330: ("limited", "Tài khoản bị giới hạn chức năng"),
    340: ("policy_violation", "Bị giới hạn/khóa do vi phạm chính sách"),
    404: ("not_found", "Không tìm thấy (404)"),
    900: ("unknown", "Không rõ / Không đủ dữ liệu"),
}

# Dò thời hạn như yêu cầu: 30d, 180d, 365d
DURATION_REGEX = re.compile(r"(\d{1,4})\s*(day|days|ngày|month|months|tháng|year|years|năm)", re.IGNORECASE)

# ------------------ Hàm hỗ trợ ------------------
def cgb_banner() -> str:
    # ANSI màu cho banner rực rỡ
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    MAG = "\033[95m"
    YEL = "\033[93m"
    RESET = "\033[0m"
    art = r"""
   ____  ____  ____ 
  / ___||  _ \| __ )
  \___ \| |_) |  _ \
   ___) |  __/| |_) |
  |____/|_|   |____/ 
    """
    header = (
        f"{CYAN}{art}{RESET}\n"
        f"{MAG}  Tool bởi  ☯  CGB  ☯{RESET}\n"
        + "=" * 50 + "\n"
        + f"{YEL}  Bản quyền thuộc về CGB  ·  Phiên bản 2.0{RESET}\n"
        + "=" * 50 + "\n"
    )
    return header

def extract_key(raw: str) -> Tuple[Optional[str], Optional[str]]:
    raw = raw.strip()
    if re.fullmatch(r"\d{5,}", raw):
        return raw, "id"
    try:
        parsed = urlparse(raw)
        if parsed.netloc:
            path = (parsed.path or "").strip("/")
            if "profile.php" in parsed.path:
                qs = parse_qs(parsed.query)
                if "id" in qs and qs["id"]:
                    return qs["id"][0], "id"
            if not path:
                return raw, "url"
            first = path.split("/")[0]
            if re.fullmatch(r"\d{5,}", first):
                return first, "id"
            return first, "username"
    except Exception:
        pass
    if " " not in raw and raw:
        return raw, "username"
    return None, None

def build_mobile_url(key: str, kind: str) -> str:
    if kind == "id":
        return f"https://m.facebook.com/profile.php?id={key}"
    if kind == "username":
        return f"https://m.facebook.com/{key}"
    return key

def fetch_url(url: str) -> Tuple[int, str, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        return r.status_code, r.url, r.text or ""
    except requests.RequestException as e:
        return 0, url, f"__error__:{e}"

def analyze_html(html: str) -> dict:
    low = html.lower()
    detections = {}
    for label, phrases in PHRASES.items():
        for ph in phrases:
            if ph in low:
                detections.setdefault(label, []).append(ph)
    try:
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string.strip() if soup.title and soup.title.string else "").lower()
        if title:
            for label, phrases in PHRASES.items():
                for ph in phrases:
                    if ph in title:
                        detections.setdefault(f"title_{label}", []).append(ph)
        meta_og = soup.find("meta", {"property": "og:type"})
        if meta_og and meta_og.get("content"):
            detections.setdefault("og_type", []).append(meta_og["content"].lower())
        # Search short text sample
        text_sample = " ".join([t.strip().lower() for t in soup.stripped_strings][:200])
        for label, phrases in PHRASES.items():
            for ph in phrases:
                if ph in text_sample:
                    detections.setdefault(f"sample_{label}", []).append(ph)
    except Exception:
        pass
    return detections

def detect_duration_for_disabled(text: str) -> Optional[int]:
    low = text.lower()
    for m in DURATION_REGEX.finditer(low):
        n = int(m.group(1)); unit = m.group(2)
        if "month" in unit or "tháng" in unit:
            n_days = n * 30
        elif "year" in unit or "năm" in unit:
            n_days = n * 365
        else:
            n_days = n
        if 25 <= n_days <= 35:
            return 281
        if 150 <= n_days <= 210:
            return 282
        if 350 <= n_days <= 380:
            return 283
    return None

def assign_status_code(detections: dict, http_status: int, final_url: str, html_text: str) -> Tuple[int, str]:
    # Quy tắc xác định trạng thái (theo thứ tự ưu tiên)
    if http_status == 404:
        return 404, "Không tìm thấy (HTTP 404)"
    if "memorialized" in detections or "sample_memorialized" in detections:
        return 310, "Timeline bị tưởng niệm (Memorialized)"
    if "content_unavailable" in detections:
        return 300, "Nội dung không khả dụng hoặc bị gỡ"
    if "disabled" in detections or "title_disabled" in detections or "sample_disabled" in detections:
        dur_code = detect_duration_for_disabled(html_text)
        if dur_code:
            return dur_code, f"Phát hiện vô hiệu hóa, mapping -> mã {dur_code}"
        return 200, "Tài khoản bị vô hiệu hóa (không rõ thời hạn)"
    if "policy_violation" in detections or "sample_policy_violation" in detections:
        return 340, "Giới hạn/khóa do vi phạm chính sách"
    if "checkpoint" in detections or "title_checkpoint" in detections or "sample_checkpoint" in detections:
        low = html_text.lower()
        if "sms" in low or "số điện thoại" in low:
            return 251, "Checkpoint - gợi ý SMS"
        if "identify" in low or "id" in low or "giấy tờ" in low or "xác minh" in low:
            return 252, "Checkpoint - gợi ý ID"
        return 250, "Checkpoint - cần xác minh"
    if "verification_required" in detections or "sample_verification_required" in detections:
        return 260, "Cần xác minh thông tin (verification)"
    if "two_factor" in detections or "sample_two_factor" in detections:
        return 270, "Yêu cầu xác thực 2 lớp"
    if "age_restricted" in detections or "sample_age_restricted" in detections:
        return 320, "Giới hạn độ tuổi"
    if "limited" in detections or "sample_limited" in detections:
        return 330, "Tài khoản đang bị giới hạn chức năng"
    if "login_required" in detections or ("login.php" in final_url and http_status in (200, 302)):
        return 110, "Cần đăng nhập để xem (private / login_required)"
    # Page detection
    if "page_indicators" in detections or ("og_type" in detections and any("page" in s for s in detections.get("og_type", []))):
        return 120, "Đây là Page (Trang), không phải profile cá nhân"
    # fallback
    return 100, "Hoạt động / công khai (không phát hiện vấn đề rõ ràng)"

def pretty_print_result(res: dict):
    # In kết quả bằng tiếng Việt, kèm JSON
    print("\n" + "-" * 50)
    print(f"MÃ TRẠNG THÁI: {res.get('status_code')}  -  {res.get('status_label')}")
    print(f"MÔ TẢ: {res.get('status_description')}")
    print(f"NGUYÊN NHÂN (heuristic): {res.get('reason')}")
    print("-" * 50)
    # Chi tiết detections & url
    print(f"URL kiểm tra: {res.get('checked_url')} (HTTP {res.get('http_status')})")
    print("Các phát hiện (detections):")
    try:
        print(json.dumps(res.get('detections', {}), ensure_ascii=False, indent=2))
    except Exception:
        print(res.get('detections'))
    print("-" * 50 + "\n")

# ------------------ Chạy 1 lần ------------------
def check_once(input_str: str) -> dict:
    key, kind = extract_key(input_str)
    if not key:
        return {"error": "Không parse được uid/url"}
    url = build_mobile_url(key, kind)
    status_code, final_url, html = fetch_url(url)
    if html.startswith("__error__:"):
        detections = {"request_error": [html]}
    else:
        detections = analyze_html(html)
    code, reason = assign_status_code(detections, status_code, final_url, html)
    label, desc = STATUS_CODE_MAP.get(code, (f"code_{code}", "Không rõ"))
    out = {
        "cgb_banner": "CGB",
        "input": input_str,
        "parsed_key": key,
        "kind": kind,
        "checked_url": final_url,
        "http_status": status_code,
        "detections": detections,
        "status_code": code,
        "status_label": label,
        "status_description": desc,
        "reason": reason,
    }
    return out

# ------------------ REPL ------------------
def repl():
    # In banner đẹp (màu) và menu tiếng Việt, KHÔNG in log thêm
    print(cgb_banner())
    print("Nhập UID hoặc URL để kiểm tra. Gõ 'exit' hoặc 'quit' để thoát.")
    try:
        while True:
            s = input("CGB> ").strip()
            if not s:
                continue
            if s.lower() in ("exit", "quit"):
                print("Thoát. CGB.")
                break
            result = check_once(s)
            if "error" in result:
                print("Lỗi:", result["error"])
                continue
            # In kết quả ngắn gọn + JSON chi tiết
            pretty_print_result(result)
            print("JSON chi tiết:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (KeyboardInterrupt, EOFError):
        print("\nThoát. CGB.")

# ------------------ CLI ------------------
def main():
    parser = argparse.ArgumentParser(description="CGB - FB Status Checker REPL (Tiếng Việt)")
    parser.add_argument("input", nargs="?", help="(Tùy chọn) UID hoặc URL để kiểm tra 1 lần và exit")
    args = parser.parse_args()
    if args.input:
        print(cgb_banner())
        r = check_once(args.input)
        if "error" in r:
            print("Lỗi:", r["error"])
            sys.exit(1)
        pretty_print_result(r)
        print("JSON chi tiết:")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    repl()

if __name__ == "__main__":
    main()