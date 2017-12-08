from db import db
from phrases import BOT_SUBSCRIBED_USR, BOT_UNSUBSCRIBED_USR
from helpers import get_keyboard


def subscribe(bot, update):
    c = db.cursor()
    c.execute('INSERT INTO subscribers VALUES (%s)', (update.message.from_user.id,))
    db.commit()
    c.close()
    update.message.reply_text(BOT_SUBSCRIBED_USR,
                              reply_markup=get_keyboard(update, True))


def unsubscribe(bot, update):
    c = db.cursor()
    c.execute('DELETE FROM subscribers WHERE id=(%s)', (update.message.from_user.id,))
    db.commit()
    c.close()
    update.message.reply_text(BOT_UNSUBSCRIBED_USR,
                              reply_markup=get_keyboard(update, False))


def subscribed(id):
    c = db.cursor()
    c.execute('SELECT * FROM subscribers WHERE id=(%s)', (id,))
    if c.fetchone() is not None:
        return True
    return False
