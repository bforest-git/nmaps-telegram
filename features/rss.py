from telegram.error import TelegramError
from telegram import Bot
from itertools import chain
from calendar import timegm
from config import nmaps_chat, mods_chat, instantview_url
from phrases import BOT_NEW_RSS
import feedparser
import logging

from pony.orm import db_session
from db import Rss, Subscriber


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


def rss(bot: Bot, _job) -> None:
    log.info('Starting RSS poster')
    new_entries, new_latest_date = get_new_entries()

    with db_session:
        Rss.select().delete()
        Rss(last_published=new_latest_date)

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


def get_new_entries() -> tuple:
    feed = feedparser.parse('https://yandex.ru/blog/narod-karta/rss')
    entries = feed.entries

    with db_session:
        last_published = int(Rss.get().last_published)

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


def send_post(bot: Bot, url: str, subscribers: list) -> None:
    log.info('Sending post: {}'.format(url))
    message_text = BOT_NEW_RSS.format(instantview_url.format(url), url)
    for subscriber in chain((nmaps_chat, mods_chat), subscribers):
        try:
            bot.send_message(subscriber, message_text, parse_mode='markdown')
        except TelegramError:
            pass


@db_session
def get_subscribers() -> list:
    return [s.user_id for s in Subscriber.select(lambda s: s.user_id)]
