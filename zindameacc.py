#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIN THIÊN ĐẠO - Dame Page & Profile Edition
Firefox + VNC | Termux | SIÊU TỐC
Version 6.4 - Fix Celebrity Flow + Sorry-Dialog DIE Detection (5 retries)
"""

import os
import sys
import time
import subprocess
import shutil
from datetime import datetime

# ===== BẮT BUỘC =====
os.environ['DISPLAY'] = ':1'
os.environ['SE_OFFLINE'] = 'true'
os.environ['MOZ_HEADLESS'] = '1'

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    C = {
        "reset": Style.RESET_ALL, "bold": Style.BRIGHT, "dim": Style.DIM,
        "red": Fore.RED, "green": Fore.GREEN, "yellow": Fore.YELLOW,
        "blue": Fore.BLUE, "magenta": Fore.MAGENTA, "cyan": Fore.CYAN,
        "white": Fore.WHITE
    }
except ImportError:
    C = {k: "" for k in ["reset","bold","dim","red","green","yellow",
                          "blue","magenta","cyan","white"]}

# ================== CẤU HÌNH SIÊU TỐC ==================
GECKODRIVER_PATH = "/data/data/com.termux/files/usr/bin/geckodriver"
BASE_DELAY = 0.5
INPUT_DELAY = 1.2
WAIT_FOR_ACTION = 1.2
DONE_DELAY = 0.1
SOMETHING_RETRIES = 5
MAX_RETRIES = 4
INTER_REPORT_DELAY = 0.4
CYCLE_REST = 10

# ================== DIE DETECTION ==================
TARGET_DIED = False          # Set True khi phát hiện page đã die
SORRY_STREAK = 0             # Số report liên tiếp gặp dialog lỗi
SORRY_THRESHOLD = 7          # Ngưỡng để xác nhận DIE

DIE_DIALOG_SIGNALS = [
    "sorry, something went wrong",
    "we're sorry, there's a technical problem",
    "there's a technical problem with this feature",
    "technical problem with this feature",
    "xin lỗi, đã xảy ra lỗi",
    "đã xảy ra sự cố",
    "có lỗi kỹ thuật",
    "chúng tôi đang khắc phục",
]

# ================== BLACKLIST ==================
BLACKLIST_TEXT = [
    "share now",
    "share to feed",
    "share to your story",
    "chia sẻ ngay",
    "chia sẻ lên",
    "send to friends",
    "send in messenger",
    "gửi cho bạn bè",
    "gửi qua messenger",
    "post to profile",
    "đăng lên trang cá nhân"
]

# ================== ĐA NGÔN NGỮ ==================
LANG = {
    "menu": [
        "Profile settings see more options",
        "Page settings see more options",
        "Profile settings",
        "Page settings",
        "その他のオプション",
        "その他のアクション",
        "プロフィール設定のその他のオプション",
        "More options",
        "See more options",
        "More",
        "Xem thêm tùy chọn",
        "Tùy chọn khác",
        "Thêm tùy chọn",
        "Cài đặt trang cá nhân xem thêm tùy chọn",
        "Cài đặt trang xem thêm tùy chọn",
        "Xem thêm tùy chọn trang cá nhân",
        "Xem thêm tùy chọn trang"
    ],
    "reportProfile": [
        "Report profile", "Báo cáo trang cá nhân",
        "プロフィールを報告",
        "प्रोफाइल रिपोर्ट गर्नुहोस्",
        "प्रोफ़ाइल की रिपोर्ट करें"
    ],
    "reportPage": [
        "Report page", "Report Page",
        "Báo cáo trang", "Báo cáo Trang",
        "ページを報告", "ページの報告",
        "पेज रिपोर्ट गर्नुहोस्", "पेज की रिपोर्ट करें"
    ],
    "somethingAbout": [
        "Something about this profile",
        "Something about this page",
        "Có gì đó về trang cá nhân này",
        "Có gì đó về trang này",
        "このプロフィールに関すること",
        "このページに関すること",
        "यो प्रोफाइलका बारेमा केही कुरा",
        "यस पेजको बारेमा केही कुरा",
        "इस प्रोफ़ाइल के बारे में कुछ जानकारी",
        "इस पेज के बारे में कुछ जानकारी"
    ],
    "fakeProfile": [
        "Fake profile", "Fake Page", "Fake account", "Fake business",
        "Trang cá nhân giả mạo", "Trang giả mạo", "Tài khoản giả mạo",
        "Doanh nghiệp giả mạo", "Mạo danh", "Giả mạo",
        "Pretending to be", "Impersonation",
        "なりすまし", "偽プロフィール", "偽ページ",
        "नक्कली प्रोफाइल", "नक्कली पेज", "नक्कली खाता",
        "फ़र्ज़ी प्रोफ़ाइल", "फ़र्ज़ी पेज", "फ़र्ज़ी खाता"
    ],
    "celebrity": [
        "celebrity", "public figure", "A celebrity or public figure",
        "Người nổi tiếng", "nhân vật công chúng",
        "Người nổi tiếng hoặc nhân vật công chúng",
        "有名人", "著名人", "有名人・著名人",
        "सेलिब्रेटी", "प्रसिद्ध व्यक्ति",
        "सेलिब्रिटी", "सार्वजनिक हस्ती"
    ],
    "notRealPerson": [
        "not a real person", "real person",
        "không phải người thật",
        "実在しない人物である",
        "उहाँ वास्तविक व्यक्ति होइन",
        "ये कोई असली व्यक्ति नहीं है"
    ],
    "under18": [
        "under 18", "involving someone", "dưới 18",
        "18歳未満の人物が関わる問題",
        "18 वर्षभन्दा कम उमेरको कोही संलग्न भएको समस्या",
        "यह 18 साल से कम उम्र के किसी व्यक्ति की समस्या से संबंधित है"
    ],
    "physicalAbuse": [
        "Physical abuse", "Bạo hành thể chất", "身体的虐待",
        "शारीरिक दुर्व्यवहार",
        "यह शारीरिक दुर्व्यवहार से संबंधित है"
    ],
    "violent": [
        "Violent", "hateful", "disturbing", "Bạo lực",
        "暴力的、不快、または悪意があるコンテンツ",
        "हिंसात्मक, घृणापूर्ण वा बाधा पुर्‍याउने सामग्री",
        "इसमें हिंसक, नफ़रत फैलाने वाला या असहज करने वाला कंटेंट है"
    ],
    "credibleThreat": [
        "Credible threat", "threat to safety", "Đe dọa đáng tin",
        "信頼できる脅威", "脅迫", "暴力の脅威",
        "सुरक्षामा प्रमाणिक खतरा",
        "यह सुरक्षा के लिए गंभीर खतरा है"
    ],
    "scamFraud": [
        "Scam", "fraud", "false information", "Lừa đảo",
        "詐欺または虚偽の情報",
        "स्क्याम, ठगी वा झुटो जानकारी",
        "यह स्कैम, धोखाधड़ी या गलत जानकारी है"
    ],
    "fraudOrScam": [
        "Fraud or scam", "Lừa đảo hoặc gian lận",
        "詐欺行為", "ठगी वा स्क्याम",
        "धोखाधड़ी या स्कैम"
    ],
    "spam": ["Spam", "Tin rác", "スパム", "स्प्याम", "स्पैम"],
    "somethingElse": [
        "Something else", "Điều gì đó khác",
        "अरू केही", "कोई और समस्या है",
        "その他", "その他の問題", "その他の理由"
    ],
    "suicideOrSelfHarm": [
        "Suicide or self-harm", "自殺または自傷行為",
        "आत्महत्या वा आफैलाई चोट पुर्‍याउने",
        "यह आत्महत्या या खुद को नुकसान पहुँचाने से संबंधित है"
    ],
    "eatingDisorder": [
        "Eating disorder", "摂食障害",
        "खानपानसम्बन्धी विकार", "भोजन संबंधी विकार"
    ],
    "adultContent": [
        "Adult content", "成人向けコンテンツ",
        "वयस्क सामग्री", "इसमें अश्लील कंटेंट है"
    ],
    "adultProstitution": [
        "Seems like prostitution", "売春だと思われる",
        "वेश्यावृत्ति जस्तो देखिन्छ",
        "यह कंटेंट वेश्यावृत्ति जैसा लग रहा है"
    ],
    "harassment": [
        "Bullying or harassment", "いじめまたは嫌がらせ",
        "डरधम्की वा दुर्व्यवहार",
        "यह कंटेंट धमकाने या उत्पीड़न करने से संबंधित है"
    ],
    "terrorism": [
        "Seems like terrorism", "テロリズムだと思われる",
        "आतङ्कवाद जस्तो देखिन्छ",
        "यह आतंकवाद जैसा लग रहा है"
    ],
    "callingForViolence": [
        "Calling for violence", "暴力を呼びかけている",
        "हिंसाका लागि आह्वान",
        "इसमें लोगों को हिंसा करने के लिए उकसाया गया है"
    ],
    "organizedCrime": [
        "Seems like organized crime", "組織的犯罪と思われる",
        "सङ्गठित अपराध जस्तो देखिन्छ",
        "संगठित अपराध जैसा लग रहा है"
    ],
    "submit": ["Submit", "Gửi", "Send", "送信", "पेस गर्नुहोस्", "सबमिट करें"],
    "next": ["Next", "Tiếp", "Tiếp tục", "次へ", "अर्को", "आगे बढ़ें"],
    "done": ["Done", "Xong", "Hoàn tất", "Close", "Đóng", "完了", "सम्पन्न भयो", "ओके"]
}

REPORT_MODE = "auto"

# ================== UI ==================
def print_banner():
    os.system('clear')
    print(f"""{C['cyan']}{C['bold']}
    ███████╗██╗███╗   ██╗
    ╚══███╔╝██║████╗  ██║
      ███╔╝ ██║██╔██╗ ██║
     ███╔╝  ██║██║╚██╗██║
    ███████╗██║██║ ╚████║
    ╚══════╝╚═╝╚═╝  ╚═══╝{C['reset']}
{C['yellow']}  ━━━━━━ ZIN THIÊN ĐẠO - VĨNH HẰNG CHÍ TÔN ━━━━━━{C['reset']}
{C['magenta']}        Firefox + VNC | Termux | SIÊU TỐC{C['reset']}
{C['dim']}  ⚡ Version 6.4 | 🔱 DIE Detection + Celebrity Fix{C['reset']}
""")

def log(msg, color="white", icon="•"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C['dim']}[{ts}]{C['reset']} {C[color]}{icon} {msg}{C['reset']}")

def hr(char="─", width=60, color="cyan"):
    print(f"{C[color]}{char * width}{C['reset']}")

# ================== SELENIUM ==================
def sleep(sec):
    time.sleep(sec)

def _is_blacklisted(el):
    try:
        t = (el.text or "").lower().strip()
        a = (el.get_attribute('aria-label') or "").lower().strip()
        combined = (t + " " + a).strip()
        for b in BLACKLIST_TEXT:
            if t == b or a == b:
                return True
            if len(combined) < len(b) + 15 and b in combined:
                return True
    except Exception:
        pass
    return False

def find_by_keywords(driver, keywords, timeout=4, exact=False,
                     prefer_dialog=False, dialog_only=False):
    end = time.time() + timeout
    kw_lower = [k.lower() for k in keywords]

    while time.time() < end:
        scopes = []
        if prefer_dialog or dialog_only:
            try:
                for d in driver.find_elements(By.CSS_SELECTOR,
                                              '[role="dialog"], [role="alertdialog"]'):
                    if d.is_displayed():
                        scopes.append(d)
            except Exception:
                pass
            if not scopes and dialog_only:
                sleep(0.15)
                continue

        if not scopes:
            scopes = [driver]

        for scope in scopes:
            # CÁCH 1: aria-label
            for kw in kw_lower:
                try:
                    kw_esc = kw.replace("'", "\\'")
                    if exact:
                        xpath = (f".//*[translate(@aria-label,"
                                 "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                 f"'abcdefghijklmnopqrstuvwxyz')='{kw_esc}']")
                    else:
                        xpath = (f".//*[contains(translate(@aria-label,"
                                 "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                 f"'abcdefghijklmnopqrstuvwxyz'),'{kw_esc}')]")
                    for el in scope.find_elements(By.XPATH, xpath):
                        try:
                            if not el.is_displayed():
                                continue
                            if _is_blacklisted(el):
                                continue
                            return el
                        except Exception:
                            continue
                except Exception:
                    pass

            # CÁCH 2: text trong button/menuitem
            for kw in kw_lower:
                try:
                    kw_esc = kw.replace("'", "\\'")
                    if exact:
                        xpath = (".//*[@role='button' or @role='menuitem' or "
                                 "@role='option' or @role='link']"
                                 "[translate(normalize-space(string(.)),"
                                 "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                 f"'abcdefghijklmnopqrstuvwxyz')='{kw_esc}']")
                    else:
                        xpath = (".//*[@role='button' or @role='menuitem' or "
                                 "@role='option' or @role='link']"
                                 "[contains(translate(.,"
                                 "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                                 "'abcdefghijklmnopqrstuvwxyz'),"
                                 f"'{kw_esc}')]")
                    for el in scope.find_elements(By.XPATH, xpath):
                        try:
                            if not el.is_displayed():
                                continue
                            if _is_blacklisted(el):
                                continue
                            return el
                        except Exception:
                            continue
                except Exception:
                    pass

        sleep(0.15)
    return None

def safe_click(driver, el, highlight=True):
    if not el:
        return False
    try:
        role = el.get_attribute('role')
        if role not in ('button', 'link', 'menuitem', 'option'):
            try:
                parent = el.find_element(
                    By.XPATH,
                    "ancestor-or-self::*[@role='button' or @role='link' "
                    "or @role='menuitem' or @role='option'][1]")
                if parent:
                    el = parent
            except Exception:
                pass
    except Exception:
        pass

    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center',inline:'center'});", el)
        if highlight:
            driver.execute_script(
                "arguments[0].style.outline='3px solid #FF1493';"
                "arguments[0].style.outlineOffset='2px';", el)
        sleep(0.1)
        el.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False

def get_report_keywords():
    if REPORT_MODE == "page":
        return LANG["reportPage"]
    if REPORT_MODE == "profile":
        return LANG["reportProfile"]
    return LANG["reportPage"] + LANG["reportProfile"]

# ================== DIE DIALOG DETECTION ==================
def close_sorry_dialog(driver):
    """Đóng dialog 'Sorry, something went wrong'."""
    try:
        for d in driver.find_elements(By.CSS_SELECTOR,
                                       '[role="dialog"], [role="alertdialog"]'):
            if not d.is_displayed():
                continue
            t = (d.text or "").lower()
            if ("sorry" in t or "technical problem" in t
                    or "đã xảy ra lỗi" in t or "đã xảy ra sự cố" in t):
                # Tìm nút Close
                for xpath in [
                    ".//*[@aria-label='Close' or @aria-label='Đóng' or @aria-label='閉じる']",
                    ".//*[@aria-label='close']",
                    ".//div[@role='button'][contains(.,'Close') or contains(.,'Đóng') or contains(.,'OK') or contains(.,'閉じる')]",
                    ".//*[contains(@aria-label,'close')]",
                ]:
                    try:
                        el = d.find_element(By.XPATH, xpath)
                        if el.is_displayed():
                            safe_click(driver, el, highlight=False)
                            sleep(0.5)
                            return True
                    except Exception:
                        pass
    except Exception:
        pass
    return False

def check_sorry_dialog(driver):
    """Phát hiện dialog lỗi kỹ thuật — dấu hiệu page DIE."""
    try:
        # Check dialog cụ thể
        for d in driver.find_elements(By.CSS_SELECTOR,
                                       '[role="dialog"], [role="alertdialog"]'):
            if not d.is_displayed():
                continue
            t = (d.text or "").lower()
            for sig in DIE_DIALOG_SIGNALS:
                if sig in t:
                    return True

        # Fallback: check page source
        src = (driver.page_source or "").lower()
        for sig in DIE_DIALOG_SIGNALS:
            if sig in src:
                return True
    except Exception:
        pass
    return False

# ================== ACTIONS ==================
def click_menu(driver):
    el = find_by_keywords(driver, LANG["menu"], timeout=8)
    if el:
        safe_click(driver, el)
        sleep(BASE_DELAY)
        return True

    try:
        for el in driver.find_elements(By.XPATH,
                "//*[contains(@aria-label,'see more options') or "
                "contains(@aria-label,'その他のオプション')]"):
            if el.is_displayed():
                safe_click(driver, el)
                sleep(BASE_DELAY)
                return True
    except Exception:
        pass

    try:
        for el in driver.find_elements(By.XPATH,
                "//div[@role='button'][.//*[local-name()='svg']]"):
            try:
                al = (el.get_attribute('aria-label') or '').lower()
                if ('more' in al or 'option' in al or '設定' in al
                        or 'tùy chọn' in al or 'xem thêm' in al):
                    if el.is_displayed():
                        safe_click(driver, el)
                        sleep(BASE_DELAY)
                        return True
            except Exception:
                continue
    except Exception:
        pass

    return False

def click_report_entry(driver):
    kws = get_report_keywords()
    for _ in range(10):
        el = find_by_keywords(driver, kws, timeout=2, prefer_dialog=True)
        if el:
            safe_click(driver, el)
            sleep(0.8)
            return True
        sleep(0.3)
    return False

def click_something_about(driver):
    for _ in range(SOMETHING_RETRIES):
        el = find_by_keywords(driver, LANG["somethingAbout"], timeout=2,
                              prefer_dialog=True)
        if el:
            safe_click(driver, el)
            sleep(BASE_DELAY + 0.3)
            return True

        try:
            for el in driver.find_elements(By.XPATH,
                    "//*[contains(translate(.,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),'about this') or "
                    "contains(.,'về trang này') or "
                    "contains(.,'về trang cá nhân này') or "
                    "contains(.,'このページ') or "
                    "contains(.,'このプロフィール')]"):
                if el.is_displayed() and el.tag_name in ('div', 'span', 'a'):
                    try:
                        clickable = el.find_element(By.XPATH,
                            "ancestor-or-self::*[@role='button' or "
                            "@role='menuitem' or @role='link'][1]")
                        if clickable and clickable.is_displayed():
                            safe_click(driver, clickable)
                            sleep(BASE_DELAY + 0.3)
                            return True
                    except Exception:
                        continue
        except Exception:
            pass

        try:
            driver.execute_script("window.scrollBy(0, 200);")
        except Exception:
            pass
        sleep(0.4)
    return False

def click_something_else(driver):
    for _ in range(MAX_RETRIES + 2):
        el = find_by_keywords(driver, LANG["somethingElse"], timeout=2,
                              prefer_dialog=True)
        if el:
            safe_click(driver, el)
            sleep(1.0)
            return True
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except Exception:
            pass
        sleep(0.3)
    return False

def click_meta_result(driver):
    for _ in range(4):
        try:
            for opt in driver.find_elements(By.CSS_SELECTOR,
                                             'div[role="listbox"] span, ul[role="listbox"] span'):
                if opt.is_displayed() and opt.text.strip() == "Meta":
                    safe_click(driver, opt)
                    sleep(0.8)
                    return True
            imgs = driver.find_elements(By.CSS_SELECTOR, 'div[role="listbox"] img')
            if imgs:
                safe_click(driver, imgs[0])
                sleep(0.8)
                return True
        except Exception:
            pass
        sleep(0.4)
    return False

def input_meta_name(driver):
    try:
        inp = driver.find_element(
            By.XPATH,
            "//input[contains(@aria-label,'Page name') or "
            "contains(@aria-label,'ページ名') or "
            "contains(@aria-label,'पेज')]"
        )
        inp.clear()
        inp.send_keys("Meta ")
        sleep(INPUT_DELAY)
        return True
    except Exception:
        return False

def click_fake_celebrity_flow(driver):
    """Xử lý 2 bước: Fake profile → Celebrity. Có retry mạnh + fallback."""
    # BƯỚC 1: Fake profile / Mạo danh / Doanh nghiệp giả mạo
    fake_clicked = False
    for _ in range(10):
        el = find_by_keywords(driver, LANG["fakeProfile"], timeout=2,
                              prefer_dialog=True)
        if el:
            safe_click(driver, el)
            sleep(1.2)
            fake_clicked = True
            break

        # Fallback: tìm trong dialog theo text
        try:
            for el in driver.find_elements(By.XPATH,
                    "//*[@role='menuitem' or @role='button' or @role='option']"
                    "[contains(translate(.,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),'fake') or "
                    "contains(.,'giả mạo') or "
                    "contains(.,'mạo danh') or "
                    "contains(.,'doanh nghiệp giả')]"):
                if el.is_displayed():
                    safe_click(driver, el)
                    sleep(1.2)
                    fake_clicked = True
                    break
            if fake_clicked:
                break
        except Exception:
            pass
        sleep(0.4)

    if not fake_clicked:
        return False

    # BƯỚC 2: Celebrity / Người nổi tiếng
    for _ in range(10):
        el = find_by_keywords(driver, LANG["celebrity"], timeout=2,
                              prefer_dialog=True)
        if el:
            safe_click(driver, el)
            sleep(BASE_DELAY + 0.5)
            return True

        try:
            for el in driver.find_elements(By.XPATH,
                    "//*[@role='menuitem' or @role='button' or @role='option']"
                    "[contains(translate(.,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),'celebrity') or "
                    "contains(translate(.,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),'public figure') or "
                    "contains(.,'nổi tiếng') or "
                    "contains(.,'công chúng')]"):
                if el.is_displayed():
                    safe_click(driver, el)
                    sleep(BASE_DELAY + 0.5)
                    return True
        except Exception:
            pass
        sleep(0.4)

    return False

# ================== REPORT TYPES ==================
REPORT_TYPES = [
    {"name": "Bạo Lực - Khủng Bố", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["violent"]}, {"k": LANG["terrorism"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Bạo Lực - Kêu Gọi Bạo Lực", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["violent"]}, {"k": LANG["callingForViolence"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Bạo Lực - Tội Phạm Có Tổ Chức", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["violent"]}, {"k": LANG["organizedCrime"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Tự Sát - Rối Loạn Ăn Uống", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["suicideOrSelfHarm"]}, {"k": LANG["eatingDisorder"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Lừa Đảo - Gian Lận", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["scamFraud"]}, {"k": LANG["fraudOrScam"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Lừa Đảo - Thư Rác", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["scamFraud"]}, {"k": LANG["spam"]},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Người Nổi Tiếng", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"a": "fake_celebrity_flow"},
        {"a": "input_meta"}, {"a": "meta"},
        {"k": LANG["next"], "act": 1},
        {"k": LANG["submit"], "act": 1},
        {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Giả Mạo - Không Phải Người Thật", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["fakeProfile"]}, {"k": LANG["notRealPerson"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Vấn Đề Khác", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"a": "something_else"},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Bắt Nạt - Quấy Rối", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["under18"]}, {"k": LANG["harassment"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Người Lớn - Mại Dâm", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["adultContent"]}, {"k": LANG["adultProstitution"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Bạo Hành Thể Chất", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["under18"]}, {"k": LANG["physicalAbuse"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]},
    {"name": "Đe Dọa Đáng Tin", "steps": [
        {"a": "menu"}, {"a": "report_entry"}, {"a": "something_about"},
        {"k": LANG["violent"]}, {"k": LANG["credibleThreat"]},
        {"k": LANG["submit"], "act": 1}, {"k": LANG["next"], "act": 1},
        {"k": LANG["done"], "act": 1, "done": 1}
    ]}
]

# ================== EXECUTE ==================
def execute_step(driver, step):
    a = step.get("a")
    kws = step.get("k")
    is_act = step.get("act", 0)
    is_done = step.get("done", 0)

    if a == "menu":
        return click_menu(driver)
    if a == "report_entry":
        return click_report_entry(driver)
    if a == "something_about":
        return click_something_about(driver)
    if a == "something_else":
        return click_something_else(driver)
    if a == "meta":
        return click_meta_result(driver)
    if a == "input_meta":
        return input_meta_name(driver)
    if a == "fake_celebrity_flow":
        return click_fake_celebrity_flow(driver)

    if not kws:
        return False

    if is_act or is_done:
        el = find_by_keywords(driver, kws, timeout=6,
                              exact=True, prefer_dialog=True)
        if not el:
            el = find_by_keywords(driver, kws, timeout=3,
                                  exact=False, prefer_dialog=True)
    else:
        el = find_by_keywords(driver, kws, timeout=8, exact=False,
                              prefer_dialog=True)

    if el:
        safe_click(driver, el)
        if is_done:
            sleep(DONE_DELAY)
        elif is_act:
            sleep(WAIT_FOR_ACTION)
        else:
            sleep(BASE_DELAY)
        return True
    return False

def run_report(driver, report):
    """Chạy 1 report + check dialog lỗi sau MỖI bước."""
    global TARGET_DIED, SORRY_STREAK
    name = report["name"]
    steps = report["steps"]
    log(f"📋 Bắt đầu: {name}", "yellow")

    had_sorry = False
    for i, step in enumerate(steps):
        if TARGET_DIED:
            log("💀 Page đã DIE — dừng report!", "red", "🛑")
            return False

        label = step.get("a") or (step["k"][0] if step.get("k") else "?")
        print(f"   {C['dim']}[{i+1}/{len(steps)}]{C['reset']} "
              f"{C['cyan']}{label}{C['reset']}", end=" ")
        ok = execute_step(driver, step)
        print(f"{C['green']}✓{C['reset']}" if ok
              else f"{C['red']}✗ (bỏ qua){C['reset']}")

        # Check dialog lỗi sau mỗi bước
        if check_sorry_dialog(driver):
            had_sorry = True
            SORRY_STREAK += 1
            print(f"\n   {C['bold']}{C['yellow']}"
                  f"⚠️  'Sorry, something went wrong' "
                  f"({SORRY_STREAK}/{SORRY_THRESHOLD}){C['reset']}")
            close_sorry_dialog(driver)
            # Thử quay về URL mục tiêu
            break

        if not ok:
            sleep(0.2)

    if had_sorry:
        if SORRY_STREAK >= SORRY_THRESHOLD:
            TARGET_DIED = True
            log(f"💀 {SORRY_STREAK} report liên tiếp lỗi → PAGE ĐÃ DIE!",
                "red", "🛑")
        return False

    # Report OK → reset streak
    SORRY_STREAK = 0
    if TARGET_DIED:
        return False
    log(f"✅ Xong: {name}", "green", "✔")
    return True

def start_vnc_if_needed():
    try:
        out = subprocess.run(["pgrep", "-f", "Xvnc"],
                             capture_output=True, text=True)
        if out.returncode != 0:
            log("Khởi động VNC server :1...", "yellow", "🖥️")
            subprocess.Popen(["vncserver", ":1"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            sleep(2)
    except Exception:
        pass

def start_firefox():
    log("Khởi tạo Firefox (SIÊU TỐC - no CSS/img)...", "yellow", "🦊")
    opts = Options()
    opts.add_argument("--headless") # <--- DÒNG ĐÃ ĐƯỢC THÊM VÀO ĐÂY

    opts.set_preference("permissions.default.image", 2)
    opts.set_preference("permissions.default.stylesheet", 2)
    opts.set_preference("permissions.default.subdocument", 2)
    opts.set_preference("permissions.default.object", 2)
    opts.set_preference("permissions.default.font", 2)

    opts.set_preference("toolkit.cosmeticAnimations.enabled", False)
    opts.set_preference("browser.fullscreen.animate", False)
    opts.set_preference("ui.prefersReducedMotion", 1)
    opts.set_preference("image.animation_mode", "none")

    opts.set_preference("dom.ipc.processCount", 1)
    opts.set_preference("browser.tabs.remote.autostart", False)
    opts.set_preference("layers.acceleration.disabled", True)
    opts.set_preference("gfx.webrender.all", False)
    opts.set_preference("gfx.canvas.accelerated", False)
    opts.set_preference("media.hardware-video-decoding.enabled", False)

    opts.set_preference("browser.cache.memory.enable", True)
    opts.set_preference("browser.cache.disk.enable", False)
    opts.set_preference("browser.sessionstore.resume_from_crash", False)
    opts.set_preference("browser.sessionstore.max_tabs_undo", 0)

    opts.set_preference("dom.webnotifications.enabled", False)
    opts.set_preference("media.volume_scale", "0.0")
    opts.set_preference("toolkit.telemetry.enabled", False)
    opts.set_preference("toolkit.telemetry.unified", False)
    opts.set_preference("datareporting.healthreport.uploadEnabled", False)
    opts.set_preference("app.update.auto", False)
    opts.set_preference("app.update.enabled", False)
    opts.set_preference("extensions.update.enabled", False)

    opts.set_preference("network.http.pipelining", True)
    opts.set_preference("network.http.pipelining.maxrequests", 8)
    opts.set_preference("network.http.max-connections", 30)
    opts.set_preference("network.http.max-persistent-connections-per-server", 10)

    opts.set_preference("general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    opts.binary_location = shutil.which("firefox") or \
        "/data/data/com.termux/files/usr/bin/firefox"
    service = Service(GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=opts)
    driver.set_window_size(1000, 900)

    try:
        driver.execute_script("""
            const style = document.createElement('style');
            style.textContent = 'img,video,svg{display:none!important}';
            document.head.appendChild(style);
        """)
    except Exception:
        pass
    return driver

def login_with_cookies(driver, cookies_raw):
    log("Mở Facebook để nạp cookie...", "cyan", "🍪")
    driver.get("https://www.facebook.com")
    sleep(2)
    count = 0
    for pair in cookies_raw.split(";"):
        pair = pair.strip()
        if "=" not in pair:
            continue
        name, value = pair.split("=", 1)
        try:
            driver.add_cookie({
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".facebook.com",
                "path": "/"
            })
            count += 1
        except Exception:
            pass
    log(f"Đã nạp {count} cookie", "green")
    driver.refresh()
    sleep(3)
    if "login" in driver.current_url.lower():
        return False
    return True

def navigate_target(driver, url):
    log(f"Đang mở mục tiêu: {url}", "cyan", "🎯")
    driver.get(url)
    sleep(3)
    try:
        for el in driver.find_elements(By.CSS_SELECTOR,
                                       'div[role="button"], button'):
            t = (el.text or "").lower()
            if "not now" in t or "không phải bây giờ" in t or "今はしない" in t:
                safe_click(driver, el, highlight=False)
                sleep(0.5)
                break
    except Exception:
        pass

# ================== DIE CHECK CUỐI VÒNG ==================
def check_target_status(driver, url):
    try:
        driver.get(url)
        sleep(3)

        current_url = (driver.current_url or "").lower().rstrip("/")
        try:
            page_source = (driver.page_source or "").lower()
        except Exception:
            page_source = ""
        title = (driver.title or "").lower()

        # Check dialog lỗi trước
        try:
            for d in driver.find_elements(By.CSS_SELECTOR,
                                           '[role="dialog"], [role="alertdialog"]'):
                if d.is_displayed():
                    t = (d.text or "").lower()
                    if ("sorry, something went wrong" in t or
                            "technical problem" in t or
                            "đã xảy ra lỗi" in t or
                            "đã xảy ra sự cố" in t):
                        return "DIE", f"Dialog lỗi: '{t[:80]}'"
        except Exception:
            pass

        die_signals = [
            "this content isn't available",
            "this page isn't available",
            "content isn't available right now",
            "this content isn't available right now",
            "sorry, this page",
            "page not found",
            "no longer available",
            "has been removed",
            "has been disabled",
            "was disabled",
            "isn't available",
            "sorry, something went wrong",
            "we're sorry, there's a technical problem",
            "there's a technical problem",
            "trang này hiện không",
            "nội dung này hiện không",
            "không khả dụng",
            "không tìm thấy trang",
            "đã bị xóa",
            "đã bị vô hiệu hóa",
            "đã bị khóa",
            "tài khoản này đã bị",
            "xin lỗi, đã xảy ra lỗi",
            "đã xảy ra sự cố",
            "このコンテンツは現在",
            "このページは",
            "利用できません",
        ]
        for signal in die_signals:
            if signal in page_source:
                return "DIE", f"Phát hiện: '{signal}'"

        home_urls = (
            "https://www.facebook.com",
            "https://facebook.com",
            "https://m.facebook.com",
            "https://web.facebook.com",
        )
        if current_url in home_urls:
            return "DIE", "Bị redirect về trang chủ FB"

        if len(page_source) < 5000:
            return "UNKNOWN", f"Page source quá ngắn ({len(page_source)} bytes)"

        if title.strip() in ("facebook", "facebook - log in or sign up"):
            return "DIE", "Title chỉ có 'Facebook' — không load được page"

        return "ALIVE", "Truy cập bình thường, page còn tồn tại"

    except Exception as e:
        return "UNKNOWN", f"Lỗi kiểm tra: {e}"

def print_verdict(status, reason, total_reports, elapsed):
    hr("═", 60, "magenta")
    print(f"{C['bold']}{C['magenta']}  💀 ĐÁNH GIÁ MỤC TIÊU 💀{C['reset']}")
    hr("─", 60, "magenta")
    print(f"  {C['dim']}Tổng reports :{C['reset']} {C['cyan']}{total_reports}{C['reset']}")
    print(f"  {C['dim']}Thời gian    :{C['reset']} {C['cyan']}{elapsed:.0f}s{C['reset']}")

    if status == "DIE":
        print(f"\n  {C['bold']}{C['red']}"
              f"╔══════════════════════════════════════╗{C['reset']}")
        print(f"  {C['bold']}{C['red']}"
              f"║     💀  ACC ĐÃ DIE  💀              ║{C['reset']}")
        print(f"  {C['bold']}{C['red']}"
              f"╚══════════════════════════════════════╝{C['reset']}")
        print(f"  {C['yellow']}Lý do:{C['reset']} {reason}")
        return "DIE"

    elif status == "ALIVE":
        print(f"\n  {C['bold']}{C['green']}"
              f"╔══════════════════════════════════════╗{C['reset']}")
        print(f"  {C['bold']}{C['green']}"
              f"║     ✅  ACC CHƯA DIE                ║{C['reset']}")
        print(f"  {C['bold']}{C['green']}"
              f"╚══════════════════════════════════════╝{C['reset']}")
        print(f"  {C['yellow']}Lý do:{C['reset']} {reason}")
        return "ALIVE"

    else:
        print(f"\n  {C['bold']}{C['yellow']}"
              f"╔══════════════════════════════════════╗{C['reset']}")
        print(f"  {C['bold']}{C['yellow']}"
              f"║     ⚠️  KHÔNG XÁC ĐỊNH ĐƯỢC         ║{C['reset']}")
        print(f"  {C['bold']}{C['yellow']}"
              f"╚══════════════════════════════════════╝{C['reset']}")
        print(f"  {C['yellow']}Lý do:{C['reset']} {reason}")
        return "UNKNOWN"

# ================== MAIN ==================
def main():
    global REPORT_MODE, BASE_DELAY, CYCLE_REST
    global TARGET_DIED, SORRY_STREAK
    print_banner()

    # Cookie
    hr()
    log("Bước 1: Nhập cookie Facebook", "yellow", "1️⃣")
    print(f"{C['dim']}Ví dụ: c_user=1000xxx;xs=12%3Aabc...;datr=xxx{C['reset']}")
    cookies = input(f"{C['cyan']}🍪 Cookie > {C['reset']}").strip()
    if not cookies:
        log("Cookie trống — thoát!", "red", "❌")
        sys.exit(1)

    # URL
    hr()
    log("Bước 2: Link mục tiêu (profile / page)", "yellow", "2️⃣")
    target = input(f"{C['cyan']}🎯 URL > {C['reset']}").strip()
    if not target:
        log("URL trống — thoát!", "red", "❌")
        sys.exit(1)
    if not target.startswith("http"):
        target = "https://www.facebook.com/" + target.lstrip("/")

    # Mode
    hr()
    log("Bước 3: Chế độ báo cáo", "yellow", "3️⃣")
    print(f"  {C['cyan']}[1]{C['reset']} 👤 Profile  "
          f"{C['cyan']}[2]{C['reset']} 📄 Page  "
          f"{C['cyan']}[3]{C['reset']} 🎯 Auto (mặc định)")
    mode = input(f"{C['cyan']}⚙️  Chọn [1/2/3] > {C['reset']}").strip()
    if mode == "1":
        REPORT_MODE = "profile"
    elif mode == "2":
        REPORT_MODE = "page"
    else:
        REPORT_MODE = "auto"
    log(f"Chế độ: {REPORT_MODE.upper()}", "magenta")

    # Delay
    hr()
    print(f"{C['dim']}Enter để dùng mặc định siêu tốc{C['reset']}")
    d = input(f"{C['cyan']}⏱️  Delay bước (mặc định 0.5s) > {C['reset']}").strip()
    if d:
        try:
            BASE_DELAY = float(d)
        except ValueError:
            pass
    r = input(f"{C['cyan']}💤 Nghỉ vòng (mặc định 10s) > {C['reset']}").strip()
    if r:
        try:
            CYCLE_REST = int(r)
        except ValueError:
            pass

    # Start
    hr()
    start_vnc_if_needed()
    log("Mở VNC Viewer để xem nha em yêu💗", "magenta", "📱")
    sleep(0.5)

    driver = None
    total_reports = 0
    t_start = time.time()
    try:
        driver = start_firefox()
        log("Firefox đã khởi động", "green", "✓")

        if not login_with_cookies(driver, cookies):
            log("Cookie hết hạn hoặc không hợp lệ!", "red", "❌")
            input("Nhấn Enter để đóng...")
            driver.quit()
            sys.exit(1)
        log("Đăng nhập thành công!", "green", "✓")

        navigate_target(driver, target)

        loop = 0
        try:
            while True:
                loop += 1
                TARGET_DIED = False
                SORRY_STREAK = 0
                hr("═")
                print(f"{C['bold']}{C['yellow']}  🔄 VÒNG {loop}  |  "
                      f"Tổng: {total_reports}{C['reset']}")
                hr("═")

                for report in REPORT_TYPES:
                    if TARGET_DIED:
                        log(f"💀 Page đã DIE — dừng vòng {loop}!",
                            "red", "🛑")
                        break
                    try:
                        success = run_report(driver, report)
                        if success:
                            total_reports += 1
                        sleep(INTER_REPORT_DELAY)
                    except Exception as e:
                        log(f"Lỗi: {e}", "red", "⚠")
                        try:
                            navigate_target(driver, target)
                        except Exception:
                            pass
                        continue

                elapsed = time.time() - t_start
                log(f"Vòng {loop} xong! "
                    f"({elapsed:.0f}s / {total_reports} rp)", "green", "✅")

                # Kiểm tra mục tiêu cuối vòng
                log("Đang kiểm tra mục tiêu...", "cyan", "🔍")
                if TARGET_DIED:
                    status, reason = ("DIE",
                        f"{SORRY_STREAK} report liên tiếp gặp lỗi "
                        f"'Sorry, something went wrong'")
                else:
                    status, reason = check_target_status(driver, target)

                verdict = print_verdict(status, reason,
                                        total_reports, elapsed)

                if verdict == "DIE":
                    print(f"\n{C['bold']}{C['red']}"
                          f"  ⚠️  Mục tiêu đã DIE!{C['reset']}")
                    print(f"  {C['cyan']}[c]{C['reset']} Tiếp tục vòng mới")
                    print(f"  {C['cyan']}[d]{C['reset']} Dừng tool (mặc định)")
                    ans = input(f"{C['cyan']}  > {C['reset']}").strip().lower()
                    if ans != "c":
                        log("Dừng tool — mục tiêu đã die.", "red", "💀")
                        break
                else:
                    log(f"Nghỉ {CYCLE_REST}s...", "yellow", "💤")
                    sleep(CYCLE_REST)

                try:
                    navigate_target(driver, target)
                except Exception:
                    pass

        except KeyboardInterrupt:
            print()
            log("Người dùng dừng.", "yellow", "⏹️")
        finally:
            hr("═")
            elapsed = time.time() - t_start
            log(f"TỔNG: {total_reports} báo cáo / {elapsed:.0f}s",
                "magenta", "📊")
            try:
                input("Nhấn Enter để đóng trình duyệt...")
            except Exception:
                pass
            if driver:
                driver.quit()
    except WebDriverException as e:
        log(f"Lỗi WebDriver: {e}", "red", "❌")
    except Exception as e:
        log(f"Lỗi: {e}", "red", "❌")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main()