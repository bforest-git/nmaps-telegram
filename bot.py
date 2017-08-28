import logging, requests, psycopg2, telebot
from telebot import types
from phrases import *
from bs4 import BeautifulSoup

bot = telebot.TeleBot('405295345:AAEiq-A3mEVsE203a0qOM3z2QCpPOlMKbZ0')
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
db_creds = {'dbname': 'bot',
            'user': 'ubuntu',
            'password': 'sas'}

nmaps_chat = '-1001136617457'
mods_chat = '-240980847'
roads_chat = '-227479062'

kbrd_btn = types.InlineKeyboardButton

db = psycopg2.connect(**db_creds)
c = db.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS roads (username text,
                                               chat_message_id bigint,
                                               mods_message_id bigint,
                                               roads_message_id bigint)''')
c.execute('CREATE TABLE IF NOT EXISTS banned (username text)')
db.commit()
db.close()


def private_chat(message):
    return message.chat.type == 'private'


@bot.message_handler(commands=['start', 'home'])
def home(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
               one_time_keyboard=True)
    keyboard.row(MENU_LINKS)
    keyboard.row(MENU_SEARCH_CLUB, MENU_SEARCH_RULES)
    keyboard.row(MENU_ROADS)
    keyboard.row(MENU_FAQ, MENU_SUPPORT)
    bot.send_message(message.chat.id,
                     BOT_ACTION_SELECT,
                     reply_markup=keyboard)

@bot.message_handler(regexp=MENU_LINKS)
def bookmarks(message):
    if not private_chat(message):
        return
    keyboard = types.InlineKeyboardMarkup()

    url1 = kbrd_btn(text='Правила',
                    url='https://yandex.ru/support/nmaps/rules_2.html')
    url2 = kbrd_btn(text='Клуб',
                    url='https://yandex.ru/blog/narod-karta')
    url3 = kbrd_btn(text='ПКК',
                    url='https://pkk5.rosreestr.ru/')
    url4 = kbrd_btn(text='ФИАС',
                    url='https://fias.nalog.ru/')
    url5 = kbrd_btn(text='ЕГРП365',
                    url='https://egrp365.ru/map/')
    url6 = kbrd_btn(text='TerraServer',
                    url='https://www.terraserver.com/')
    url7 = kbrd_btn(text='Реформа ЖКХ',
                    url='https://www.reformagkh.ru/')
    keyboard.add(url1, url2, url3, url4, url5, url6, url7)
    bot.send_message(message.chat.id,
                     BOT_CHS_LINK,
                     reply_markup=keyboard)
    home(message)


@bot.message_handler(regexp=MENU_SEARCH)
def search(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.row(MENU_RETURN)
    bot.send_message(message.chat.id,
                     BOT_SRCH_QUERY,
                     reply_markup=keyboard)
    if message.text == MENU_SEARCH_RULES:
        bot.register_next_step_handler(message, search_rules)
    elif message.text == MENU_SEARCH_CLUB:
        bot.register_next_step_handler(message, search_club)
    elif message.text == MENU_RETURN:
        home(message)


def search_club(message):
    if message.text == MENU_RETURN:
        home(message)
        return
    page = requests.get('https://yandex.ru/blog/narod-karta/search?text=' +
                        message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='b-serp-item'):
        title = item.find('h2').text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + ')\n'
        answer += '____________________\n'
    if not answer:
        bot.send_message(message.chat.id, BOT_NOT_FOUND)
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown',
                         disable_web_page_preview=True)
    home(message)


def search_rules(message):
    if message.text == MENU_RETURN:
        home(message)
        return
    page = requests.get('https://yandex.ru/support/search-results/?text=' +
                        message.text.replace(' ', '+') +
                        '&service=nmaps-guide')
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
        bot.send_message(message.chat.id, BOT_NOT_FOUND)
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown',
                         disable_web_page_preview=True)
    home(message)


@bot.message_handler(content_types=['text'])
def roads(message):
    if '#перекрытие' in message.text:
        bot.send_message(message.chat.id,
                         BOT_MSG_ACCEPT.format(message.from_user.username))

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_ACCEPT,
                              callback_data='road_mod_approve'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_REQUEST_INFO,
                              callback_data='road_mod_request_info'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_FRAUD,
                              callback_data='road_mod_ban'))
        mods_message = bot.send_message(mods_chat,
                                        BOT_REQUEST_CHECK.format(message.from_user.username), reply_markup=keyboard)
        bot.forward_message(mods_chat, nmaps_chat, message.message_id)
        db = psycopg2.connect(**db_creds)
        c = db.cursor()
        c.execute('INSERT INTO roads VALUES (%s, %s, %s, %s)',
                  (message.from_user.username, message.message_id,
                   mods_message.message_id, 0))
        db.commit()
        db.close()


@bot.callback_query_handler(func=lambda call: True)
def roads_callback(call):
    db = psycopg2.connect(**db_creds)
    c = db.cursor()

    if call.data == 'road_mod_approve':
        bot.edit_message_text(BOT_SENT_TO_STAFF,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_CLOSED,
                              callback_data='road_closed'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_OPENED,
                              callback_data='road_opened'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_INFOPOINT,
                              callback_data='info_added'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_REQUEST_INFO,
                              callback_data='road_request_info'))
        roads_message = bot.send_message(roads_chat,
                                         BOT_NEW_ROADBLOCK,
                                         reply_markup=keyboard)

        c.execute('SELECT chat_message_id FROM roads WHERE mods_message_id = %s', (call.message.message_id,))
        chat_message_id = c.fetchall()[0][0]
        bot.forward_message(roads_chat, nmaps_chat, chat_message_id)

        c.execute('UPDATE roads SET roads_message_id = %s WHERE chat_message_id = %s', (roads_message.message_id, chat_message_id,))
    elif call.data == 'road_mod_request_info':
        bot.edit_message_text(BOT_WAIT_FOR_INFO, chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == 'road_mod_ban':
        bot.edit_message_text(BOT_USER_BANNED, chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('INSERT INTO banned VALUES (SELECT username FROM roads WHERE mods_message_id = %s)', (call.message.message_id,))
    elif call.data == 'road_closed':
        bot.edit_message_text(BOT_ROADBLOCK_SET, chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = %s', (call.message.message_id,))
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, BOT_ROADBLOCK_SET_USR, reply_to_message_id=chat_message_id)
    elif call.data == 'road_opened':
        bot.edit_message_text(BOT_ROADBLOCK_DEL, chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = %s', (call.message.message_id,))
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, BOT_ROADBLOCK_DEL_USR, reply_to_message_id=chat_message_id)
    elif call.data == 'info_added':
        bot.edit_message_text(BOT_INFOPOINT_SET, chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('SELECT chat_message_id FROM roads WHERE roads_message_id = %s', (call.message.message_id,))
        chat_message_id = c.fetchall()
        bot.send_message(nmaps_chat, BOT_INFOPOINT_SET_USR, reply_to_message_id=chat_message_id)
    elif call.data == 'road_request_info':
        bot.edit_message_text(BOT_WAIT_FOR_INFO, chat_id=call.message.chat.id, message_id=call.message.message_id)
        c.execute('INSERT INTO banned SELECT username FROM roads WHERE mods_message_id = %s', (call.message.message_id,))

    db.commit()
    db.close()


if __name__ == '__main__':
    bot.polling()
