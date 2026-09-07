import re
import requests
import time
import random
import threading


xanh_la = "\033[1;32m"
do = "\033[1;31m"
xanhnhat = "\033[0;36m"
xanh_cyan_dam = "\033[1;36m"
vang = "\033[1;33m"
trang = "\033[0m"
xanh_duong = "\033[1;34m" 

RAINBOW_COLORS = [
    "\033[1;31m", 
    "\033[1;33m", 
    "\033[1;32m", 
    "\033[1;36m", 
    "\033[1;34m", 
    "\033[1;35m", 
]
RESET_COLOR = "\033[0m"


COLOR_DEFAULT = trang
COLOR_SUCCESS = xanh_la
COLOR_ERROR = do
COLOR_INFO = xanh_cyan_dam
COLOR_HIGHLIGHT = vang
COLOR_INPUT = xanh_duong
COLOR_BOX_ID = xanhnhat
COLOR_CONTENT = trang


class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.init_params()

    def get_user_id(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        urls = [
            'https://www.facebook.com',
            'https://mbasic.facebook.com',
            'https://m.facebook.com'
        ]

        for url in urls:
            try:
                print(f"[*] Thử lấy fb_dtsg từ {url}")
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"[❌] Yêu cầu tới {url} thất bại, mã trạng thái: {response.status_code}")
                    continue

                fb_dtsg_patterns = [
                    r'"token":"(.*?)"',
                    r'name="fb_dtsg" value="(.*?)"',
                    r'"fb_dtsg":"(.*?)"',
                    r'fb_dtsg=([^&"]+)'
                ]
                jazoest_pattern = r'name="jazoest" value="(\d+)"'
                rev_pattern = r'"__rev":"(\d+)"'

                fb_dtsg = None
                for pattern in fb_dtsg_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        fb_dtsg = match.group(1)
                        break

                jazoest_match = re.search(jazoest_pattern, response.text)
                rev_match = re.search(rev_pattern, response.text)

                if fb_dtsg:
                    self.fb_dtsg = fb_dtsg
                    self.jazoest = jazoest_match.group(1) if jazoest_match else "22036"
                    self.rev = rev_match.group(1) if rev_match else "1015919737"
                    print(f"[✓] Lấy được fb_dtsg: {self.fb_dtsg}, jazoest: {self.jazoest}, rev: {self.rev}")
                    return
                else:
                    print(f"[⚠] Không tìm thấy fb_dtsg trong {url}")

            except Exception as e:
                print(f"[❌] Lỗi khi truy cập {url}: {str(e)}")
                time.sleep(2)

        raise Exception("Không thể lấy được fb_dtsg từ bất kỳ URL nào")

    def refresh_fb_dtsg(self):
        self.fb_dtsg = None 
        try:
            self.init_params()
            return self.fb_dtsg is not None
        except Exception as e:
            print(f"{COLOR_ERROR}[LỖI LÀM MỚI] Cookie {self.user_id}: {str(e)}{trang}")
            return False

    def send_message(self, recipient_id, message):
        timestamp = int(time.time() * 1000)
        data = {
            'fb_dtsg': self.fb_dtsg,
            '__user': self.user_id,
            'body': message,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp,
            'offline_threading_id': str(timestamp),
            'message_id': str(timestamp),
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury',
            'jazoest': self.jazoest,
            '__rev': self.rev
        }
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
            return response.status_code == 200, response.text
        except requests.exceptions.RequestException:
            return False, "CONNECTION_ERROR"


def load_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()  
        if not content.strip():
            raise Exception(f"File {file_path} trống!")
        return content
    except Exception as e:
        raise Exception(f"Lỗi đọc file {file_path}: {str(e)}")


def messenger_worker(cookie, recipient_id, message, delay):
    try:
        messenger = Messenger(cookie)
        user_id = messenger.user_id
        
        print(f"{COLOR_INFO}[BẮT ĐẦU TREO]{trang} Cookie {user_id} - Delay: {delay}s")

        while True:
            try:
                success, response_text = messenger.send_message(recipient_id, message)
                
                status_text = f"{COLOR_SUCCESS}[SUCCESS]{trang}" if success else f"{COLOR_ERROR}[THẤT BẠI]{trang}"
                
                if not success:
                    
                    print(f"{status_text} {COLOR_HIGHLIGHT}Cookie {user_id}{trang} | {COLOR_HIGHLIGHT}[!] PHÁT HIỆN LỖI/HÀNH VI TỰ ĐỘNG. BẮT ĐẦU LÀM MỚI fb_dtsg...{trang}")
                    
                    if messenger.refresh_fb_dtsg():
                        print(f"{COLOR_SUCCESS}[THÀNH CÔNG] {COLOR_HIGHLIGHT}Cookie {user_id}{trang} | Đã làm mới fb_dtsg. Thử lại ở chu kỳ tiếp theo.{trang}")
                        
                        status_text = f"{COLOR_SUCCESS}[REFRESH_OK]{trang}"
                    else:
                        print(f"{COLOR_ERROR}[THẤT BẠI] {COLOR_HIGHLIGHT}Cookie {user_id}{trang} | KHÔNG THỂ LÀM MỚI. CÓ THỂ COOKIE ĐÃ CHẾT.{trang}")
                        
                
                
                print(f"{status_text} {COLOR_HIGHLIGHT}Cookie {user_id}{trang} gửi tin nhắn tới box: {COLOR_BOX_ID}{recipient_id}{trang} | Delay: {delay}s")

            except Exception as e:
                
                print(f"{COLOR_ERROR}[LỖI GỬI TIN] Cookie {user_id}: {str(e)}{trang}")
            
            
            time.sleep(delay)
            
    except Exception as e:
        
        print(f"{COLOR_ERROR}[LUỒNG DỪNG] Cookie {cookie[:10]}...: {str(e)}{trang}")
        


def print_rainbow_banner(text, frame_width=60):
    """In banner với hiệu ứng gradient 7 màu"""
    print(trang)
    print("═" * frame_width)
    
    colored_text = ""
    for i, char in enumerate(text):
        color_index = i % len(RAINBOW_COLORS)
        colored_text += RAINBOW_COLORS[color_index] + char
    
    # Tính padding để căn giữa
    visible_length = len(text)
    padding = (frame_width - 2 - visible_length) // 2
    
    print("║" + " " * padding + colored_text + RESET_COLOR + " " * (frame_width - 2 - padding - visible_length) + "║")
    
    print("═" * frame_width)
    print(trang)


def main():
    
    print(f"{COLOR_DEFAULT}=== Bắt đầu chạy ==={trang}")
    
    # In banner với tên mới
    print_rainbow_banner(" ZIN - Vĩnh Hằng Sàn Treo ")
    
    # Bước 1: Nhập cookie trực tiếp
    print(f"{COLOR_INFO}Nhập cookie của bạn (paste trực tiếp, nhập 'done' để kết thúc):{trang}")
    cookies = []
    cookie_count = 1
    while True:
        cookie_input = input(f"{COLOR_INPUT}Cookie {cookie_count}: {trang}").strip()
        if cookie_input.lower() == 'done':
            if len(cookies) == 0:
                print(f"{COLOR_ERROR}Bạn chưa nhập cookie nào!{trang}")
                continue
            break
        if cookie_input:
            cookies.append(cookie_input)
            print(f"{COLOR_SUCCESS}Đã thêm cookie {cookie_count}{trang}")
            cookie_count += 1
        else:
            print(f"{COLOR_ERROR}Cookie không được để trống!{trang}")
    
    print(f"{COLOR_SUCCESS}Đã nhập tổng cộng {len(cookies)} cookie{trang}")
    
    # Bước 2: Nhập ID box
    while True:
        recipient_id = input(f"{COLOR_INPUT}Nhập ID box: {trang}").strip()
        if recipient_id.isdigit():
            break
        print(f"{COLOR_ERROR}ID box phải là số!{trang}")
    
    # Bước 3: Nhập nội dung tin nhắn
    message = input(f"{COLOR_INPUT}Nhập nội dung tin nhắn: {trang}")
    while not message.strip():
        print(f"{COLOR_ERROR}Nội dung không được để trống!{trang}")
        message = input(f"{COLOR_INPUT}Nhập nội dung tin nhắn: {trang}")
    
    # Bước 4: Nhập delay cho từng cookie
    per_cookie_delays = []
    
    print(f"\n{COLOR_INFO}Nhập delay cho từng cookie:{trang}")
    for i in range(len(cookies)):
        while True:
            try:
                d = float(input(f"{COLOR_INPUT}Delay cho cookie {i+1}: {trang}").strip())
                if d <= 0:
                    raise ValueError
                per_cookie_delays.append(d)
                break
            except ValueError:
                print(f"{COLOR_ERROR}Delay phải là số dương!{trang}")

    
    print(f"\n{COLOR_DEFAULT}Bắt đầu gửi tin nhắn với {len(cookies)} acc...{trang}")
    
    
    threads = []
    
    
    for cookie, delay in zip(cookies, per_cookie_delays):
        
        thread = threading.Thread(
            target=messenger_worker, 
            args=(cookie, recipient_id, message, delay), 
            daemon=True 
        )
        threads.append(thread)
        thread.start()

    
    try:
        
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        
        print(f"\n{COLOR_DEFAULT}Đã dừng chương trình!{trang}")

if __name__ == "__main__":
    main()