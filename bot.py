import requests, telebot
from telebot import types
from bs4 import BeautifulSoup

bot = telebot.TeleBot('405295345:AAEiq-A3mEVsE203a0qOM3z2QCpPOlMKbZ0')

@bot.message_handler(commands=['start', 'home'])
def home(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row('📝 Клуб', '📖 Правила')
    keyboard.row('🔎 Поиск')
    bot.send_message(message.chat.id, 'Пожалуйста, выберите действие.', reply_markup=keyboard)
    
@bot.message_handler(regexp='📝 Клуб')
def club(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text='Перейти в Клуб', url='https://yandex.ru/blog/narod-karta')
    keyboard.add(url_button)
    bot.send_message(message.chat.id, 'Для перехода в Клуб нажмите кнопку ниже.', reply_markup=keyboard)
    
@bot.message_handler(regexp='📖 Правила')
def rules(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text='Открыть правила', url='https://yandex.ru/support/nmaps/rules_2.html')
    keyboard.add(url_button)
    bot.send_message(message.chat.id, 'Для открытия справки нажмите кнопку ниже.', reply_markup=keyboard)
    
@bot.message_handler(regexp='🔎 Поиск')
def search(message):
    if message.text == '🔎 Поиск':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row('🔎 Клуб', '🔎 Правила')
        bot.send_message(message.chat.id, 'Где будем искать?', reply_markup=keyboard)
        bot.register_next_step_handler(message, search)
    elif message.text == '🔎 Правила' or message.text == '🔎 Клуб':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row('Вернуться')
        bot.send_message(message.chat.id, 'Напишите фразу для поиска.', reply_markup=keyboard)
        if message.text == '🔎 Правила':
            bot.register_next_step_handler(message, search_rules)
        else:
            bot.register_next_step_handler(message, search_club)
    elif message.text == 'Вернуться':
        home(message)
        
def search_club(message):
    pass

def search_rules(message):
    page = requests.get('https://yandex.ru/support/search-results/?text=' + message.text.replace(' ', '+') + '&service=nmaps-guide')
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    results = []
    for item in soup.find_all('a', class_='serp__item'):
        results.append([item.find_all('div')[0].text, item.find_all('div')[1].text])
        answer += '*' + item.find_all('div')[0].text.split('—')[0] + '* : ' + item.find_all('div')[1].text + '\n'
    bot.send_message(message.chat.id, answer, parse_mode='markdown') 
        
if __name__ == '__main__':
    bot.polling()