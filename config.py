import os
import re
from telegram import ReplyKeyboardMarkup
from phrases import *

telegram_key = os.getenv('TELEGRAM_API_KEY', '331488080:AAH8PEA9WnsZtFubYnwFI5EWDq1fvqb9ZAE')

screen_hashtags = re.compile('.*#({}|{}.*)'.format(HASH_SCREEN, HASH_SCREEN_ENG), flags=re.I | re.U)
road_hashtag = re.compile('.*#({}.*)'.format(HASH_ROADBLOCK), flags=re.I | re.U)

FEEDBACK_REQUESTED, SEARCH_QUERY_REQUESTED = 1, 1

main_menu = ReplyKeyboardMarkup([[MENU_LINKS], [MENU_SEARCH_CLUB, MENU_SEARCH_RULES], [MENU_ROADS, MENU_FEEDBACK]],
                                one_time_keyboard=True,
                                resize_keyboard=True)

nmaps_chat = int(os.getenv('NMAPSCHAT', '-1001136617457'))
mods_chat = int(os.getenv('MODSCHAT', '-240980847'))
roads_chat = int(os.getenv('ROADSCHAT', '-259382209'))

alexfox = 30375360
admins = list(map(int, os.getenv('ADMINS', str(alexfox)).split(',')))
roads_staff = os.getenv('ROADS_STAFF', 'Bagirov').split(',')