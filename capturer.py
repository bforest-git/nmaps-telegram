from time import sleep
from urllib.parse import urlsplit
from selenium import webdriver, common


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
    default = 'scrn.png'

    def __init__(self):
        self.drv = webdriver.PhantomJS('./phantomjs')
        self.drv.set_window_size(1024, 800)
        self.drv.implicitly_wait(5)

    @staticmethod
    def is_nmaps(url):
        return urlsplit(url).netloc.startswith('n.maps')

    def take_screenshot(self, url, filename=default):
        self.drv.get(url)
        self.drv.refresh()
        sleep(3)

        if self.is_nmaps(url):
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
        self.drv.save_screenshot(filename)

    def __del__(self):
        self.drv.quit()

    def emergency(self):
        self.drv.save_screenshot('error.png')


if __name__ == '__main__':
    cpt = Capturer()
    for idx, url in enumerate(['https://n.maps.yandex.ru/#!/?z=19&ll=74.607714%2C42.876470&l=nk%23sat',
                               'https://n.maps.yandex.ru/-/CBUfr0Bt~C',
                               'https://yandex.ru/maps/54/yekaterinburg/?ll=60.640533%2C56.810370&z=12',
                               'https://yandex.ru/maps/-/CBUfr0rbGB']):
        try:
            cpt.take_screenshot(url, 'test{}.png'.format(idx))
        except:
            cpt.emergency()
            break
