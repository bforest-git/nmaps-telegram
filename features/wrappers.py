from functools import wraps

from telegram.ext import Filters

from config import admins


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
