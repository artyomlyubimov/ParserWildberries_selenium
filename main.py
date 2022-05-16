from random import randrange
import requests
import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

import colorama
from colorama import Fore, Style
colorama.init()


class Parser:

    def __init__(self, article: int):
        """ Объект страницы на товар (определяющийся по артикулу) """
        self.article = article
        self.url = f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=GP'
        self.user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, ' \
                          'like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36'

        # main
        self.name = None
        self.brand = None
        self.price_now = 0
        self.price_old = 0
        self.sold_out = False
        self.discount = True
        self.seller = None
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.errors = 'No'
        self.image = None

    def _get_name(self, driver) -> None:
        try:
            self.name = driver.find_element(By.XPATH, '//*[@id="container"]/div[2]/div/div[2]/h1/span[2]').text
        except NoSuchElementException:
            self.name = driver.find_element(By.XPATH, '//*[@id="container"]/div[2]/div/div[2]/h1/span[2]').text
        finally:
            if self.name:
                print(Fore.GREEN + '[+] The "name" was successfully received!' + Style.RESET_ALL)
            else:
                print(Fore.RED + '[-] Failed to parse the "name"!' + Style.RESET_ALL)

    def _get_brand(self, driver) -> None:
        try:
            self.brand = driver.find_element(By.XPATH, '//*[@id="container"]/div[2]/div/div[2]/h1/span[1]').text
        except NoSuchElementException:
            sleep(1)
            self.brand = driver.find_element(By.XPATH, '//*[@id="container"]/div[2]/div/div[2]/h1/span[1]').text
        finally:
            if self.brand:
                print(Fore.GREEN + '[+] The "brand" was successfully received!' + Style.RESET_ALL)
            else:
                print(Fore.RED + '[-] Failed to parse the "brand"!' + Style.RESET_ALL)

    def _get_seller(self, driver) -> None:
        lim = 10
        while True:
            if lim == 0:
                break

            try:
                self.seller = driver.find_element(By.XPATH,
                                                      '//*[@id="infoBlockProductCard"]/div[8]/div[2]/div/div[1]/div[2]/div[1]/a').text
                break
            except NoSuchElementException:
                lim -= 1
                sleep(randrange(1, 2))
        if self.seller:
            print(Fore.GREEN + '[+] The "seller" was successfully received!' + Style.RESET_ALL)
        else:
            print(Fore.RED + '[-] Failed to parse the "seller"!' + Style.RESET_ALL)

    def _get_image(self, driver) -> None:
        try:
            image_url = driver.find_element(By.XPATH, '//*[@id="imageContainer"]/div/img[1]').get_attribute('src')
            img_data = requests.get(image_url).content
            path = f'media\\{self.article}.png'
            with open(path, 'wb') as f:
                f.write(img_data)

            self.image = path
        except NoSuchElementException:
            pass
        finally:
            if self.image:
                print(Fore.GREEN + '[+] The "image" was successfully received!' + Style.RESET_ALL)
            else:
                print(Fore.RED + '[-] Failed to parse the "image"!' + Style.RESET_ALL)

    def _get_price(self, driver) -> None:
        try:
            self.price_now = driver.find_element(By.XPATH, '//*[@id="infoBlockProductCard"]/div[2]/div/div/p/span').text
            self.price_old = driver.find_element(By.XPATH, '//*[@id="infoBlockProductCard"]/div[2]/div/div/p/del').text
        except NoSuchElementException:
            pass
        finally:
            if self.price_now and self.price_old:
                print(Fore.GREEN + '[+] The "price" was successfully received!' + Style.RESET_ALL)
            elif self.price_now:
                print(Fore.GREEN + '[+] The "price" was successfully received! (without discount)' + Style.RESET_ALL)
                self.price_old = self.price_now
                self.discount = False
            else:
                self.sold_out = True
                print(Fore.YELLOW + '[!] The product is out of stock!' + Style.RESET_ALL)

    def parse(self, **options: bool) -> list:
        """
            ** options:
                name(bool): Спарсить ли наименование товара. По умолчанию True.
                brand(bool): Спарсить ли наименование бренда товара. По умолчанию True.
                seller(bool): Спарсить ли наименование поставщика товара. По умолчанию True.
                price(bool): Спарсить ли стоимость товара (со скидкой/без  скидки). По умолчанию True.
                image(bool): Спарсить ли фото товара. По умолчанию True.

            Возвращает словарь со всеми данными
         """
        print('----- Started parsing the page! -----\n')
        options_chrome = Options()
        options_chrome.add_argument(f'user-agent={self.user_agent}')
        # options_chrome.add_argument('--headless')
        options_chrome.add_argument('--ignore-certificate-errors')
        options_chrome.add_argument('--ignore-ssl-errors')

        s = Service(r'C:\Users\palac\PycharmProjects\test_task\newsite\tracking\chromedriver101\chromedriver.exe')
        driver = webdriver.Chrome(service=s, options=options_chrome)
        driver.get(url=self.url)
        while True:
            try:
                driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/h1')
                self.errors = '404'
                print('----- Page not found! -----')
                return self._render()
            except NoSuchElementException:
                pass

            try:
                driver.find_element(By.ID, 'productNmId')
                print('I\'m started')
                break
            except NoSuchElementException:
                print('Waiting for the page to load...')
                sleep(randrange(1, 2))
        try:
            if options.get('seller', True):
                self._get_seller(driver)
            if options.get('name', True):
                self._get_name(driver)
            if options.get('brand', True):
                self._get_brand(driver)
            if options.get('price', True):
                self._get_price(driver)
            if options.get('image', True):
                self._get_image(driver)

        except Exception as ex:
            print(ex)

        finally:
            driver.close()
            driver.quit()
        print('\n----- Parsing completed successfully! -----')
        return self._render()

    def _render(self) -> list:
        """ Формиррует словарь для возврата """
        self.price_old = self.price_old if self.price_old else self.price_now

        data = [{'main':
                     {'article_id': self.article,
                      'url': self.url,
                      'name': self.name,
                      'brand': self.brand,
                      'price_now': self.price_now,
                      'price_old': self.price_old,
                      'sold_out': self.sold_out,
                      'seller': str(self.seller),
                      'date_upload': self.date,
                      'errors': self.errors,
                      'image': self.image
                      }}]
        return data

    def upload_price(self) -> list:
        """ Собирает со страницы только цены на товар (Вызывает только get_price) """
        return self.parse(name=False, brand=False, seller=False, image=False, description=False)

    def __str__(self):
        return f'Артикул: {self.article} / Ссылка: {self.url}'

    def __call__(self):
        return self._render()


if __name__ == '__main__':
    from pprint import pprint
    article_id = 28440520
    p = Parser(article=article_id)
    print(p)
    p.parse(name=True, brand=True, seller=True, price=True, image=True)
    pprint(p())
