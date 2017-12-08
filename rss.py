from telegram.error import TelegramError
from db import db
from calendar import timegm
from config import nmaps_chat, mods_chat
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
    feed = feedparser.parse('https://yandex.ru/blog/narod-karta/rss')

    c = db.cursor()
    c.execute('''SELECT * FROM rss''')
    last_published = int(c.fetchone()[0])
    log.info('Last published post timestamp is {}'.format(last_published))
    new_latest_date = last_published

    new_entries = []
    for entry in feed.entries:
        if timegm(entry.published_parsed) > last_published:
            if timegm(entry.published_parsed) > new_latest_date:
                new_latest_date = timegm(entry.published_parsed)
            log.info('New entry: {}'.format(entry.link))
            new_entries.append(entry.link)
        else:
            break

    c.execute('''DELETE FROM rss''')
    c.execute('''INSERT INTO rss VALUES(%s)''', (new_latest_date,))
    db.commit()
    log.info('Wrote latest timestamp to database: {}'.format(new_latest_date))

    if new_entries:
        c.execute('SELECT id FROM subscribers')
        subscribers = []
        for id in c.fetchall():
            subscribers.append(id[0])
        log.info('Fetched subscribers')

        log.info('Sending new posts')
        for entry in list(reversed(new_entries)):
            log.info('Sending post: {}'.format(entry))
            bot.send_message(nmaps_chat, entry)
            bot.send_message(mods_chat, entry)
            for subscriber in subscribers:
                try:
                    bot.send_message(subscriber, entry)
                except TelegramError:
                    pass

    else:
        log.info('No new posts')

    c.close()