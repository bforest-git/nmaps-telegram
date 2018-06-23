import os
from pony.orm import Database, PrimaryKey, Required, Optional


db_creds = {'host': os.getenv('DBHOST', 'localhost'),
            'database': os.getenv('DBNAME', 'bot'),
            'user': os.getenv('DBUSER', 'bot'),
            'password': os.getenv('DBPASS', 'bot')}

db = Database(provider='postgres', **db_creds)


class Roadblock(db.Entity):
    id = PrimaryKey(int, auto=True)
    author = Required(int, size=64)
    chat_id = Required(int, size=64)
    chat_message_id = Required(int, size=64)
    mods_message_id = Optional(int, size=64)
    roads_message_id = Optional(int, size=64)


class Banned(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(int, size=64)


class Rss(db.Entity):
    id = PrimaryKey(int, auto=True)
    last_published = Required(int, size=64)


class Subscriber(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(int, size=64)


db.generate_mapping(create_tables=True)
