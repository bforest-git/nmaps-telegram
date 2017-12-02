from io import BytesIO
from threading import Lock
from time import sleep
from urllib.parse import urlsplit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import os


class IllegalURL(Exception):
    pass


class Capturer:
    hide_sidebar = ("document.querySelector('.nk-onboarding-view')"
                    ".style.display = 'none';")
                    
    def start_driver(self):
        chrome_options = Options()
        chrome_options.binary_location = os.getenv('GOOGLE_CHROME_BIN', '')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')

        self.drv = webdriver.Chrome(executable_path=os.getenv('GOOGLE_CHROME_DRIVER', ''),
                                    chrome_options=chrome_options)

        self.drv.set_window_size(1280, 1024)
        self.drv.implicitly_wait(5)

    def __init__(self):
        self.start_driver()
        self.lock = Lock()
        
    def reboot(self):
        self.drv.quit()
        self.start_driver()

    @staticmethod
    def is_nmaps(url):
        spl = urlsplit(url)
        if spl.netloc == 'n.maps.yandex.ru' or spl.netloc == 'mapmaker.yandex.com':
            return True
        elif spl.netloc == 'yandex.ru' and spl.path.startswith('/maps'):
            return False
        raise IllegalURL

    def take_screenshot(self, url):
        self.lock.acquire()
        try:
            nmaps = self.is_nmaps(url)

            self.drv.get(url)
            self.drv.refresh()
            sleep(3)

            if nmaps:
                self.drv.execute_script(self.hide_sidebar)

            sleep(3)
        except WebDriverException as e:
            print(e)
        finally:
            self.lock.release()
        return BytesIO(self.drv.get_screenshot_as_png())

    def __del__(self):
        self.drv.quit()
