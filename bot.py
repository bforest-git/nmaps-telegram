import requests, telebot
from telebot import types
from bs4 import BeautifulSoup

bot = telebot.TeleBot('405295345:AAEiq-A3mEVsE203a0qOM3z2QCpPOlMKbZ0')
test1 = '-235537432'
test2 = '-236614825'
test_message = '605'

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
    home(message)
    
@bot.message_handler(regexp='📖 Правила')
def rules(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text='Открыть правила', url='https://yandex.ru/support/nmaps/rules_2.html')
    keyboard.add(url_button)
    bot.send_message(message.chat.id, 'Для открытия справки нажмите кнопку ниже.', reply_markup=keyboard)
    home(message)
    
@bot.message_handler(regexp='🔎 Поиск')
def search(message):
    if message.text == '🔎 Поиск':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row('🔎 Клуб', '🔎 Правила')
        keyboard.row('Вернуться')
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
    if message.text == 'Вернуться':
        home(message)
    page = requests.get('https://yandex.ru/blog/narod-karta/search?text=' + message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='b-serp-item'):
        pass
        title = item.find('h2').text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + ')\n'
        answer += '____________________\n'
    bot.send_message(message.chat.id, answer, parse_mode='markdown', disable_web_page_preview=True) 
    home(message)

def search_rules(message):
    if message.text == 'Вернуться':
        home(message)
    page = requests.get('https://yandex.ru/support/search-results/?text=' + message.text.replace(' ', '+') + '&service=nmaps-guide')
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='serp__item'):
        if '...' in item.find_all('div')[0].text:
            title = item.find_all('div')[0].text.split('...')[0]
        else:
            title = item.find_all('div')[0].text.split('—')[0]
        excerpt = item.find_all('div')[1].text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + '): ' + excerpt + '\n'
        answer += '____________________\n'
    bot.send_message(message.chat.id, answer, parse_mode='markdown', disable_web_page_preview=True) 
    home(message)
    
@bot.message_handler(content_types=['text'])
def find_roads_hashtags(message):
    print('chat id: ' + str(message.chat.id))
    print('message id: ' + str(message.message_id))
    if message.forward_from:
        print('forwarded from: ' + str(message.forward_from))
        
@bot.callback_query_handler(func=lambda call:True)
def test_callback(call):
    if call.data == 'approved':
        bot.edit_message_text('⬇ Перекрытие установлено ⬇', chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == 'declined':
        bot.edit_message_text('⬇ Недостаточно информации ⬇', chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == 'spam':
        bot.edit_message_text('⬇ Пользователь заблокирован ⬇', chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == '__main__':
    bot.polling()