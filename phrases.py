HASH_SCREEN = 'скрин'
HASH_SCREEN_ENG = 'screen'
HASH_ROADBLOCK = 'перекрытие'
HASH_ROADBLOCK_ENG = 'roadblock'

BOT_ACTION_SELECT = 'Пожалуйста, выберите действие.'
BOT_CHS_LINK = 'Для перехода на сайт нажмите нужную кнопку из списка.'
BOT_SRCH_QUERY = 'Напишите фразу для поиска. Для возврата воспользуйтесь кнопкой меню.'
BOT_SRCH_CONTINUE = 'Вы можете написать следующий запрос или вернуться в меню.'
BOT_NOT_FOUND = 'К сожалению, ничего не найдено.'
BOT_MSG_ACCEPT = '{}, сообщение принято. Спасибо!'
BOT_REQUEST_CHECK = 'Пользователь {} оставил следующее сообщение. Просьба проверить информацию.'
BOT_SENT_TO_STAFF = '✅ Направлено сотрудникам (отправил [{}](tg://user?id={}))'
BOT_NEW_ROADBLOCK = 'Добрый день. Появилась новая информация о перекрытии. ⤴️'
BOT_INVESTIGATING = '📋 Выясняет [{}](tg://user?id={})'
BOT_USER_BANNED = '🚫 Пользователь заблокирован (модератор [{}](tg://user?id={}))'
BOT_ROADBLOCK_SET = '✅ Перекрытие установлено ([{}](tg://user?id={}))'
BOT_ROADBLOCK_SET_USR = 'Перекрытие установлено, спасибо! Изменения вступят в силу в течение 15 минут.'
BOT_ROADBLOCK_DEL = '✅ Перекрытие снято ([{}](tg://user?id={}))'
BOT_ROADBLOCK_DEL_USR = 'Перекрытие снято, спасибо! Изменения вступят в силу в течение 15 минут.'
BOT_INFOPOINT_SET = '✅ Инфоточка установлена ([{}](tg://user?id={}))'
BOT_INFOPOINT_SET_USR = 'Инфоточка установлена, спасибо! Изменения вступят в силу в течение 15 минут.'
BOT_UNDER_INVESTIGATION = 'Данным сообщением занимается другой модератор.'
BOT_PRIVATE_ROAD_REPORT_USR = 'Вы можете сообщить о предстоящем или имеющемся перекрытии дороги. Обратите внимание на следующие правила:\n\n1. Сообщаем только про оперативные изменения в дорожной обстановке: началось или окончилось строительство развязки, праздничные или иные перекрытия, требующие вмешательства;\n2. К своему сообщению обязательно прикрепите ссылку на место в Яндекс.Карте и/или статью в СМИ, подтверждающую факт закрытия дороги;\n3. В своё сообщение добавьте хэштег #{}, чтобы бот среагировал на сообщение.\n\nСпасибо!'.format(HASH_ROADBLOCK)
BOT_SEND_FEEDBACK_USR = 'Мы будем благодарны, если Вы оставите свой отзыв или пожелания по поводу расширения функционала нашего бота. Написанное далее сообщение будет передано разработчикам анонимно.'
BOT_FEEDBACK_SENT_USR = 'Спасибо, Ваше сообщение получено.'
BOT_NOT_ROAD_STAFF = 'Вы не являетесь сотрудником отдела маршрутизации.'
BOT_REQUEST_CANCELLED = '❌ Сообщение отклонено ([{}](tg://user?id={}))'
BOT_REQUEST_CANCELLED_USR = 'По данному сообщению действия не требуются.'
BOT_ILLEGAL_URL = 'Функция скриншотов доступна только для ссылок на Яндекс.Карты и НЯК.'
BOT_SUBSCRIBED_USR = 'Вы были успешно подписаны на новые оповещения. До встречи!'
BOT_UNSUBSCRIBED_USR = 'Вы отписались от дальнейших уведомлений.'
BOT_UNRECOGNIZED_MESSAGE = 'Увы, я ничего не понял. Давайте начнём заново.'
BOT_CANCELLED = 'Возвращаемся в главное меню.'
BOT_UNEXPECTED_ERROR = 'Произошла непредвиденная ошибка.'
BOT_SCREEN_REQUESTED = 'Одну минуту.'
BOT_YM_SCREENS_BANNED = 'Взятие скриншотов ЯК временно недоступно.'
BOT_INLINE_INSTRUCTIONS = '*Как пользоваться поиском по рубрикатору?*\nВведите имя бота (@nmapsbot) в окне для сообщения и начните писать поисковый запрос.\n\nНапример:\n`@nmapsbot детская одежда`\n\nВ появившемся окне нажмите на подходящую рубрику. После этого она будет отправлена в текущий чат вместе с описанием.'

MENU_RETURN = '⬅ Вернуться'
MENU_SEARCH = '🔎 Поиск'
MENU_LINKS = '📌 Полезные ссылки'
MENU_SEARCH_CLUB = '🔎 Поиск в Клубе'
MENU_SEARCH_RULES = '🔎 Поиск в Правилах'
MENU_FAQ = '📚 Частые вопросы'
MENU_SUPPORT = '✏ Служба поддержки'
MENU_ROADS = '🚫 Сообщить о перекрытии'
MENU_FEEDBACK = '💬 Оставить отзыв'
MENU_SUBSCRIBE = '🔔 Подписаться на рассылку'
MENU_UNSUBSCRIBE = '🔕 Отписаться от рассылки'

BTN_ROADS_ACCEPT = '↩ Передать сотрудникам'
BTN_ROADS_REQUEST_INFO = '🔫 Запросить информацию'
BTN_ROADS_FRAUD = '🚫 Вандализм'
BTN_ROADS_CLOSED = '🚧 Перекрытие установлено'
BTN_ROADS_OPENED = '🚗 Перекрытие снято'
BTN_ROADS_INFOPOINT = '⚠ Инфоточка установлена'
BTN_CANCEL = '❌ Изменения не нужны'
BTN_NEXT_PAGE = '▶️'
BTN_PREV_PAGE = '◀️'

INLINE_HELP_BUTTON = 'Помощь'
inline_templates = {'rules': {'text': '<b>Правила рисования</b>\n{}\n\n<b>{}</b>\n<i>Кратко:</i> {}\n\n<a href="{}">Перейти к пункту правил</a>',
                              'args': ('path', 'title', 'short', 'url')
                              },
                    'rubrics': {'text': '<b>Рубрикатор</b>\n\n<b>Рубрика: {}</b>\n{}\n\n<a href="https://yandex.ru/support/nmaps/app_poi.html">Перейти в рубрикатор</a>',
                                'args': ('title', 'text')}}
