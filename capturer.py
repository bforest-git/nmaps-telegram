from io import BytesIO
from threading import Lock
from time import sleep
from urllib.parse import urlsplit
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


class IllegalURL(Exception):
    pass


class YMTempUnsupported(Exception):
    pass


class Capturer:
    chrome = ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
              'Gecko/20100101 Firefox/55.0')
    webdriver.DesiredCapabilities.PHANTOMJS[
        'phantomjs.page.customHeaders.User-Agent'
    ] = chrome
    hide_sidebar = ("document.querySelector('.nk-onboarding-view')"
                    ".style.display = 'none';")

    def start_driver(self) -> None:
        self.drv = webdriver.PhantomJS('phantomjs')

        self.drv.set_window_size(1280, 1024)
        self.drv.implicitly_wait(5)

    def __init__(self) -> None:
        self.start_driver()
        self.lock = Lock()

    def reboot(self) -> None:
        self.drv.quit()
        self.start_driver()

    @staticmethod
    def is_nmaps(url: str) -> bool:
        spl = urlsplit(url)
        if spl.netloc in ('n.maps.yandex.ru', 'mapmaker.yandex.com'):
            return True
        elif spl.netloc == 'yandex.ru' and spl.path.startswith('/maps'):
            raise YMTempUnsupported
        raise IllegalURL

    def take_screenshot(self, url: str) -> BytesIO:
        self.lock.acquire()
        try:
            nmaps = self.is_nmaps(url)

            self.drv.get(url)
            self.drv.refresh()
            sleep(3)

            if nmaps:
                self.drv.execute_script(self.hide_sidebar)

            sleep(4)
        except WebDriverException as e:
            print(e)
        finally:
            self.lock.release()
        return BytesIO(self.drv.get_screenshot_as_png())

    def __del__(self) -> None:
        self.drv.quit()
