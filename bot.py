import logging, os, requests, psycopg2, telebot
from telebot import types
from phrases import *
from bs4 import BeautifulSoup


class Prefix:
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, call):
        return call.data.startswith(self.prefix)


bot = telebot.TeleBot(os.getenv('TLGAPIKEY', '331488080:AAH8PEA9WnsZtFubYnwFI5EWDq1fvqb9ZAE'))
bot.bypass_moderators = False
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
db_creds = {'host': 'localhost',
            'dbname': os.getenv('DBNAME', 'bot'),
            'user': os.getenv('DBUSER', 'ubuntu'),
            'password': os.getenv('DBPASS', 'bot')}

nmaps_chat = os.getenv('NMAPSCHAT', '-1001136617457')
mods_chat = os.getenv('MODSCHAT', '-240980847')
roads_chat = os.getenv('ROADSCHAT', '-227479062')

alexfox = '30375360'

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

db.commit()
c.close()
db.close()


def private_chat(message):
    return message.chat.type == 'private'


def is_admin(user):
    db = psycopg2.connect(**db_creds)
    c = db.cursor()
    c.execute('''SELECT username FROM admins
                 WHERE username = %s''', (user,))
    is_adm = c.fetchone() is not None
    db.close()
    return is_adm


@bot.message_handler(commands=['start', 'home'])
def home(message, user_override=None):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.row(MENU_LINKS)
    keyboard.row(MENU_SEARCH_CLUB, MENU_SEARCH_RULES)
    keyboard.row(MENU_ROADS, MENU_FEEDBACK)
    if is_admin(user_override or message.from_user.username):
        keyboard.row(MENU_FAQ, MENU_SUPPORT)
        keyboard.row(MENU_SETTINGS)
    bot.send_message(message.chat.id,
                     BOT_ACTION_SELECT,
                     reply_markup=keyboard)


@bot.message_handler(regexp=MENU_SETTINGS)
def settings(message):
    keyboard = types.InlineKeyboardMarkup()
    if bot.bypass_moderators:
        keyboard.row(kbrd_btn(text=PREF_MOD_ON,
                              callback_data='prefs_mod_on'))
    else:
        keyboard.row(kbrd_btn(text=PREF_MOD_OFF,
                              callback_data='prefs_mod_off'))
    keyboard.row(kbrd_btn(text=PREF_ADMINS,
                          callback_data='prefs_admins'))
    keyboard.row(kbrd_btn(text=MENU_RETURN,
                          callback_data='prefs_return'))

    bot.send_message(message.chat.id,
                     PREF_DESC,
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


def add_admin(message):
    db = psycopg2.connect(**db_creds)
    c = db.cursor()
    try:
        c.execute('INSERT INTO admins VALUES (%s)', (message.text.strip('@'), ))
    except psycopg2.IntegrityError:
        bot.send_message(message.chat.id, PREF_ALREADY_ADMIN_USR)
        home(message)
        return
    db.commit()
    c.close()
    db.close()
    bot.send_message(message.chat.id, PREF_ADDED_ADMIN_USR)
    home(message, user_override=message.from_user.username)


def del_admin(message):
    db = psycopg2.connect(**db_creds)
    c = db.cursor()
    c.execute('DELETE FROM admins WHERE username = %s', (message.text.strip('@'), ))
    db.commit()
    c.close()
    db.close()
    bot.send_message(message.chat.id, PREF_DELED_ADMIN_USR)
    home(message, user_override=message.from_user.username)


@bot.message_handler(content_types=['text'])
def roads(message):
    if message.from_user.username == 'combot':
        bot.delete_message(message.chat.id, message.id)
    if '#перекрытие' not in message.text.lower() or str(message.chat.id) == roads_chat or str(message.chat.id) == mods_chat:
        return

    bot.send_message(message.chat.id,
                     BOT_MSG_ACCEPT.format(message.from_user.username))

    db = psycopg2.connect(**db_creds)
    c = db.cursor()

    if bot.bypass_moderators:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_CLOSED,
                              callback_data='road_closed'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_OPENED,
                              callback_data='road_opened'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_INFOPOINT,
                              callback_data='road_info_added'))

        bot.forward_message(roads_chat, message.chat.id, message.message_id)
        roads_message = bot.send_message(roads_chat,
                                         BOT_NEW_ROADBLOCK,
                                         reply_markup=keyboard)
        c.execute('''INSERT INTO roads VALUES (%s, %s, %s, %s, %s)''',
                  (message.from_user.username, message.chat.id, message.message_id,
                   0, roads_message.message_id))
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_ACCEPT,
                              callback_data='road_mod_approve'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_REQUEST_INFO,
                              callback_data='road_mod_request_info'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_FRAUD,
                              callback_data='road_mod_ban'))

        msg = BOT_REQUEST_CHECK.format(message.from_user.username)
        mods_message = bot.send_message(mods_chat, msg, reply_markup=keyboard)
        bot.forward_message(mods_chat, message.chat.id, message.message_id)
        c.execute('''INSERT INTO roads VALUES (%s, %s, %s, %s, %s)''',
                  (message.from_user.username, message.chat.id, message.message_id,
                   mods_message.message_id, 0))
    db.commit()
    db.close()


@bot.callback_query_handler(func=Prefix('road_'))
def roads_callback(call):
    db = psycopg2.connect(**db_creds)
    c = db.cursor()

    if call.data == 'road_mod_approve':
        if 'Выясняет' in call.message.text and call.from_user.username not in call.message.text:
            bot.answer_callback_query(call.id, text=BOT_UNDER_INVESTIGATION)
            return
        bot.edit_message_text(BOT_SENT_TO_STAFF.format(call.from_user.username),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(kbrd_btn(text=BTN_ROADS_CLOSED,
                              callback_data='road_closed'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_OPENED,
                              callback_data='road_opened'))
        keyboard.row(kbrd_btn(text=BTN_ROADS_INFOPOINT,
                              callback_data='road_info_added'))

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
        msg = BOT_INVESTIGATING.format(call.from_user.username)
        bot.edit_message_text(msg, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)
    elif call.data == 'road_mod_ban':
        bot.edit_message_text(BOT_USER_BANNED.format(call.from_user.username),
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        c.execute('''INSERT INTO banned VALUES
                     (SELECT username FROM roads
                      WHERE mods_message_id = %s)''',
                  (call.message.message_id,))
    elif call.data == 'road_closed':
        bot.edit_message_text(BOT_ROADBLOCK_SET, chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
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
        bot.edit_message_text(BOT_ROADBLOCK_DEL, chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
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
        bot.edit_message_text(BOT_INFOPOINT_SET, chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
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

    db.commit()
    db.close()


@bot.callback_query_handler(func=Prefix('prefs_'))
def prefs_callback(call):
    keyboard = types.InlineKeyboardMarkup()

    if call.data == 'prefs_mod_on':
        bot.bypass_moderators = False
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
        bot.bypass_moderators = True
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
        db = psycopg2.connect(**db_creds)
        c = db.cursor()
        c.execute('''SELECT username FROM admins''')
        for idx, user in enumerate(c.fetchall(), 1):
            msg += '{}) @{}\n'.format(idx, user[0])
        bot.send_message(text=msg,
                         chat_id=call.message.chat.id)
        home(call.message, user_override=call.from_user.username)


if __name__ == '__main__':
    bot.polling()
