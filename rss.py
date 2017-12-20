from telegram.error import TelegramError
from itertools import chain
from db import db
from calendar import timegm
from config import nmaps_chat, mods_chat, instantview_url
import feedparser
import logging


log_level = logging.INFO

log = logging.Logger('RSS')
log.setLevel(log_level)

log_handler = logging.StreamHandler()
log_handler.setLevel(log_level)

log_fmt = logging.Formatter('[{asctime}] [{levelname}] [RSS]\n{message}\n',
                            datefmt='%d-%m %H:%M:%S',
                            style='{')
log_handler.setFormatter(log_fmt)

log.addHandler(log_handler)


def rss(bot, job):
    log.info('Starting RSS poster')
    new_entries, new_latest_date = get_new_entries()

    c = db.cursor()
    c.execute('DELETE FROM rss')
    c.execute('INSERT INTO rss VALUES (%s)', (new_latest_date,))
    db.commit()
    log.info('Wrote latest timestamp to database: {}'.format(new_latest_date))

    if new_entries:
        subscribers = get_subscribers()
        log.info('Fetched subscribers')
        log.info('Sending new posts')
        for entry in list(reversed(new_entries)):
            send_post(bot, entry, subscribers)
        log.info('Done sending posts!')
    else:
        log.info('No new posts')
    c.close()


def get_new_entries():
    feed = feedparser.parse('https://yandex.ru/blog/narod-karta/rss')
    entries = feed.entries

    c = db.cursor()
    c.execute('SELECT * FROM rss')
    last_published = int(c.fetchone()[0])
    log.info('Last published post timestamp is {}'.format(last_published))
    new_latest_date = last_published

    new_entries = []
    i = 0
    while timegm(entries[i].published_parsed) > last_published:
        if timegm(entries[i].published_parsed) > new_latest_date:
            new_latest_date = timegm(entries[i].published_parsed)
        log.info('New entry: {}'.format(entries[i].link))
        new_entries.append(entries[i].link)
        i += 1

    return new_entries, new_latest_date


def send_post(bot, url, subscribers):
    log.info('Sending post: {}'.format(url))
    message_text = '[{}]({})'.format(url, instantview_url.format(url))
    for subscriber in chain((nmaps_chat, mods_chat), subscribers):
        try:
            bot.send_message(subscriber, message_text, parse_mode='markdown')
        except TelegramError:
            pass


def get_subscribers():
    c = db.cursor()
    c.execute('SELECT id FROM subscribers')
    subscribers = []
    for id in c.fetchall():
        subscribers.append(id[0])
    c.close()
    return subscribers
