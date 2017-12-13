from telegram import InlineQueryResultArticle, InputTextMessageContent
from config import rules, admins
from phrases import INLINE_TEMPLATE
from uuid import uuid4


def inline_search(bot, update):
    query = update.inline_query

    if query.from_user.id not in admins:
        return
    results = rules.search(query.query)

    articles = []
    for result in results['hits']:
        message_text = InputTextMessageContent(
            message_text=INLINE_TEMPLATE.format(result['path'],
                                                result['short'],
                                                result['url'],
                                                result['title']),
            parse_mode='html')
        articles.append(InlineQueryResultArticle(
            id=uuid4(),
            title=result['title'],
            url=result['url'],
            description=result['short'],
            input_message_content=message_text,
            hide_url=True))
    query.answer(articles, cache_time=0)
