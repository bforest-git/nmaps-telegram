import logging
import math
import os
import psycopg2
import re
import requests
import telebot
from bs4 import BeautifulSoup
types = telebot.types

from capturer import Capturer, IllegalURL
from phrases import *


class Prefix:
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, call):
        return call.data.startswith(self.prefix)


bot = telebot.TeleBot(os.getenv('TLGAPIKEY', '331488080:AAH8PEA9WnsZtFubYnwFI5EWDq1fvqb9ZAE'))
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

db_creds = {'host': os.getenv('DBHOST', 'localhost'),
            'dbname': os.getenv('DBNAME', 'bot'),
            'user': os.getenv('DBUSER', 'ubuntu'),
            'password': os.getenv('DBPASS', 'bot')}

nmaps_chat = int(os.getenv('NMAPSCHAT', '-1001136617457'))
mods_chat = int(os.getenv('MODSCHAT', '-240980847'))
roads_chat = int(os.getenv('ROADSCHAT', '-227479062'))

alexfox = 30375360

staff = ['Borodin', 'Kalashnikov', 'expertSerg', 'Khudozhnikov', 'Soloviev', 'Kruzhalov']

kbrd_btn = types.InlineKeyboardButton

db = psycopg2.connect(**db_creds)
c = db.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS roads (username text,
                                               chat_id bigint,
                                               chat_message_id bigint,
                                               mods_message_id bigint,
                                               roads_message_id bigint)''')

c.execute('''CREATE TABLE IF NOT EXISTS banned (username text primary key)''')
c.execute('''CREATE TABLE IF NOT EXISTS admins (username text primary key)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (option text unique, value text)''')
c.execute('''CREATE TABLE IF NOT EXISTS subscribers (tlg_id bigint primary key, is_subscribed integer)''')

try:
    c.execute('INSERT INTO settings VALUES (%s, %s)', ('roads_moderation', 'enabled'))
except psycopg2.IntegrityError:
    pass

db.commit()
c.close()

cpt = Capturer()


def private_chat(message):
    return message.chat.type == 'private'


def is_admin(user):
    c = db.cursor()
    c.execute('''SELECT username FROM admins
                 WHERE username = %s''', (user,))
    is_adm = c.fetchone() is not None
    return is_adm


def subscribed(telegram_id):
    c = db.cursor()
    c.execute('''SELECT is_subscribed FROM subscribers
                 WHERE tlg_id = %s''', (telegram_id,))
    is_subscribed = c.fetchone()
    if is_subscribed is None:
        try:
            c.execute('''INSERT INTO subscribers VALUES (%s, %s)''', (telegram_id, '0'))
            db.commit()
        except psycopg2.IntegrityError:
            pass
    return is_subscribed is not None and is_subscribed[0] == 1


def full_name(user):
    return user.first_name + ' ' + user.last_name


@bot.message_handler(commands=['start', 'home'])
def home(message, user_override=None):
    if not private_chat(message):
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.row(MENU_LINKS)
    keyboard.row(MENU_SEARCH_CLUB, MENU_SEARCH_RULES)
    keyboard.row(MENU_ROADS, MENU_FEEDBACK)
    if subscribed(message.from_user.id):
        keyboard.row(MENU_UNSUBSCRIBE)
    else:
        keyboard.row(MENU_SUBSCRIBE)
    if is_admin(user_override or message.from_user.username):
        keyboard.row(MENU_FAQ, MENU_SUPPORT)
        keyboard.row(MENU_SETTINGS)
    bot.send_message(message.chat.id,
                     BOT_ACTION_SELECT,
                     reply_markup=keyboard)


@bot.message_handler(regexp=MENU_SETTINGS)
def settings(message):
    keyboard = types.InlineKeyboardMarkup()
    c = db.cursor()
    c.execute('''SELECT value FROM settings
                 WHERE option = 'roads_moderation' ''')

    if c.fetchone()[0] == 'disabled':
        keyboard.row(kbrd_btn(text=PREF_MOD_ON,
                              callback_data='prefs_mod_on'))
    else:
        keyboard.row(kbrd_btn(text=PREF_MOD_OFF,
                              callback_data='prefs_mod_off'))
    keyboard.row(kbrd_btn(text=PREF_ADMINS,
                          callback_data='prefs_admins'))
    keyboard.row(kbrd_btn(text=MENU_UNBAN,
                          callback_data='unbanpage_0'))
    keyboard.row(kbrd_btn(text=MENU_RETURN,
                          callback_data='prefs_return'))

    bot.send_message(message.chat.id,
                     PREF_DESC,
                     reply_markup=keyboard)

    c.close()


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
    page = requests.get('https://yandex.ru/support/search-results/?service=nmaps&query=' +
                        message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('div', class_='results__item'):
        if item.find_all('div')[1].text != 'Народная карта':
            continue
        title = item.find('div').text.replace('&nbsp;', ' ')
        link = 'https://yandex.ru/support/' + item.attrs['data-document']
        text = item.find_all('div')[2].text
        answer += '[' + title + '](' + link + ')\n'
        answer += '```' + text + '```\n'
        answer += '____________________\n'
    if not answer:
        bot.send_message(message.chat.id, BOT_NOT_FOUND)
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown',
                         disable_web_page_preview=True)
    home(message)


@bot.message_handler(regexp=MENU_ROADS)
def report_roads(message):
    if not private_chat(message):
        return
    bot.send_message(message.chat.id, BOT_PRIVATE_ROAD_REPORT_USR)
    home(message)


@bot.message_handler(regexp=MENU_FEEDBACK)
def feedback(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.row(MENU_RETURN)
    bot.send_message(message.chat.id, BOT_SEND_FEEDBACK_USR, reply_markup=keyboard)
    bot.register_next_step_handler(message, send_feedback)


def send_feedback(message):
    if message.text != MENU_RETURN:
        bot.send_message(alexfox, message.text)
        bot.send_message(message.chat.id, BOT_FEEDBACK_SENT_USR)
    home(message)


@bot.message_handler(regexp=MENU_SUBSCRIBE)
def subscribe(message):
    c = db.cursor()
    c.execute('''UPDATE subscribers SET is_subscribed = 1 WHERE tlg_id = %s''', (message.from_user.id,))
    db.commit()
    bot.send_message(message.chat.id, BOT_SUBSCRIBED_USR)
    home(message)


@bot.message_handler(regexp=MENU_UNSUBSCRIBE)
def unsubscribe(message):
    c = db.cursor()
    c.execute('''UPDATE subscribers SET is_subscribed = 0 WHERE tlg_id = %s''', (message.from_user.id,))
    db.commit()
    bot.send_message(message.chat.id, BOT_UNSUBSCRIBED_USR)
    home(message)


def add_admin(message):
    c = db.cursor()
    try:
        c.execute('''INSERT INTO admins VALUES (%s)''',
                  (message.text.strip('@'), ))
    except psycopg2.IntegrityError:
        bot.send_message(message.chat.id, PREF_ALREADY_ADMIN_USR)
        home(message)
        return
    db.commit()
    c.close()
    bot.send_message(message.chat.id, PREF_ADDED_ADMIN_USR)
    home(message, user_override=message.from_user.username)


def del_admin(message):
    c = db.cursor()
    c.execute('''DELETE FROM admins WHERE username = %s''',
              (message.text.strip('@'), ))
    db.commit()
    c.close()
    bot.send_message(message.chat.id, PREF_DELED_ADMIN_USR)
    home(message, user_override=message.from_user.username)


hashtags = re.compile('#({}|{})'.format(HASH_SCREEN, HASH_ROADBLOCK),
                      flags=re.I | re.U)


@bot.message_handler(content_types=['text'])
def roads(message):
    if message.from_user.username == 'combot':
        bot.delete_message(message.chat.id, message.id)

    tag = hashtags.search(message.text)
    if tag is None:
        return

    if tag.group(1).lower() == HASH_SCREEN:
        url = None
        for i in message.text.split():
            if i.startswith('http'):
                url = i
                break
        if url is not None:
            try:
                scrn = cpt.take_screenshot(url)
                bot.send_photo(photo=scrn,
                               chat_id=message.chat.id)
            except IllegalURL:
                bot.send_message(message.chat.id,
                                 text=BOT_ILLEGAL_URL)
        return

    if message.chat.id in (roads_chat, mods_chat):
        return

    c = db.cursor()
    c.execute('SELECT * FROM banned WHERE username = %s', (message.from_user.username,))

    if c.fetchone() is not None:
        return

    bot.send_message(message.chat.id,
                     BOT_MSG_ACCEPT.format(message.from_user.username))

    c = db.cursor()

    c.execute('''SELECT value FROM settings
                 WHERE option = 'roads_moderation' ''')

    if c.fetchone()[0] == 'disabled':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_CLOSED,
                              callback_data='road_closed'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_OPENED,
                              callback_data='road_opened'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_INFOPOINT,
                              callback_data='road_info_added'))
        keyboard.row(kbrd_btn(text=BTN_CANCEL,
                              callback_data='road_cancel'))

        bot.forward_message(roads_chat, message.chat.id, message.message_id)
        roads_message = bot.send_message(roads_chat,
                                         BOT_NEW_ROADBLOCK,
                                         reply_markup=keyboard)
        c.execute('''INSERT INTO roads VALUES (%s, %s, %s, %s, %s)''',
                  (message.from_user.username,
                   message.chat.id,
                   message.message_id,
                   0, roads_message.message_id))
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_ACCEPT,
                              callback_data='road_mod_approve'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_REQUEST_INFO,
                              callback_data='road_mod_request_info'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_FRAUD,
                              callback_data='road_mod_ban'))
        keyboard.row(kbrd_btn(text=BTN_CANCEL,
                              callback_data='road_mod_cancel'))

        msg = BOT_REQUEST_CHECK.format(message.from_user.username)
        mods_message = bot.send_message(mods_chat, msg, reply_markup=keyboard)
        bot.forward_message(mods_chat, message.chat.id, message.message_id)
        c.execute('''INSERT INTO roads VALUES (%s, %s, %s, %s, %s)''',
                  (message.from_user.username,
                   message.chat.id,
                   message.message_id,
                   mods_message.message_id, 0))
    db.commit()
    c.close()


@bot.callback_query_handler(func=Prefix('unban_'))
def unban_callback(call):
    user = call.data[len('unban_'):]
    c = db.cursor()
    c.execute('''DELETE FROM banned
                 WHERE username = %s''', (user,))
    bot.send_message(text=BOT_USER_UNBANNED.format(user),
                     chat_id=call.message.chat.id)


items_per_page = 3


@bot.callback_query_handler(func=Prefix('unbanpage_'))
def unban_pagination(call):
    items = int(call.data[len('unbanpage_'):])
    keyboard = types.InlineKeyboardMarkup()
    c = db.cursor()
    c.execute('''SELECT * FROM banned
                 LIMIT %s OFFSET %s''', (items_per_page, items))
    banned = c.fetchall()
    c.execute('''SELECT COUNT(*) FROM banned''')
    row_amt = c.fetchone()[0]
    for user in banned:
        keyboard.row(kbrd_btn(text=user[0],
                              callback_data='unban_' + user[0]))

    page_ctrl = []
    if items:
        page_ctrl.append(kbrd_btn(text=BTN_PREV_PAGE,
                                  callback_data='unbanpage_' +
                                                str(items - items_per_page)))
    if row_amt > items + items_per_page:
        page_ctrl.append(kbrd_btn(text=BTN_NEXT_PAGE,
                                  callback_data='unbanpage_' +
                                                str(items + items_per_page)))
    keyboard.row(*page_ctrl)
    keyboard.row(kbrd_btn(text=MENU_RETURN,
                          callback_data='prefs_return'))

    curr_page = items // items_per_page + 1
    all_pages = math.ceil(row_amt / items_per_page)
    bot.edit_message_text(BOT_CHOOSE_TO_UNBAN.format(curr_page, all_pages)
                          if row_amt else BOT_NO_BANNED,
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=keyboard)
    c.close()


@bot.callback_query_handler(func=Prefix('road_'))
def roads_callback(call):
    c = db.cursor()

    if call.data == 'road_mod_approve':
        if ('Выясняет' in call.message.text and
            full_name(call.from_user) not in call.message.text):
            bot.answer_callback_query(call.id, text=BOT_UNDER_INVESTIGATION)
            return
        msg = BOT_SENT_TO_STAFF.format(full_name(call.from_user),
                                       str(call.from_user.id))
        bot.edit_message_text(msg,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_CLOSED,
                              callback_data='road_closed'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_OPENED,
                              callback_data='road_opened'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_INFOPOINT,
                              callback_data='road_info_added'))
        keyboard.row(kbrd_btn(text=BTN_CANCEL,
                              callback_data='road_cancel'))

        c.execute('''SELECT chat_id FROM roads
                     WHERE mods_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE mods_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]
        bot.forward_message(roads_chat, chat_id, chat_message_id)
        roads_message = bot.send_message(roads_chat,
                                         BOT_NEW_ROADBLOCK,
                                         reply_markup=keyboard)

        c.execute('''UPDATE roads SET roads_message_id = %s
                     WHERE chat_message_id = %s''',
                  (roads_message.message_id, chat_message_id,))
    elif call.data == 'road_mod_request_info':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_ACCEPT,
                              callback_data='road_mod_approve'))
        keyboard.row(kbrd_btn(text=BTN_CANCEL,
                              callback_data='road_mod_cancel'))
        msg = BOT_INVESTIGATING.format(full_name(call.from_user),
                                       str(call.from_user.id))
        bot.edit_message_text(msg, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown',
                              reply_markup=keyboard)
    elif call.data == 'road_mod_ban':
        bot.edit_message_text(BOT_USER_BANNED.format(full_name(call.from_user),
                                                     str(call.from_user.id)),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')
        try:
            c.execute('''INSERT INTO banned VALUES
                         ((SELECT username FROM roads
                           WHERE mods_message_id = %s))''',
                      (call.message.message_id,))
        except psycopg2.IntegrityError:
            pass
    elif call.data == 'road_closed':
        if call.from_user.last_name not in staff:
            bot.answer_callback_query(call.id, text=BOT_NOT_ROAD_STAFF)
            return
        bot.edit_message_text(BOT_ROADBLOCK_SET.format(full_name(call.from_user),
                                                       str(call.from_user.id)),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')
        c.execute('''SELECT chat_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]
        bot.send_message(chat_id, BOT_ROADBLOCK_SET_USR,
                         reply_to_message_id=chat_message_id)
    elif call.data == 'road_opened':
        if call.from_user.last_name not in staff:
            bot.answer_callback_query(call.id, text=BOT_NOT_ROAD_STAFF)
            return
        bot.edit_message_text(BOT_ROADBLOCK_DEL.format(full_name(call.from_user),
                                                       str(call.from_user.id)),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')
        c.execute('''SELECT chat_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]
        bot.send_message(chat_id, BOT_ROADBLOCK_DEL_USR,
                         reply_to_message_id=chat_message_id)
    elif call.data == 'road_info_added':
        if call.from_user.last_name not in staff:
            bot.answer_callback_query(call.id, text=BOT_NOT_ROAD_STAFF)
            return
        bot.edit_message_text(BOT_INFOPOINT_SET.format(full_name(call.from_user),
                                                       str(call.from_user.id)),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')
        c.execute('''SELECT chat_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]
        bot.send_message(chat_id, BOT_INFOPOINT_SET_USR,
                         reply_to_message_id=chat_message_id)
    elif call.data == 'road_cancel':
        if call.from_user.last_name not in staff:
            bot.answer_callback_query(call.id, text=BOT_NOT_ROAD_STAFF)
            return
        bot.edit_message_text(BOT_REQUEST_CANCELLED.format(full_name(call.from_user),
                                                           str(call.from_user.id)),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')
        c.execute('''SELECT chat_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE roads_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]
        bot.send_message(chat_id, BOT_REQUEST_CANCELLED_USR,
                         reply_to_message_id=chat_message_id)
    elif call.data == 'road_mod_cancel':
        if ('Выясняет' in call.message.text and
            full_name(call.from_user) not in call.message.text):
            bot.answer_callback_query(call.id, text=BOT_UNDER_INVESTIGATION)
            return
        msg = BOT_REQUEST_CANCELLED.format(full_name(call.from_user),
                                           str(call.from_user.id))
        bot.edit_message_text(msg,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              parse_mode='markdown')

        c.execute('''SELECT chat_id FROM roads
                     WHERE mods_message_id = %s''',
                  (call.message.message_id,))
        chat_id = c.fetchone()[0]
        c.execute('''SELECT chat_message_id FROM roads
                     WHERE mods_message_id = %s''',
                  (call.message.message_id,))
        chat_message_id = c.fetchone()[0]

        bot.send_message(chat_id, BOT_REQUEST_CANCELLED_USR,
                         reply_to_message_id=chat_message_id)

    db.commit()
    c.close()


@bot.callback_query_handler(func=Prefix('prefs_'))
def prefs_callback(call):
    keyboard = types.InlineKeyboardMarkup()

    c = db.cursor()

    if call.data == 'prefs_mod_on':
        c.execute('''UPDATE settings SET value = 'enabled'
                     WHERE option = 'roads_moderation' ''')
        keyboard.row(kbrd_btn(text=PREF_MOD_OFF,
                              callback_data='prefs_mod_off'))
        keyboard.row(kbrd_btn(text=PREF_ADMINS,
                              callback_data='prefs_admins'))
        keyboard.row(kbrd_btn(text=MENU_RETURN,
                              callback_data='prefs_return'))
        bot.edit_message_text(PREF_DESC, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)
    elif call.data == 'prefs_mod_off':
        c.execute('''UPDATE settings SET value = 'disabled'
                     WHERE option = 'roads_moderation' ''')
        keyboard.row(kbrd_btn(text=PREF_MOD_ON,
                              callback_data='prefs_mod_on'))
        keyboard.row(kbrd_btn(text=PREF_ADMINS,
                              callback_data='prefs_admins'))
        keyboard.row(kbrd_btn(text=MENU_RETURN,
                              callback_data='prefs_return'))
        bot.edit_message_text(PREF_DESC, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)
    elif call.data == 'prefs_admins':
        keyboard.row(kbrd_btn(text=PREF_ADD_ADMIN,
                              callback_data='admin_add'))
        keyboard.row(kbrd_btn(text=PREF_DEL_ADMIN,
                              callback_data='admin_del'))
        keyboard.row(kbrd_btn(text=PREF_LIST_ADMINS,
                              callback_data='admin_list'))
        bot.send_message(text=BOT_ACTION_SELECT,
                         chat_id=call.message.chat.id,
                         reply_markup=keyboard)
    elif call.data == 'prefs_return':
        home(call.message, user_override=call.from_user.username)

    db.commit()
    c.close()


@bot.callback_query_handler(func=Prefix('admin_'))
def admin_callback(call):
    if call.data == 'admin_add':
        msg = bot.send_message(text=PREF_ADD_ADMIN_USR,
                               chat_id=call.message.chat.id)
        bot.register_next_step_handler(msg, add_admin)
    elif call.data == 'admin_del':
        msg = bot.send_message(text=PREF_DEL_ADMIN_USR,
                               chat_id=call.message.chat.id)
        bot.register_next_step_handler(msg, del_admin)
    elif call.data == 'admin_list':
        msg = PREF_CURR_ADMINS + ':\n'
        c = db.cursor()
        c.execute('''SELECT username FROM admins''')
        for idx, user in enumerate(c.fetchall(), 1):
            msg += '{}) @{}\n'.format(idx, user[0])
        bot.send_message(text=msg,
                         chat_id=call.message.chat.id)
        home(call.message, user_override=call.from_user.username)
        c.close()


if __name__ == '__main__':
    try:
        bot.polling()
    finally:
        db.close()
