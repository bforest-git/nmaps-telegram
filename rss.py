from db import db
from calendar import timegm
from config import nmaps_chat, mods_chat
import feedparser


def rss(bot, job):
    feed = feedparser.parse('https://yandex.ru/blog/narod-karta/rss')

    c = db.cursor()
    c.execute('''SELECT * FROM rss''')
    last_published = int(c.fetchone()[0])
    new_latest_date = last_published

    new_entries = []
    for entry in feed.entries:
        if timegm(entry.published_parsed) > last_published:
            if timegm(entry.published_parsed) > new_latest_date:
                new_latest_date = timegm(entry.published_parsed)
            new_entries.append(entry.link)
        else:
            break

    c.execute('''DELETE FROM rss''')
    c.execute('''INSERT INTO rss VALUES(%s)''', (new_latest_date,))
    db.commit()
    c.close()

    if new_entries:
        for entry in list(reversed(new_entries)):
            bot.send_message(nmaps_chat, entry)
            bot.send_message(mods_chat, entry)
