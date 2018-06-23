from phrases import BOT_SUBSCRIBED_USR, BOT_UNSUBSCRIBED_USR
from helpers import get_keyboard
from telegram import Bot, Update

from pony.orm import db_session
from db import Subscriber


@db_session
def update_subscription(_bot: Bot, update: Update) -> None:
    user_id = update.effective_user.id

    if not subscribed(user_id):
        Subscriber(user_id=user_id)
        update.message.reply_text(BOT_SUBSCRIBED_USR,
                                  reply_markup=get_keyboard(update, True))
    else:
        Subscriber.get(user_id=user_id).delete()
        update.message.reply_text(BOT_UNSUBSCRIBED_USR,
                                  reply_markup=get_keyboard(update, False))


@db_session
def subscribed(id: int) -> bool:
    return Subscriber.exists(user_id=id)
