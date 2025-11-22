import requests
import urllib3
import re
from .TrOCR import run_ocr
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup


class VTUScraper:
    """
    ONE METHOD ONLY: run()
    All constants stored inside __init__.
    """

    def __init__(self, site_path: str):
        self.site_path = site_path.strip().strip("/")
        self.base = "https://results.vtu.ac.in"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        self.index_url = f"{self.base}/{self.site_path}/index.php"
        self.result_url = f"{self.base}/{self.site_path}/resultpage.php"
        self.result_header = {
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                                "Cache-Control": "max-age=0",
                                "Connection": "keep-alive",
                                "Content-Type": "application/x-www-form-urlencoded",
                                "Origin": "https://results.vtu.ac.in",
                                "Referer": "https://results.vtu.ac.in/JJEcbcs25/index.php",
                                "Sec-Fetch-Dest": "document",
                                "Sec-Fetch-Mode": "navigate",
                                "Sec-Fetch-Site": "same-origin",
                                "Sec-Fetch-User": "?1",
                                "Upgrade-Insecure-Requests": "1",
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 OPR/123.0.0.0",
                                "sec-ch-ua": "\"Not;A=Brand\";v=\"99\", \"Opera\";v=\"123\", \"Chromium\";v=\"139\"",
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": "\"Windows\"",
            }
        self.cookies = None
        self.result_payload = None
        self.timeout = 20
        self.verify_ssl = False

    def run(self, lns: str):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            session = requests.Session()

            # GET INDEX PAGE
            r = session.get(
                self.index_url,
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            html = r.text
            print("STATUS:", r.status_code)
            # =============================
            # EXTRACT TOKEN (IMPORTANT)
            # =============================
            soup = BeautifulSoup(html, "html.parser")
            token_tag = soup.find("input", {"name": "Token"})

            if not token_tag:
                print("Token NOT FOUND")
                return "TOKEN NOT FOUND"

            token_value = token_tag.get("value")
            print("TOKEN:", token_value)

            # FIND CAPTCHA
            captcha_url = None
            captcha_text = ""

            m = re.search(r'src="(/captcha/[^"]+)"', html)
            if m:
                captcha_url = self.base + m.group(1)
                #print("CAPTCHA URL:", captcha_url)

                cap = session.get(captcha_url, timeout=self.timeout, verify=self.verify_ssl)
                raw_img = cap.content

                # OCR
                img = Image.open(BytesIO(raw_img))
                captcha_text = run_ocr(img).strip()
                print("OCR:", captcha_text)

                # SAVE CAPTCHA
                # with open("captcha.jpg", "wb") as f:
                #     f.write(raw_img)
            else:
                print("NO CAPTCHA FOUND")

            self.cookies = session.cookies.get_dict()
            self.result_payload = {
                "Token":token_value,
            "lns":lns,
            "captchacode":captcha_text,
            }

            r = requests.post(
                url=self.result_url,
                headers=self.headers,
                cookies=self.cookies,
                data=self.result_payload,
                timeout=self.timeout,
                verify=False
            )

            # with open("full_response.json", "w", encoding="utf-8") as f:
            #     json.dump(full, f, ensure_ascii=False, indent=2)
            full = r.text

            return full

        except Exception as e:
            print("ERROR:", e)
            return {"error": str(e)}


#  ----------------------------
#  MAIN EXECUTION BLOCK
#  ----------------------------
if __name__ == "__main__":
    scraper = VTUScraper("JJEcbcs25")

    MAX_RETRY = 5
    attempt = 0
    result = ""

    while attempt < MAX_RETRY:
        attempt += 1
        print(f"\n===== ATTEMPT {attempt} =====")

        result = scraper.run("")

        # invalid captcha check
        if "Invalid captcha code !!!" in result:
            print("Invalid captcha — retrying...")
            continue

        # success → break
        break

    print("\nFINAL RESULT:\n")
    print(result)

