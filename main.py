from xml.sax.handler import all_properties

import telebot
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from telebot import types
import webbrowser


class PriceCheckBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.user_agent = UserAgent()
        self.store_urls = {
            '4:20 Shop': 'https://4-20.shop/',
            'Brand66Shop': 'https://brand66shop.ru/',
            'Корт': 'https://xn--j1aigi.com/',
            're:premium': 'https://ekt.stores-apple.com',
            'Девайс': 'https://xn----7sbbfjg4ac6ckif.xn--p1ai/',
            'Айстудио': 'https://ekb.istudio-shop.ru/'
        }
        self.last_parsed_products = {}  # {chat_id: [товары]}
        self.setup_handlers()
        self.comparison_data = {}  # {chat_id: {'products': [], 'current_store': None}}

    def setup_handlers(self):
        """Настройка обработчиков сообщений"""
        self.bot.message_handler(commands=['start'])(self.main)
        self.bot.message_handler(commands=['help'])(self.helps)
        self.bot.message_handler(commands=['website'])(self.website)
        self.bot.message_handler(commands=['category'])(self.product_category)
        self.bot.callback_query_handler(func=lambda call: call.data == 'clear_comparison')(self.clear_comparison)
        self.bot.callback_query_handler(func=lambda call: call.data == 'callback_help')(self.helps_callback)
        self.bot.callback_query_handler(func=lambda call: call.data == 'callback_info')(self.info_callback)

    def run(self):
        """Запуск бота"""
        self.bot.polling(none_stop=True)

    # Основные методы интерфейса
    def send_photo_with_caption(self, chat_id, photo_path, caption, parse_mode='html', reply_markup=None):
        with open(photo_path, 'rb') as photo:
            self.bot.send_photo(chat_id, photo, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)

    def create_inline_keyboard(self, buttons):
        markup = types.InlineKeyboardMarkup()
        for btn_text, btn_callback in buttons.items():
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=btn_callback))
        return markup

    def create_reply_keyboard(self, buttons, resize=True):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=resize)
        for btn_row in buttons:
            markup.row(*[types.KeyboardButton(btn) for btn in btn_row])
        return markup

    def main(self, message):
        inline_buttons = {
            'Помощь': 'callback_help',
            'Информация': 'callback_info'
        }
        inline_markup = self.create_inline_keyboard(inline_buttons)

        self.send_photo_with_caption(
            message.chat.id,
            'photo.png',
            f'<b>Привет, {message.from_user.first_name}.</b> Это <u>бот</u> сервиса - <em>PriceCheck!</em>',
            reply_markup=inline_markup
        )

        reply_buttons = [
            ['Найти товар'],
            ['Помощь']
        ]
        reply_markup = self.create_reply_keyboard(reply_buttons)

        self.bot.send_message(
            message.chat.id,
            '<b>Выберите один из вариантов:</b>',
            parse_mode='html',
            reply_markup=reply_markup
        )
        self.bot.register_next_step_handler(message, self.on_click)

    def on_click(self, message):
        if message.text == 'Помощь':
            self.helps(message)
        elif message.text == 'Открыть страницу ВК':
            self.website(message)
        elif message.text == 'Найти товар':
            self.product_category(message)

    def helps_callback(self, call):
        self.bot.send_message(call.message.chat.id, 'хелпа')

    def helps(self, message):
        self.bot.send_message(message.chat.id, 'хелпа')

    def info_callback(self, call):
        info_text = (
            'Наша система проводит автоматизированный мониторинг цен, чтобы вы всегда были в курсе изменений. \n'
            'Вам больше не нужно вручную проверять различные сайты — просто введите название товара, '
            'и PriceCheck предоставит вам всю необходимую информацию.')
        self.bot.send_message(call.message.chat.id, info_text)

    def website(self, message):
        webbrowser.open('https://vk.com/ankoppchik')

    # Методы для работы с магазинами
    def product_category(self, message):
        buttons = [
            ['Одежда и обувь', 'Техника'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            '<b>Выберите категорию товаров: </b>',
            parse_mode='html',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.click_catalog)

    def click_catalog(self, message):
        if message.text == 'Техника':
            self.web_technic(message)
        elif message.text == 'Одежда и обувь':
            self.web_clothes(message)
        elif message.text == 'Вернуться в Главное меню':
            self.main(message)
        elif message.text in ['re:premium', 'Девайс', 'Айстудио']:
            self.selected_store(message)
        elif message.text in ['4:20 Shop', 'Brand66Shop', 'Корт']:
            self.selected_store(message)
        else:
            self.bot.send_message(message.chat.id, 'Пожалуйста, выберите опцию из меню.')

    def web_technic(self, message):
        buttons = [
            ['re:premium', 'Девайс', 'Айстудио'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            '<b>Выберите интернет-магазин: </b>',
            parse_mode='html',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.click_catalog)

    def web_clothes(self, message):
        buttons = [
            ['4:20 Shop', 'Brand66Shop', 'Корт'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            '<b>Выберите интернет-магазин: </b>',
            parse_mode='html',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.click_catalog)

    def format_product_message(self, product_info):
        """Форматирует информацию о товаре в красивое сообщение"""
        message = "🛍️ <b>{name}</b>\n".format(name=product_info.get('name', 'Название не указано'))

        if 'price' in product_info:
            message += "💰 <b>Цена:</b> {price}\n".format(price=product_info['price'])

        if 'link' in product_info:
            message += "🔗 <a href='{link}'>Смотреть товар</a>\n".format(link=product_info['link'])

        if 'image' in product_info:
            message += "📸 <a href='{image}'>Фото товара</a>\n".format(image=product_info['image'])

        if 'sizes' in product_info and product_info['sizes']:
            message += "📏 <b>Размеры:</b> {sizes}\n".format(sizes=", ".join(product_info['sizes']))

        if 'description' in product_info and product_info['description']:
            message += "\n📝 <b>Описание:</b>\n{desc}\n".format(desc=product_info['description'])

        return message

    def selected_store(self, message):
        store = message.text
        self.bot.send_message(message.chat.id, f'Вы выбрали магазин: <b>{store}</b>', parse_mode='html')

        if message.chat.id not in self.comparison_data:
            self.comparison_data[message.chat.id] = {'products': [], 'current_store': None}
        self.comparison_data[message.chat.id]['current_store'] = store

        if store not in self.store_urls:
            self.bot.send_message(message.chat.id, 'Выбранный магазин не найден.')
            return

        selected_url = self.store_urls[store]

        response = None
        for _ in range(3):
            try:
                headers = {'user-agent': self.user_agent.random}
                response = requests.get(selected_url, headers=headers)
                if response.status_code == 200:
                    break
            except Exception as e:
                print(f"Ошибка при запросе к {store}: {e}")

        if not response or response.status_code != 200:
            self.bot.send_message(
                message.chat.id,
                f'Не удалось получить данные из <b>{store}</b>. Статус: {response.status_code if response else "нет ответа"}',
                parse_mode='html'
            )
            return

        if store == '4:20 Shop':
            self.handle_420_shop(message, response, store, selected_url)
        elif store == 'Brand66Shop':
            self.handle_brand66_shop(message, response, store, selected_url)
        elif store == 're:premium':
            self.handle_re_premium(message, response, store, selected_url)
        elif store == 'Девайс':
            self.handle_device_shop(message, response, store, selected_url)

    # Обработка магазина 4:20 Shop
    def handle_420_shop(self, message, response, store, base_url):
        buttons = [
            ['Обувь', 'Одежда'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какую категорию товаров вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.step_category_420(msg, response, store, base_url)
        )

    def step_category_420(self, message, response, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        if message.text == 'Обувь':
            self.parse_420_category(
                message, store, base_url,
                'https://4-20.shop/obuv/page-{count}/',
                'ty-column3',
                'ty-grid-list__item ty-quick-view-button__wrapper ty-grid-list__item--overlay',
                1, 18
            )
        elif message.text == 'Одежда':
            self.parse_420_category(
                message, store, base_url,
                'https://4-20.shop/odezhda/page-{count}/',
                'ty-column3',
                'ty-grid-list__item ty-quick-view-button__wrapper ty-grid-list__item--overlay',
                1, 275
            )

    def create_progress_bar(self, current, total, bar_length=10):
        """Создает текстовый прогресс-бар"""
        percent = float(current) / total
        arrow = '█' * int(round(percent * bar_length))
        spaces = '░' * (bar_length - len(arrow))
        return f"[{arrow}{spaces}] {current}/{total}"

    def parse_420_category(self, message, store, base_url, url_template, container_class, item_class, start_page,
                           end_page):
        self.bot.send_message(message.chat.id, f'Ищем {message.text} в {store}...')
        all_products = []  # Сохраняем все найденные товары
        chat_id = message.chat.id
        total_pages = end_page - start_page + 1
        progress_msg = self.bot.send_message(chat_id, "🔍 Начинаю сканирование...")
        try:
            for count in range(start_page, end_page + 1):
                link = url_template.format(count=count)
                try:
                    category_response = requests.get(link)
                    category_soup = BeautifulSoup(category_response.text, 'lxml')
                    containers = category_soup.find_all('div', class_=container_class)

                    for container in containers:
                        items = container.find_all('div', class_=item_class)
                        for item in items:
                            form = item.find('form')
                            if not form:
                                continue

                            name_block = form.find('div', class_='ty-grid-list__item-name')
                            name = name_block.find('span',
                                                   itemprop='name').text.strip().upper() if name_block else 'Название не найдено'

                            price_block = form.find('div', class_='ty-grid-list__price')
                            price = price_block.find('span',
                                                     itemprop='price').text.strip() if price_block else 'Цена не указана'

                            image_block = form.find('div', class_='ty-grid-list__image')
                            image = image_block.find('img', class_='ty-pict cm-image').get(
                                'src') if image_block else None

                            description = form.find('meta', itemprop='description')
                            description = description.get('content').replace(';',
                                                                             '; ') if description else 'Описание отсутствует'

                            link_block = image_block.find('a', itemprop='url') if image_block else None
                            product_link = link_block.get('href') if link_block else None

                            sizes = []
                            size_labels = form.find_all('label', class_='ty-product-options__radio--label')
                            for label in size_labels:
                                sizes.append(label.text.strip())

                            product_info = {
                                'name': name,
                                'price': price,
                                'link': product_link,
                                'image': image,
                                'sizes': sizes,
                                'description': description,
                                'store': store  # Добавляем магазин
                            }
                            all_products.append(product_info)

                except Exception as e:
                    print(f"Ошибка при парсинге страницы {count}: {e}")
                if count % 3 == 0 or count == end_page:  # Обновлять каждые 3 страницы или в конце
                    progress = self.create_progress_bar(count - start_page + 1, total_pages)
                    try:
                        self.bot.edit_message_text(f"🔍 Сканирование {store}...\n{progress}", chat_id=chat_id, message_id=progress_msg.message_id)
                    except:
                        pass  # Игнорируем ошибки редактирования
        finally:
            try:
                self.bot.delete_message(chat_id, progress_msg.message_id)
            except:
                pass

            # Сохраняем все найденные товары
            self.last_parsed_products[message.chat.id] = all_products
            self.offer_comparison(message)

    # Обработка магазина Brand66Shop
    def handle_brand66_shop(self, message, response, store, base_url):
        buttons = [
            ['Мужская обувь', 'Женская обувь'],
            ['Мужская одежда', 'Мужские зимние куртки'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какую категорию товаров вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.step_category_brand66(msg, response, store, base_url)
        )

    def step_category_brand66(self, message, response, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        category_urls = {
            'Мужская обувь': ('catalog/muzhskie', 1, 49),
            'Женская обувь': ('catalog/zhenskie', 1, 27),
            'Мужская одежда': ('catalog/muzhskaya-odezhda', 1, 5),
            'Мужские зимние куртки': ('catalog/muzhskie-zimnie-kurtki', 1, 1)
        }

        if message.text in category_urls:
            url_part, start_page, end_page = category_urls[message.text]
            self.parse_brand66_category(
                message, store, base_url,
                f'{base_url}{url_part}/?page={{count}}',
                'col-sm-4',
                'variants',
                start_page, end_page
            )
            print(f'{base_url}{url_part}/?page={{count}}')

    def parse_brand66_category(self, message, store, base_url, url_template, container_class, item_class, start_page,
                               end_page):
        self.bot.send_message(message.chat.id, f'Ищем {message.text} в {store}...')
        all_products = []
        chat_id = message.chat.id
        total_pages = end_page - start_page + 1
        progress_msg = self.bot.send_message(chat_id, "🔍 Начинаю сканирование...")

        try:
            for count in range(start_page, end_page + 1):
                link = url_template.format(count=count)
                try:
                    category_response = requests.get(link)
                    category_soup = BeautifulSoup(category_response.text, 'lxml')
                    containers = category_soup.find_all('div', class_=container_class)

                    for container in containers:
                        form = container.find('form', class_=item_class)
                        if not form:
                            continue

                        info_block = form.find('div', class_='info')
                        name = info_block.find('a', class_='name').text.strip() if info_block else 'Название не найдено'

                        price_block = info_block.find('p', class_='product-price') if info_block else None
                        price = price_block.contents[0].text.strip() if price_block else 'Цена не указана'

                        image_block = form.find('div', class_='image')
                        image = image_block.find('img').get('src') if image_block else None
                        product_link = image_block.find('a').get('href') if image_block else None

                        sizes = []
                        select_box = form.find('div', class_='select-box')
                        if select_box:
                            options = select_box.find_all('option')
                            for option in options:
                                if option.text.strip():
                                    sizes.append(option.text.strip())

                        product_info = {
                            'name': name,
                            'price': price,
                            'link': f"{base_url}{product_link}",
                            'image': image,
                            'sizes': sizes,
                            'store': store
                        }
                        all_products.append(product_info)

                except Exception as e:
                    print(f"Ошибка при парсинге страницы {count}: {e}")
                if count % 2 == 0 or count == end_page:  # Обновлять чаще для меньшего кол-ва страниц
                    progress = self.create_progress_bar(count - start_page + 1, total_pages)
                    try:
                        self.bot.edit_message_text(
                        f"🔍 Сканирование {store}...\n{progress}",
                        chat_id=chat_id,
                        message_id=progress_msg.message_id
                        )
                    except:
                        pass
        finally:
            try:
                self.bot.delete_message(chat_id, progress_msg.message_id)
            except:
                pass

        # Сохраняем все найденные товары
        self.last_parsed_products[message.chat.id] = all_products
        self.offer_comparison(message)

    # Обработка магазина Корт
    def handle_cort_shop(self, message, response, store, base_url):
        self.bot.send_message(message.chat.id, f'Модуль в разработке...')

    # Обработка магазина re:premium
    def handle_re_premium(self, message, response, store, base_url):
        buttons = [
            ['Телефоны', 'Планшеты', 'Смарт-часы и браслеты'],
            ['Mac', 'ТВ, консоли и аудио', 'Бытовая техника'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какую категорию товаров вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.step_category_re_premium(msg, response, store, base_url)
        )

    def step_category_re_premium(self, message, response, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        category_handlers = {
            'ТВ, консоли и аудио': self.handle_re_tv_category,
            'Бытовая техника': self.handle_re_appliances,
            'Смарт-часы и браслеты': self.handle_re_smartwatches,
            'Телефоны': self.handle_re_phones,
            'Планшеты': self.handle_re_tablets,
            'Mac': self.handle_re_mac
        }

        handler = category_handlers.get(message.text)
        if handler:
            handler(message, response, store, base_url)

    def handle_re_tv_category(self, message, response, store, base_url):
        buttons = [
            ['Playstation 5 Pro', 'PlayStation 5'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие товары из категории "ТВ, консоли и аудио" вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def handle_re_appliances(self, message, response, store, base_url):
        buttons = [
            ['Техника для дома', 'Красота и здоровье'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какую бытовую технику вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def handle_re_smartwatches(self, message, response, store, base_url):
        buttons = [
            ['Apple Watch', 'Samsung Galaxy Watch', 'Часы Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие смарт-часы и браслеты вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def handle_re_phones(self, message, response, store, base_url):
        buttons = [
            ['Apple iPhone', 'Samsung', 'Nothing Phone', 'Телефоны Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие телефоны вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def handle_re_tablets(self, message, response, store, base_url):
        buttons = [
            ['iPad Pro', 'iPad Air', 'iPad', 'iPad mini', 'Планшеты Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие планшеты вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def handle_re_mac(self, message, response, store, base_url):
        buttons = [
            ['MacBook Pro', 'Mac Studio', 'MacBook Air', 'iMac', 'Mac mini'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие устройства Mac вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_re_premium_category(msg, store, base_url)
        )

    def parse_re_premium_category(self, message, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        category_urls = {
            'Playstation 5': ('/catalog/tv_i_multimedia/konsoli_i_videoigry/playstation_5/', 1, 5),
            'Playstation 5 Pro': ('/catalog/tv_i_multimedia/konsoli_i_videoigry/playstation_5_pro/', 1, 5),
            'Техника для дома': ('/catalog/bytovaya_tekhnika/tekhnika-dlya-doma/', 1, 5),
            'Красота и здоровье': ('/catalog/bytovaya_tekhnika/krasota-i-zdorove/', 1, 5),
            'Apple Watch': ('/catalog/accessories/smart-chasy/', 1, 5),
            'Samsung Galaxy Watch': ('/catalog/accessories/smart-chasy-samsung/', 1, 5),
            'Часы Xiaomi': ('/catalog/accessories/fitnes-braslety/', 1, 5),
            'Apple iPhone': ('/catalog/iphones/', 1, 5),
            'Samsung': ('/catalog/telefony/samsung/', 1, 5),
            'Nothing Phone': ('/catalog/nothing_phone/', 1, 5),
            'Телефоны Xiaomi': ('/catalog/xiaomi/', 1, 5),
            'iPad Pro': ('/catalog/planshety/ipad_pro/', 1, 5),
            'iPad Air': ('/catalog/planshety/ipad_air/', 1, 5),
            'iPad': ('/catalog/planshety/ipad/', 1, 5),
            'iPad mini': ('/catalog/planshety/ipad_mini/', 1, 5),
            'Планшеты Xiaomi': ('/catalog/planshety/xiaomi/', 1, 5),
            'MacBook Pro': ('/catalog/mac/macbook_pro/?PAGEN_4=2', 1, 5),
            'Mac Studio': ('/catalog/mac/mac_studio/', 1, 5),
            'MacBook Air': ('/catalog/mac/macbook_air/', 1, 5),
            'iMac': ('/catalog/mac/imac/', 1, 5),
            'Mac mini': ('/catalog/mac/mac_mini/', 1, 5)
        }

        if message.text in category_urls:
            url_part, start_page, end_page = category_urls[message.text]
            self.parse_re_premium_products(message, store, base_url, f'{base_url}{url_part}/?PAGEN_4={{count}}', start_page, end_page)

    def parse_re_premium_products(self, message, store, base_url, url_template, start_page, end_page):
        chat_id = message.chat.id
        self.bot.send_message(chat_id, f'Ищем {message.text} в {store}...')
        all_products = []

        # Прогресс-бар
        progress_msg = self.bot.send_message(chat_id, "🔍 Начинаю сканирование...")

        try:
            for count in range(start_page, end_page + 1):
                # Формируем URL с пагинацией
                current_url = url_template.format(count=count)
                try:
                    response = requests.get(current_url)
                    soup = BeautifulSoup(response.text, 'lxml')
                    items = soup.find_all('div',
                                          class_='col-lg-3 col-md-4 col-sm-6 col-xs-12 col-xxs-12 item item-parent catalog-block-view__item js-notice-block item_block')

                    # Если товаров нет и это не первая страница - заканчиваем
                    if not items and count > start_page:
                        break

                    for item in items:
                        try:
                            card = item.find('div', class_='inner_wrap TYPE_1')
                            if not card:
                                continue

                            info = card.find('div', class_='item_info')
                            title = info.find('a',
                                              class_='dark_link js-notice-block__title option-font-bold font_sm') if info else None
                            name = title.find('span').text.upper() if title else 'Название не найдено'
                            product_link = title.get('href') if title else None

                            price = info.find('span', class_='price_value').text if info and info.find('span',
                                                                                                       class_='price_value') else "Товар доступен только по предзаказу"

                            image = card.find('img').get('data-src') if card.find('img') else None

                            product_info = {
                                'name': name,
                                'price': price,
                                'link': f"{base_url}{product_link}",
                                'image': f"{base_url}{image}" if image else None,
                                'store': store
                            }
                            all_products.append(product_info)
                            print(product_info)
                        except Exception as e:
                            print(f"Ошибка при обработке товара: {e}")
                            continue

                    # Обновляем прогресс
                    progress = self.create_progress_bar(count - start_page + 1, end_page - start_page + 1)
                    try:
                        self.bot.edit_message_text(
                            f"🔍 Сканирование {store}...\n{progress}",
                            chat_id=chat_id,
                            message_id=progress_msg.message_id
                        )
                    except:
                        pass

                except Exception as e:
                    print(f"Ошибка при загрузке страницы {count}: {e}")
                    continue

        except Exception as e:
            print(f"Ошибка при парсинге категории: {e}")
        finally:
            try:
                self.bot.delete_message(chat_id, progress_msg.message_id)
            except:
                pass

        self.last_parsed_products[message.chat.id] = all_products
        self.offer_comparison(message)

    # Обработка магазина Девайс
    def handle_device_shop(self, message, response, store, base_url):
        buttons = [
            ['Телефоны', 'Планшеты', 'Смарт-часы и браслеты'],
            ['Ноутбуки и компьютеры', 'ТВ, консоли и аудио'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какую категорию товаров вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.step_category_device(msg, response, store, base_url)
        )

    def step_category_device(self, message, response, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        category_handlers = {
            'ТВ, консоли и аудио': self.handle_device_tv_category,
            'Смарт-часы и браслеты': self.handle_device_smartwatches,
            'Ноутбуки и компьютеры': self.handle_device_computers,
            'Планшеты': self.handle_device_tablets,
            'Телефоны': self.handle_device_phones
        }

        handler = category_handlers.get(message.text)
        if handler:
            handler(message, response, store, base_url)

    def handle_device_tv_category(self, message, response, store, base_url):
        buttons = [
            ['Sony', 'Xbox'],
            ['Steam Deck', 'Nintendo'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие товары из категории "ТВ, консоли и аудио" вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_device_products(msg, store, base_url)
        )

    def handle_device_smartwatches(self, message, response, store, base_url):
        buttons = [
            ['Apple Watch', 'Hoco', 'Часы Samsung', 'Часы Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие смарт-часы и браслеты вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_device_products(msg, store, base_url)
        )

    def handle_device_computers(self, message, response, store, base_url):
        buttons = [
            ['Apple iMac', 'Apple MacBook'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие компьютеры вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_device_products(msg, store, base_url)
        )

    def handle_device_tablets(self, message, response, store, base_url):
        buttons = [
            ['Apple iPad', 'Планшеты Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие планшеты вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_device_products(msg, store, base_url)
        )

    def handle_device_phones(self, message, response, store, base_url):
        buttons = [
            ['Apple iPhone', 'Samsung', 'Nothing Phone', 'Телефоны Xiaomi'],
            ['Вернуться в Главное меню']
        ]
        markup = self.create_reply_keyboard(buttons)

        self.bot.send_message(
            message.chat.id,
            f'Какие телефоны вы хотите найти в {store}?',
            reply_markup=markup
        )
        self.bot.register_next_step_handler(
            message,
            lambda msg: self.parse_device_products(msg, store, base_url)
        )

    def parse_device_category(self, message, store, base_url, url_template, item_class, start_page, end_page):
        """Парсинг товаров из магазина Девайс"""
        self.bot.send_message(message.chat.id, f'Ищем {message.text} в {store}...')
        all_products = []
        chat_id = message.chat.id
        total_pages = end_page - start_page + 1
        progress_msg = self.bot.send_message(chat_id, "🔍 Начинаю сканирование...")
        try:
            for count in range(start_page, end_page + 1):
                link = url_template.format(count=count)
                try:
                    response = requests.get(link)
                    soup = BeautifulSoup(response.text, 'lxml')
                    items = soup.find_all('div', class_=item_class)

                    for item in items:
                        title = item.find('div', class_='item__title')
                        if not title:
                            continue

                        product_link = title.find('a').get('href')
                        product_link = product_link[1:]
                        name = title.find('a').text.strip().upper()

                        price = item.find('div', class_='price_').text.strip() if item.find('div',
                                                                                            class_='price_') else 'Цена не указана'

                        image_container = item.find('div', class_='item__img')
                        image = image_container.find('img').get('src') if image_container else None
                        image = image[1:]

                        product_info = {
                            'name': name,
                            'price': price,
                            'link': f"{base_url}{product_link}",
                            'image': f"{base_url}{image}" if image else None,
                            'store': store
                        }
                        all_products.append(product_info)

                except Exception as e:
                    print(f"Ошибка при парсинге страницы: {e}")
                progress = self.create_progress_bar(count - start_page + 1, total_pages)
                try:
                    self.bot.edit_message_text(
                        f"🔍 Сканирование {store}...\n{progress}",
                        chat_id=chat_id,
                        message_id=progress_msg.message_id
                    )
                except:
                    pass

        finally:
            try:
                self.bot.delete_message(chat_id, progress_msg.message_id)
            except:
                pass

        # Сохраняем все найденные товары
        self.last_parsed_products[message.chat.id] = all_products
        self.offer_comparison(message)

    def parse_device_products(self, message, store, base_url):
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
            return

        category_urls = {
            'Nintendo': ('catalog/nintendo/?PAGEN_2={count}', 1, 2),
            'Steam Deck': ('catalog/steam_deck/?PAGEN_2={count}', 1, 2),
            'Xbox': ('catalog/xbox/?PAGEN_2={count}', 1, 2),
            'Sony': ('catalog/sony_%20PS/?PAGEN_2={count}', 1, 3),
            'Apple Watch': ('catalog/apple_watch/?PAGEN_2={count}', 1, 5),
            'Hoco': ('catalog/hoco/?PAGEN_2={count}', 1, 2),
            'Часы Samsung': ('catalog/samsung_smart/?PAGEN_2={count}', 1, 2),
            'Часы Xiaomi': ('catalog/syaomi_smart/?PAGEN_2={count}', 1, 2),
            'Apple iMac': ('catalog/apple_imac/?PAGEN_2={count}', 1, 3),
            'Apple MacBook': ('catalog/apple_macbook/?PAGEN_2={count}', 1, 6),
            'Apple iPad': ('catalog/Apple_iPad/?PAGEN_2={count}', 1, 10),
            'Планшеты Xiaomi': ('catalog/syaomi_planshet/?PAGEN_2={count}', 1, 3),
            'Apple iPhone': ('catalog/telefony/filter/brand_ref-is-apple/apply/?PAGEN_2={count}', 1, 10),
            'Samsung': ('catalog/samsung/?PAGEN_2={count}', 1, 10),
            'Nothing Phone': ('catalog/nothing/?PAGEN_2={count}', 1, 2),
            'Телефоны Xiaomi': ('catalog/syaomi/?PAGEN_2={count}', 1, 8)
        }

        if message.text in category_urls:
            url_part, start_page, end_page = category_urls[message.text]
            self.parse_device_category(
                message, store, base_url,
                f'{base_url}{url_part}',
                'catalog__item flex hidden-xs',
                start_page, end_page
            )
        else:
            self.bot.send_message(
                message.chat.id,
                "🔍 Товары не найдены. Попробуйте другую категорию.",
                parse_mode='HTML'
            )

    def offer_comparison(self, message):
        """Предлагаем добавить товары в сравнение"""
        chat_id = message.chat.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('Добавить товар в сравнение')
        markup.row('Показать сравнение', 'Очистить сравнение')
        markup.row('Вернуться в Главное меню')

        self.bot.send_message(
            chat_id,
            "Вы можете добавить товары в сравнение из разных магазинов.\n"
            "Введите точное название товара для добавления:",
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.handle_comparison_actions)

    def handle_comparison_actions(self, message):
        chat_id = message.chat.id
        if message.text == 'Вернуться в Главное меню':
            self.main(message)
        elif message.text == 'Добавить товар в сравнение':
            self.bot.send_message(
                chat_id,
                "Введите точное название товара, который хотите добавить:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.bot.register_next_step_handler(message, self.add_to_comparison)
        elif message.text == 'Показать сравнение':
            self.show_comparison(message)
        elif message.text == 'Очистить сравнение':
            self.clear_comparison(message)
        else:
            self.bot.send_message(chat_id, "Пожалуйста, выберите действие из меню.")
            self.offer_comparison(message)

    def add_to_comparison(self, message):
        chat_id = message.chat.id
        product_name = message.text.strip()

        # Проверяем есть ли товары для сравнения
        if chat_id not in self.last_parsed_products or not self.last_parsed_products[chat_id]:
            self.bot.send_message(chat_id, "Сначала найдите товары через поиск!")
            return self.main(message)

        # Ищем товары по названию
        found_products = [
            p for p in self.last_parsed_products[chat_id]
            if product_name.lower() in p['name'].lower()
        ]

        if not found_products:
            self.bot.send_message(chat_id, "Товар не найден. Попробуйте другое название.")
            return self.offer_comparison(message)

        # Берем первый найденный товар
        product = found_products[0]
        store = self.comparison_data[chat_id]['current_store']

        # Проверяем дубликаты
        if any(p['link'] == product['link'] for p in self.comparison_data[chat_id]['products']):
            self.bot.send_message(chat_id, "Этот товар уже добавлен!")
            return self.offer_comparison(message)

        # Добавляем товар
        self.comparison_data[chat_id]['products'].append({
            'name': product['name'],
            'price': product['price'],
            'link': product['link'],
            'store': store
        })

        self.bot.send_message(
            chat_id,
            f"✅ {product['name']} из {store} добавлен!\n"
            f"Цена: {product['price']}"
        )

        self.offer_comparison(message)

    def show_comparison(self, message):
        """Показ сравнения товаров из разных магазинов"""
        chat_id = message.chat.id

        if chat_id not in self.comparison_data or not self.comparison_data[chat_id]['products']:
            self.bot.send_message(chat_id, "Ваш список сравнения пуст!")
            return self.offer_comparison(message)

        # Группируем товары по имени для сравнения
        products_by_name = {}
        for product in self.comparison_data[chat_id]['products']:
            if product['name'] not in products_by_name:
                products_by_name[product['name']] = []
            products_by_name[product['name']].append(product)

        # Формируем сообщение сравнения
        comparison_text = "<b>🛒 Сравнение товаров:</b>\n\n"

        for product_name, variants in products_by_name.items():
            comparison_text += f"<b>📌 {product_name}</b>\n"

            for variant in sorted(variants, key=lambda x: (x['price'].replace(' ', '').replace('₽', ''))):
                comparison_text += (
                    f"   🏪 <b>{variant['store']}</b>\n"
                    f"   💵 {variant['price']}\n"
                    f"   🔗 <a href='{variant['link']}'>Ссылка</a>\n\n"
                )
            comparison_text += "────────────────────\n"

        # Кнопки управления
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Очистить список", callback_data='clear_comparison'),
        )

        self.bot.send_message(
            chat_id,
            comparison_text,
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=markup
        )

        self.offer_comparison(message)

    def clear_comparison(self, message_or_call):
        """Очистка списка сравнения"""
        if isinstance(message_or_call, types.CallbackQuery):
            chat_id = message_or_call.message.chat.id
            self.bot.answer_callback_query(message_or_call.id)
        else:
            chat_id = message_or_call.chat.id

        if chat_id in self.comparison_data:
            self.comparison_data[chat_id]['products'] = []
            self.bot.send_message(chat_id, "Список сравнения очищен!")
        else:
            self.bot.send_message(chat_id, "Ваш список сравнения уже пуст!")

        self.offer_comparison(
            message_or_call.message if isinstance(message_or_call, types.CallbackQuery) else message_or_call)


# Запуск бота
if __name__ == '__main__':
    token = '7913291493:AAEy7bH-r3iyomgcpgoheTwmcZueuKXWNfw'
    bot = PriceCheckBot(token)
    bot.run()
