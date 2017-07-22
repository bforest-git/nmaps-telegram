import requests, telebot
from telebot import types
from bs4 import BeautifulSoup

bot = telebot.TeleBot('405295345:AAEiq-A3mEVsE203a0qOM3z2QCpPOlMKbZ0')

def private_chat(message):
    if message.chat.type == 'private': return True

@bot.message_handler(commands=['start', 'home'])
def home(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row('📌 Полезные ссылки')
    keyboard.row('🔎 Поиск в Клубе', '🔎 Поиск в Правилах')
    keyboard.row('🚫 Сообщить о перекрытии')
    keyboard.row('📚 Частые вопросы', '✏ Служба поддержки')
    bot.send_message(message.chat.id, 'Пожалуйста, выберите действие.', reply_markup=keyboard)
    
@bot.message_handler(regexp='📌 Полезные ссылки')
def bookmarks(message):
    if not private_chat(message):
        return
    keyboard = types.InlineKeyboardMarkup()
    url1 = types.InlineKeyboardButton(text='Правила', url='https://yandex.ru/support/nmaps/rules_2.html')
    url2 = types.InlineKeyboardButton(text='Клуб', url='https://yandex.ru/blog/narod-karta')
    url3 = types.InlineKeyboardButton(text='ПКК', url='https://pkk5.rosreestr.ru/')
    url4 = types.InlineKeyboardButton(text='ФИАС', url='https://fias.nalog.ru/')
    url5 = types.InlineKeyboardButton(text='ЕГРП365', url='https://egrp365.ru/map/')
    url6 = types.InlineKeyboardButton(text='TerraServer', url='https://www.terraserver.com/')
    url7 = types.InlineKeyboardButton(text='Реформа ЖКХ', url='https://www.reformagkh.ru/')
    keyboard.add(url1, url2, url3, url4, url5, url6, url7)
    bot.send_message(message.chat.id, 'Для перехода на сайт нажмите нужную кнопку из списка.', reply_markup=keyboard)
    home(message)
    
@bot.message_handler(regexp='🔎 Поиск')
def search(message):
    if not private_chat(message):
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row('⬅ Вернуться')
    bot.send_message(message.chat.id, 'Напишите фразу для поиска.', reply_markup=keyboard)
    if message.text == '🔎 Поиск в Правилах':
        bot.register_next_step_handler(message, search_rules)
    elif message.text == '🔎 Поиск в Клубе':
        bot.register_next_step_handler(message, search_club)
    elif message.text == '⬅ Вернуться':
        home(message)
        
def search_club(message):
    if message.text == '⬅ Вернуться':
        home(message)
        return
    page = requests.get('https://yandex.ru/blog/narod-karta/search?text=' + message.text.replace(' ', '+'))
    soup = BeautifulSoup(page.text, 'lxml')
    answer = ''
    for item in soup.find_all('a', class_='b-serp-item'):
        pass
        title = item.find('h2').text
        link = 'https://yandex.ru' + item['href']
        answer += '[' + title + '](' + link + ')\n'
        answer += '____________________\n'
    if not answer:
        bot.send_message(message.chat.id, 'К сожалению, ничего не найдено.') 
    else:
        bot.send_message(message.chat.id, answer, parse_mode='markdown', disable_web_page_preview=True) 
    home(message)

def search_rules(message):
    if message.text == '⬅ Вернуться':
        home(message)
        return
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
    if not answer:
        bot.send_message(message.chat.id, 'К сожалению, ничего не найдено.') 
    else:
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