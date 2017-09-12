from io import BytesIO
from time import sleep
from urllib.parse import urlsplit
from selenium import webdriver, common

class IllegalURL(Exception):
    pass

class Capturer:
    chrome = ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
              'Gecko/20100101 Firefox/55.0')
    webdriver.DesiredCapabilities.PHANTOMJS[
        'phantomjs.page.customHeaders.User-Agent'
    ] = chrome

    nmaps_modal_cls = 'nk-welcome-screen-view__start'
    hide_sidebar = ("document.querySelector('.nk-onboarding-view')"
                    ".style.display = 'none';")
    hide_ad_info = ("document.querySelector('.sidebar-panel-view')"
                    ".style.display = 'none';")

    def __init__(self):
        self.drv = webdriver.PhantomJS('./phantomjs')
        self.drv.set_window_size(1024, 800)
        self.drv.implicitly_wait(5)

    @staticmethod
    def is_nmaps(url):
        spl = urlsplit(url)
        if spl.netloc == 'n.maps.yandex.ru':
            return True
        elif spl.netloc == 'yandex.ru' and spl.path.startswith('/maps'):
            return False
        raise IllegalURL

    def take_screenshot(self, url):
        nmaps = self.is_nmaps(url)

        self.drv.get(url)
        self.drv.refresh()
        sleep(3)

        if nmaps:
            sleep(3.5)
            try:
                start_view = self.drv.find_element_by_class_name(self.nmaps_modal_cls)
                if start_view.is_displayed():
                    start_view.find_element_by_tag_name('button').click()

                self.drv.execute_script(self.hide_sidebar)
            except common.exceptions.WebDriverException as e:
                print(e)
        else:
            try:
                self.drv.execute_script(self.hide_ad_info)
            except common.exceptions.WebDriverException as e:
                print(e)
        return BytesIO(self.drv.get_screenshot_as_png())

    def __del__(self):
        self.drv.quit()
