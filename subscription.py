from db import db
from phrases import BOT_SUBSCRIBED_USR, BOT_UNSUBSCRIBED_USR
from helpers import get_keyboard


def update_subscription(bot, update):
    c = db.cursor()
    if not subscribed(update.message.from_user.id):
        c.execute('INSERT INTO subscribers VALUES (%s)',
                  (update.message.from_user.id,))
        update.message.reply_text(BOT_SUBSCRIBED_USR,
                                  reply_markup=get_keyboard(update, True))
    else:
        c.execute('DELETE FROM subscribers WHERE id=%s',
                  (update.message.from_user.id,))
        update.message.reply_text(BOT_UNSUBSCRIBED_USR,
                                  reply_markup=get_keyboard(update, False))
    db.commit()
    c.close()


def subscribed(id):
    c = db.cursor()
    c.execute('SELECT * FROM subscribers WHERE id=%s', (id,))
    if c.fetchone() is not None:
        return True
    return False
