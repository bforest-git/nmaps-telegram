from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import BaseFilter
from config import mods_chat, roads_chat, roads_staff, road_hashtag
from phrases import BTN_ROADS_CLOSED, BTN_ROADS_OPENED, BTN_ROADS_INFOPOINT, \
    BTN_CANCEL, BTN_ROADS_ACCEPT, BTN_ROADS_FRAUD, BTN_ROADS_REQUEST_INFO, \
    BOT_MSG_ACCEPT, BOT_REQUEST_CHECK, BOT_NOT_ROAD_STAFF, \
    BOT_REQUEST_CANCELLED_USR, BOT_REQUEST_CANCELLED, BOT_USER_BANNED, \
    BOT_SENT_TO_STAFF, BOT_ROADBLOCK_DEL_USR, BOT_ROADBLOCK_SET_USR, \
    BOT_INFOPOINT_SET_USR, BOT_INVESTIGATING, BOT_ROADBLOCK_DEL, \
    BOT_ROADBLOCK_SET, BOT_INFOPOINT_SET, BOT_NEW_ROADBLOCK
from db import db


class RoadblockHashtagHandler(BaseFilter):
    def filter(self, message):
        return road_hashtag.match(message.caption)


roadblock_filter = RoadblockHashtagHandler()


def build_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=callback)]
         for label, callback in buttons]
    )


staff_buttons = (
    (BTN_ROADS_CLOSED, 'road_closed'),
    (BTN_ROADS_OPENED, 'road_opened'),
    (BTN_ROADS_INFOPOINT, 'road_info_added'),
    (BTN_CANCEL, 'road_cancel')
)

mods_buttons = (
    (BTN_ROADS_ACCEPT, 'road_mod_approve'),
    (BTN_CANCEL, 'road_cancel'),
    (BTN_ROADS_REQUEST_INFO, 'road_mod_request_info'),
    (BTN_ROADS_FRAUD, 'road_mod_ban')
)

investigation_buttons = (
    (BTN_ROADS_ACCEPT, 'road_mod_approve'),
    (BTN_CANCEL, 'road_cancel')
)

staff_keyboard, mods_keyboard, investigation_keyboard = \
    map(build_keyboard, [staff_buttons, mods_buttons, investigation_buttons])


def new_roadblock(bot, update):
    if banned(update.message.from_user):
        return
    if update.message.chat.id == roads_chat:
        return

    user = bot.get_chat_member(mods_chat, update.message.from_user.id)
    if user['status'] in ['creator', 'administrator', 'member']:
        bypass_moderators(bot, update)
        return
    update.message.reply_text(BOT_MSG_ACCEPT.format(
        user_name(update.message.from_user)))
    msg = BOT_REQUEST_CHECK.format(user_name(update.message.from_user))
    mods_message = bot.send_message(mods_chat,
                                    msg,
                                    reply_markup=mods_keyboard)
    update.message.forward(mods_chat)

    c = db.cursor()
    c.execute('INSERT INTO roads VALUES (%s, %s, %s, %s, %s)',
              (update.message.from_user.id, update.message.chat.id,
               update.message.message_id, mods_message.message_id, 0))
    db.commit()
    c.close()


def cancel_roadblock(bot, query):
    if query.message.chat.id == mods_chat:
        nmaps_message = retrieve_roadblock(mods_id=query.message.message_id)
    else:
        if query.from_user.last_name not in roads_staff:
            query.answer(BOT_NOT_ROAD_STAFF)
            return
        nmaps_message = retrieve_roadblock(roads_id=query.message.message_id)
    bot.send_message(nmaps_message['chat_id'],
                     BOT_REQUEST_CANCELLED_USR,
                     reply_to_message_id=nmaps_message['chat_message_id'])
    query.edit_message_text(BOT_REQUEST_CANCELLED.format(
        user_name(query.from_user),
        query.from_user.id),
                            parse_mode='markdown')


def ban_roadblock_author(bot, query):
    if query.message.chat.id == mods_chat:
        nmaps_message = retrieve_roadblock(mods_id=query.message.message_id)
    else:
        nmaps_message = retrieve_roadblock(roads_id=query.message.message_id)
    query.edit_message_text(BOT_USER_BANNED.format(
        user_name(query.from_user),
        query.from_user.id),
                            parse_mode='markdown')
    c = db.cursor()
    c.execute('INSERT INTO banned VALUES (%s)', (nmaps_message['user_id'],))
    db.commit()
    c.close()


def request_roadblock_info(bot, query):
    query.edit_message_text(BOT_INVESTIGATING.format(
        user_name(query.from_user),
        query.from_user.id),
                            reply_markup=investigation_keyboard,
                            parse_mode='markdown')


def accept_roadblock(bot, query):
    query.edit_message_text(BOT_SENT_TO_STAFF.format(
        user_name(query.from_user),
        query.from_user.id),
                            parse_mode='markdown')
    nmaps_message = retrieve_roadblock(mods_id=query.message.message_id)
    bot.forward_message(roads_chat,
                        nmaps_message['chat_id'],
                        nmaps_message['chat_message_id'])
    roads_message = bot.send_message(roads_chat, BOT_NEW_ROADBLOCK,
                                     reply_markup=staff_keyboard)

    nmaps_message = retrieve_roadblock(mods_id=query.message.message_id)
    c = db.cursor()
    c.execute('UPDATE roads SET roads_message_id=%s WHERE chat_message_id=%s',
              (roads_message.message_id, nmaps_message['chat_message_id']))
    db.commit()
    c.close()


def bypass_moderators(bot, update):
    update.message.reply_text(BOT_MSG_ACCEPT.format(
        user_name(update.message.from_user), update.message.from_user.id))
    bot.forward_message(roads_chat, update.message.chat.id,
                        update.message.message_id)
    roads_message = bot.send_message(roads_chat, BOT_NEW_ROADBLOCK,
                                     reply_markup=staff_keyboard)

    c = db.cursor()
    c.execute('INSERT INTO roads VALUES (%s, %s, %s, %s, %s)',
              (update.message.from_user.id, update.message.chat.id,
               update.message.message_id, 0, roads_message.message_id))
    db.commit()
    c.close()


def send_roadblock_resolution(bot, query):
    if query.from_user.last_name not in roads_staff:
        query.answer(BOT_NOT_ROAD_STAFF)
        return
    nmaps_message = retrieve_roadblock(roads_id=query.message.message_id)
    if query.data == 'road_closed':
        msg = BOT_ROADBLOCK_SET_USR
        btn_msg = BOT_ROADBLOCK_SET
    elif query.data == 'road_opened':
        msg = BOT_ROADBLOCK_DEL_USR
        btn_msg = BOT_ROADBLOCK_DEL
    else:
        msg = BOT_INFOPOINT_SET_USR
        btn_msg = BOT_INFOPOINT_SET

    bot.send_message(nmaps_message['chat_id'], msg,
                     reply_to_message_id=nmaps_message['chat_message_id'])
    query.edit_message_text(btn_msg.format(user_name(query.from_user),
                                           query.from_user.id),
                            parse_mode='markdown')


def retrieve_roadblock(**kwargs):
    c = db.cursor()

    if 'mods_id' in kwargs:
        c.execute('SELECT * FROM roads WHERE mods_message_id=%s',
                  (kwargs['mods_id'],))
    else:
        c.execute('SELECT * FROM roads WHERE roads_message_id=%s',
                  (kwargs['roads_id'],))

    roadblock = dict(zip(['user_id', 'chat_id', 'chat_message_id',
                          'mods_message_id', 'roads_message_id'],
                         c.fetchone()))
    c.close()
    return roadblock


def roadblock_callback(bot, update):
    query = update.callback_query
    if query.data == 'road_mod_approve':
        accept_roadblock(bot, update.callback_query)
    elif query.data == 'road_cancel':
        cancel_roadblock(bot, update.callback_query)
    elif query.data == 'road_mod_request_info':
        request_roadblock_info(bot, query)
    elif query.data == 'road_mod_ban':
        ban_roadblock_author(bot, update.callback_query)
    else:
        send_roadblock_resolution(bot, update.callback_query)


def user_name(user):
    if user.username is not None:
        return '@' + user.username
    else:
        return user.first_name


def banned(user):
    c = db.cursor()
    c.execute('SELECT * FROM banned WHERE id=%s', (user.id,))
    return c.fetchone() is not None
