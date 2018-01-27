from telegram.ext import Updater, MessageHandler, RegexHandler, Filters, \
    InlineQueryHandler, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup
from telegram.error import TimedOut
from config import admins, alexfox, road_hashtag, \
    screen_hashtags, telegram_key, rules_search_url, FEEDBACK_REQUESTED, \
    SEARCH_QUERY_REQUESTED
from phrases import BOT_UNRECOGNIZED_MESSAGE, BOT_FEEDBACK_SENT_USR, \
    MENU_RETURN, MENU_SEARCH_RULES, MENU_SEARCH_CLUB, MENU_ROADS, MENU_LINKS, \
    MENU_SUBSCRIBE, BOT_ACTION_SELECT, BOT_YM_SCREENS_BANNED, \
    BOT_ILLEGAL_URL, BOT_CHS_LINK, BOT_SEND_FEEDBACK_USR, BOT_NOT_FOUND, \
    BOT_SRCH_CONTINUE, BOT_SRCH_QUERY, BOT_UNEXPECTED_ERROR, \
    BOT_PRIVATE_ROAD_REPORT_USR, BOT_CANCELLED, MENU_UNSUBSCRIBE, \
    MENU_FEEDBACK, BOT_INLINE_INSTRUCTIONS
from capturer import Capturer, IllegalURL, YMTempUnsupported
from bs4 import BeautifulSoup
from functools import wraps
from roads import new_roadblock, roadblock_callback, roadblock_filter
from rss import rss
from subscription import update_subscription, subscribed
from inline import inline_search
from helpers import get_keyboard
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests


# Enable logging
logging.basicConfig(format='[%(asctime)s] [%(levelname)s] [bot]\n%(message)s',
                    datefmt='%d-%m %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

cpt = Capturer()


def private(f):
    @wraps(f)
    def wrapped_private(bot, update, *args, **kwargs):
        if Filters.private.filter(update.message):
            return f(bot, update, *args, **kwargs)
    return wrapped_private


def admins_only(f):
    @wraps(f)
    def wrapped_admins(bot, update, *args, **kwargs):
        if update.message.from_user.id in admins:
            return f(bot, update, *args, **kwargs)
    return wrapped_admins


@private
def send_instructions(bot, update, start=False):
    instructions = {MENU_ROADS: BOT_PRIVATE_ROAD_REPORT_USR,
                    '/start inline-help': BOT_INLINE_INSTRUCTIONS,
                    '/start': BOT_ACTION_SELECT}
    if update.message.text in instructions:
        text = instructions[update.message.text]
    elif start:
        text = BOT_ACTION_SELECT
    else:
        text = BOT_UNRECOGNIZED_MESSAGE
    update.message.reply_text(
        text,
        reply_markup=get_keyboard(update,
                                  subscribed(update.message.from_user.id)))


@private
def bookmarks(bot, update):
    keyboard = [
        [
            InlineKeyboardButton(
                'Правила',
                url='https://yandex.ru/support/nmaps/rules_2.html'),
            InlineKeyboardButton(
                'Клуб',
                url='https://yandex.ru/blog/narod-karta')
        ],
        [
            InlineKeyboardButton('ПКК', url='https://pkk5.rosreestr.ru/'),
            InlineKeyboardButton('ФИАС', url='https://fias.nalog.ru/')
        ],
        [
            InlineKeyboardButton('ЕГРП365', url='https://egrp365.ru/map/'),
            InlineKeyboardButton('TerraServer',
                                 url='https://www.terraserver.com/')
        ],
        [InlineKeyboardButton('Реформа ЖКХ', url='https://www.reformagkh.ru/')]
    ]
    update.message.reply_text(BOT_CHS_LINK,
                              reply_markup=InlineKeyboardMarkup(keyboard))
    send_instructions(bot, update, True)


def screenshot(bot, update):
    for entity in update.message['entities']:
        if entity['type'] == 'url':
            url_start = int(entity['offset'])
            url_end = url_start + int(entity['length'])
            try:
                scrn = cpt.take_screenshot(
                    update.message.text[url_start:url_end]
                )
                scrn_url = cloudinary.uploader.upload(scrn)['secure_url']
                bot.send_photo(update.message.chat.id, scrn_url)
                cpt.reboot()
            except IllegalURL:
                update.message.reply_text(BOT_ILLEGAL_URL)
            except YMTempUnsupported:
                update.message.reply_text(BOT_YM_SCREENS_BANNED)


@private
def request_feedback(bot, update):
    update.message.reply_text(
        BOT_SEND_FEEDBACK_USR,
        reply_markup=ReplyKeyboardMarkup([[MENU_RETURN]],
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return FEEDBACK_REQUESTED


def receive_feedback(bot, update):
    update.message.reply_text(
        BOT_FEEDBACK_SENT_USR,
        reply_markup=get_keyboard(update,
                                  subscribed(update.message.from_user.id)))
    bot.send_message(alexfox, update.message.text)
    return ConversationHandler.END


@private
def search(bot, update, user_data):
    if update.message.text == MENU_SEARCH_RULES:
        user_data['search'] = 'rules'
    else:
        user_data['search'] = 'club'
    update.message.reply_text(
        BOT_SRCH_QUERY,
        reply_markup=ReplyKeyboardMarkup([[MENU_RETURN]],
                                         resize_keyboard=True,
                                         one_time_keyboard=True))
    return SEARCH_QUERY_REQUESTED


def run_search(bot, update, user_data):
    if 'search' not in user_data:
        update.message.reply_text(BOT_UNEXPECTED_ERROR)
        send_instructions(bot, update, True)
        return ConversationHandler.END
    if user_data['search'] == 'rules':
        search_rules(bot, update)
    elif user_data['search'] == 'club':
        search_club(bot, update)

    return SEARCH_QUERY_REQUESTED


def search_rules(bot, update):
    page = requests.get(rules_search_url +
                        update.message.text.replace(' ', '+'))
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
        update.message.reply_text(BOT_NOT_FOUND)
    else:
        update.message.reply_text(answer,
                                  parse_mode='markdown',
                                  disable_web_page_preview=True)
    update.message.reply_text(
        BOT_SRCH_CONTINUE,
        reply_markup=ReplyKeyboardMarkup([[MENU_RETURN]],
                                         resize_keyboard=True,
                                         one_time_keyboard=True))


def search_club(bot, update):
    page = requests.get('https://yandex.ru/blog/narod-karta/search?text=' +
                        update.message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='b-serp-item'):
        title = item.find('h2').text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + ')\n'
        answer += '____________________\n'
    if not answer:
        update.message.reply_text(BOT_NOT_FOUND)
    else:
        update.message.reply_text(answer,
                                  parse_mode='markdown',
                                  disable_web_page_preview=True)
    update.message.reply_text(
        BOT_SRCH_CONTINUE,
        reply_markup=ReplyKeyboardMarkup([[MENU_RETURN]],
                                         resize_keyboard=True,
                                         one_time_keyboard=True))


@private
def cancel(bot, update, user_data):
    update.message.reply_text(
        BOT_CANCELLED,
        reply_markup=get_keyboard(update,
                                  subscribed(update.message.from_user.id)))
    user_data.clear()
    return ConversationHandler.END


def error(bot, update, error):
    if error == TimedOut:
        return
    logger.error(error)


def main():
    """Start the bot"""
    updater = Updater(telegram_key)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    j = updater.job_queue

    dp.add_handler(RegexHandler(r'(/start[a-z-]*|{})'.format(MENU_ROADS),
                                send_instructions))
    dp.add_handler(RegexHandler(MENU_LINKS, bookmarks))
    dp.add_handler(RegexHandler(screen_hashtags, screenshot))
    dp.add_handler(RegexHandler(road_hashtag, new_roadblock))
    dp.add_handler(MessageHandler(Filters.photo & roadblock_filter,
                                  new_roadblock))
    dp.add_handler(RegexHandler(r'({}|{})'.format(MENU_SUBSCRIBE,
                                                  MENU_UNSUBSCRIBE),
                                update_subscription))

    # Conversations
    dp.add_handler(ConversationHandler(
        entry_points=[RegexHandler(MENU_FEEDBACK, request_feedback)],
        states={
            FEEDBACK_REQUESTED: [RegexHandler(r'^(?!⬅ Вернуться)',
                                              receive_feedback)]
        },
        fallbacks=[RegexHandler(MENU_RETURN,
                                cancel,
                                pass_user_data=True)]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[RegexHandler(MENU_SEARCH_CLUB,
                                   search,
                                   pass_user_data=True),
                      RegexHandler(MENU_SEARCH_RULES,
                                   search,
                                   pass_user_data=True)],
        states={
            SEARCH_QUERY_REQUESTED: [RegexHandler(r'^(?!⬅ Вернуться)',
                                                  run_search,
                                                  pass_user_data=True)]
        },
        fallbacks=[RegexHandler(MENU_RETURN,
                                cancel,
                                pass_user_data=True)]
    ))

    # Callbacks
    dp.add_handler(CallbackQueryHandler(roadblock_callback,
                                        pattern=r'^road\w+'))

    # This one will handle any random message
    dp.add_handler(MessageHandler(Filters.all, send_instructions))

    # Logging errors
    dp.add_error_handler(error)

    # Adds repeating jobs
    j.run_repeating(rss, 300)

    # Inline handler
    dp.add_handler(InlineQueryHandler(inline_search))

    # Actually start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
