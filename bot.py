import logging, requests, sqlite3, telebot
from telebot import types
from bs4 import BeautifulSoup

bot = telebot.TeleBot('405295345:AAEiq-A3mEVsE203a0qOM3z2QCpPOlMKbZ0')
logger = telebot.logger
telebot.logger.setLevel(logging.ERROR)

nmaps_chat = '-1001136617457'
mods_chat = '-240980847'
roads_chat = '-227479062'

db = sqlite3.connect('database.db')
c = db.cursor()
c.execute('CREATE TABLE IF NOT EXISTS roads (username text, chat_message_id text, mods_message_id text, roads_message_id text)')
c.execute('CREATE TABLE IF NOT EXISTS banned (username text)')
db.commit()
c.close()
db.close()


def private_chat(message):
    if message.chat.type == 'private':
        return True


@bot.message_handler(commands=['start', 'home'])
def home(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row('📌 Полезные ссылки')
    keyboard.row('🔎 Поиск в Клубе', '🔎 Поиск в Правилах')
    keyboard.row('🚫 Сообщить о перекрытии')
    keyboard.row('📚 Частые вопросы', '✏ Служба поддержки')
    bot.send_message(message.chat.id, 'Пожалуйста, выберите действие.', reply_markup=keyboard)


@bot.message_handler(regexp='📌 Полезные ссылки')
def bookmarks(message):
    if not private_chat(message):
        return
    keyboard = types.InlineKeyboardMarkup()
    url1 = types.InlineKeyboardButton(text='Правила', url='https://yandex.ru/support/nmaps/rules_2.html')
    url2 = types.InlineKeyboardButton(text='Клуб', url='https://yandex.ru/blog/narod-karta')
    url3 = types.InlineKeyboardButton(text='ПКК', url='https://pkk5.rosreestr.ru/')
    url4 = types.InlineKeyboardButton(text='ФИАС', url='https://fias.nalog.ru/')
    url5 = types.InlineKeyboardButton(text='ЕГРП365', url='https://egrp365.ru/map/')
    url6 = types.InlineKeyboardButton(text='TerraServer', url='https://www.terraserver.com/')
    url7 = types.InlineKeyboardButton(text='Реформа ЖКХ', url='https://www.reformagkh.ru/')
    keyboard.add(url1, url2, url3, url4, url5, url6, url7)
    bot.send_message(message.chat.id, 'Для перехода на сайт нажмите нужную кнопку из списка.', reply_markup=keyboard)
    home(message)


@bot.message_handler(regexp='🔎 Поиск')
def search(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row('⬅ Вернуться')
    bot.send_message(message.chat.id, 'Напишите фразу для поиска.', reply_markup=keyboard)
    if message.text == '🔎 Поиск в Правилах':
        bot.register_next_step_handler(message, search_rules)
    elif message.text == '🔎 Поиск в Клубе':
        bot.register_next_step_handler(message, search_club)
    elif message.text == '⬅ Вернуться':
        home(message)


def search_club(message):
    if message.text == '⬅ Вернуться':
        home(message)
        return
    page = requests.get('https://yandex.ru/blog/narod-karta/search?text=' + message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='b-serp-item'):
        pass
        title = item.find('h2').text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + ')\n'
        answer += '____________________\n'
    if not answer:
        bot.send_message(message.chat.id, 'К сожалению, ничего не найдено.')
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown', disable_web_page_preview=True)
    home(message)


def search_rules(message):
    if message.text == '⬅ Вернуться':
        home(message)
        return
    page = requests.get('https://yandex.ru/support/search-results/?text=' + message.text.replace(' ', '+') + '&service=nmaps-guide')
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='serp__item'):
        if '...' in item.find_all('div')[0].text:
            title = item.find_all('div')[0].text.split('...')[0]
        else:
            title = item.find_all('div')[0].text.split('—')[0]
        excerpt = item.find_all('div')[1].text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + '): ' + excerpt + '\n'
        answer += '____________________\n'
    if not answer:
        bot.send_message(message.chat.id, 'К сожалению, ничего не найдено.')
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown', disable_web_page_preview=True)
    home(message)


@bot.message_handler(content_types=['text'])
def roads(message):
    if '#перекрытие' in message.text:
        db = sqlite3.connect('database.db')
        c = db.cursor()
        c.execute('SELECT username FROM banned WHERE username = ?', [str(message.from_user.username)])
        if c.fetchall():
            bot.reply_to(message, 'Вы были внесены в черный список и не можете передавать сообщения.')
            return

        bot.send_message(message.chat.id, '@' + message.from_user.username + ', сообщение принято. Спасибо!')

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(text='↩ Передать сотрудникам', callback_data='road_mod_approve'))
        keyboard.row(types.InlineKeyboardButton(text='🔫 Запросить информацию', callback_data='road_mod_request_info'))
        keyboard.row(types.InlineKeyboardButton(text='🚫 Вандализм', callback_data='road_mod_ban'))
        mods_message = bot.send_message(mods_chat, 'Пользователь @' + message.from_user.username + ' оставил следующее сообщение. Просьба проверить информацию.', reply_markup=keyboard)
        bot.forward_message(mods_chat, nmaps_chat, message.message_id)
        c.execute('INSERT INTO roads VALUES (?, ?, ?, ?)', [str(message.from_user.username), str(message.message_id), str(mods_message.message_id), str(0)])
        db.commit()
        db.close()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    db = sqlite3.connect('database.db')
    c = db.cursor()

    if call.data == 'road_mod_approve':
        bot.edit_message_text('✅ Направлено сотрудникам', chat_id=call.message.chat.id, message_id=call.message.message_id)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(text='🚧 Перекрытие установлено', callback_data='road_closed'))
        keyboard.row(types.InlineKeyboardButton(text='🚗 Перекрытие снято', callback_data='road_opened'))
        keyboard.row(types.InlineKeyboardButton(text='⚠ Инфоточка установлена', callback_data='info_added'))
        keyboard.row(types.InlineKeyboardButton(text='🔫 Запросить информацию', callback_data='road_request_info'))
        roads_message = bot.send_message(roads_chat, 'Добрый день. Появилась новая информация о перекрытии.', reply_markup=keyboard)

        c.execute('SELECT chat_message_id FROM roads WHERE mods_message_id = ?', [str(call.message.message_id)])
        chat_message_id = c.fetchall()[0][0]
        bot.forward_message(roads_chat, nmaps_chat, chat_message_id)

        c.execute('UPDATE roads SET roads_message_id = ? WHERE chat_message_id = ?', [str(roads_message.message_id), str(chat_message_id)])
    elif call.data == 'road_mod_request_info':
        bot.edit_message_text('📋 Ожидается информация', chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == 'road_mod_ban':
        bot.edit_message_text('🚫 Пользователь заблокирован', chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('INSERT INTO banned SELECT username FROM roads WHERE mods_message_id = ?', [str(call.message.message_id)])
    elif call.data == 'road_closed':
        bot.edit_message_text('✅ Перекрытие установлено', chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = ?', [call.message.message_id])
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, 'Перекрытие установлено, спасибо!', reply_to_message_id=chat_message_id)
    elif call.data == 'road_opened':
        bot.edit_message_text('✅ Перекрытие снято', chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = ?', [call.message.message_id])
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, 'Перекрытие снято, спасибо!', reply_to_message_id=chat_message_id)
    elif call.data == 'info_added':
        bot.edit_message_text('✅ Инфоточка установлена', chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = ?', [call.message.message_id])
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, 'Инфоточка установлена, спасибо!', reply_to_message_id=chat_message_id)
    elif call.data == 'road_request_info':
        bot.edit_message_text('📋 Ожидается информация', chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('INSERT INTO banned SELECT username FROM roads WHERE mods_message_id = ?', [str(call.message.message_id)])

    db.commit()
    db.close()


if __name__ == '__main__':
    bot.polling()
