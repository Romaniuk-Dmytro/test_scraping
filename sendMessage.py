from telethon import TelegramClient
import emoji
import sqlite3
from main import write_to_db
from keys import api_id, api_hash

API_ID = api_id
API_HASH = api_hash

with TelegramClient('scraper', API_ID, API_HASH) as client:
    print("Start successful")


async def main():
    conn = sqlite3.connect('cars.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM CAR_INFO;")
    query = cur.fetchall()
    for car in query:
        print(car)
        message_text = emoji.emojize(f'[{car[1]}]({car[6]})\n💴{car[2]}\n:gear:{car[3]}\n:pushpin:{car[4]}\n')
        message_text += emoji.emojize(f'🇺🇸[bidfax]({car[5]})' if car[5] else 'bidfax не знайдено')

        if car[9] == 0 and car[8] == 'new':
            await client.send_file('avtoria_cars', car[7].split('!'), caption=message_text)
        elif car[9] == 0 and car[8] == 'changed_price':
            await client.send_file('avtoria_cars', car[7].split('!'), caption='НОВА ЦІНА\n'+message_text)
        elif car[9] == 1 and car[8] == 'new' or car[8] == 'changed_status':
            await client.send_file('avtoria_cars', car[7].split('!'), caption='ПРОДАНО\n' + message_text)

        conn.execute(f"UPDATE CAR_INFO set MESSAGE = ? where VIN = ?",
                     ('sent', car[0],))
        conn.commit()

    conn.close()

write_to_db()
with client:
    client.loop.run_until_complete(main())
