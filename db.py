import os
import psycopg2

db_creds = {'host': os.getenv('DBHOST', 'localhost'),
            'dbname': os.getenv('DBNAME', 'bot'),
            'user': os.getenv('DBUSER', 'bot'),
            'password': os.getenv('DBPASS', 'bot')}

db = psycopg2.connect(**db_creds)
c = db.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS roads (user_id bigint,
                                               chat_id bigint,
                                               chat_message_id bigint,
                                               mods_message_id bigint,
                                               roads_message_id bigint)''')

c.execute('''CREATE TABLE IF NOT EXISTS banned (id bigint primary key)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (option text unique, value text)''')
c.execute('''CREATE TABLE IF NOT EXISTS rss (last_published bigint primary key)''')

try:
    c.execute('INSERT INTO settings VALUES (%s, %s)', ('roads_moderation', 'enabled'))
except psycopg2.IntegrityError:
    pass

db.commit()
c.close()
