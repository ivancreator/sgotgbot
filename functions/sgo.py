from __future__ import with_statement
import threading
from bot import bot, dp
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from callbacks import cb_account
from states import addAccount, selectAccount
from netschoolapi import NetSchoolAPI, errors
from html import unescape
from bs4 import BeautifulSoup
from utils.db import db
from datetime import datetime
import httpx, asyncio

latency = 1
ns_sessions = {}
alert_threads = {}

class log:
    def __init__(self, filename):
        self.file = open(filename, "w", encoding="utf-8")

    async def write(self, log_type: str, message: str):
        now = datetime.now().strftime("[%d.%m.%Y %H:%M:%S.%f]")
        log_text = str(now) + " [" + str(log_type) + "] " + str(message)
        self.file.write(str(log_text) + "\n")
        print(log_text)
        
    async def close(self):
        self.file.close()

log = log("latest_log.txt")

async def accountLogin(account_id, message=None):
    try:
        ns = ns_sessions[account_id]
        if not ns._login_data:
            # del ns_sessions[account_id]
            raise errors.AuthError("Нет данных для входа")
    except (KeyError, errors.AuthError) as e:
        try:
            account = await db.execute("SELECT url, cid, sid, pid, cn, sft, scid, username, password, chat_id, display_name FROM accounts WHERE id = %s", [account_id])
            ns = NetSchoolAPI(account['url'])
            await ns.login(account['cid'], account['sid'], account['pid'], account['cn'], account['sft'], account['scid'], account['username'], account['password'])
            ns_sessions[account_id] = ns
            await db.execute("UPDATE accounts SET status = 'active' WHERE id = %s", [account_id])
            return ns
        except httpx.HTTPStatusError as e:
            if message:
                await message.edit_text("⚠️ Ошибка подключения к СГО, попробуйте ещё раз.")
            await log.write(str(account_id), "Ошибка кода HTTP: " + str(e))
            await log.write(str(account_id), "Аргументы: " + str(e.args))
            await log.write(str(account_id), "Запрос" + str(e.request))
            raise e
        except httpx.TimeoutException as e:
            if message:
                await message.edit_text("⚠️ Слишком долгое ожидание, попробуйте ещё раз")
            await log.write(str(account_id), "Долгое ожидание во время запроса: TimeoutException ("+str(e)+")")
            raise e
        except errors.AuthError as e:
            await log.write(str(account_id), "Обработанная ошибка входа во время запроса: "+str(e))
            if message:
                await message.edit_text("⚠️ "+str(e))
            else:
                if account['display_name']:
                    await bot.send_message(account['chat_id'], "⚠️ Ошибка входа в учётную запись %s, функция уведомлений отключена.\nПодробности: %s" % [str(account['display_name']), str(e)])
            # await db.execute("UPDATE accounts SET alert = False, status = 'inactive' WHERE id = %s", [account_id])
            raise e
        except Exception as e:
            if message:
                await message.edit_text("⚠️ Неожиданная ошибка")
            await log.write(str(account_id), "Неожиданная ошибка при входе ("+str(e)+")")
            raise e

# Функция получения объявлений в отформатированном виде
async def getAnnouncements(ns: NetSchoolAPI, take=-1):
    announcements = await ns.announcements(take=take)
    clear_announcements = []
    for announcement in announcements:
        tree = BeautifulSoup(unescape(announcement["content"]), 'html.parser')
        contents = tree.find_all("p")
        clear_content = []
        links = []
        for content in contents:
            atags = content.find_all("a", href=True)
            if atags:
                for atag in atags:
                    if str(atag.text).replace(' ', '') != str(atag.get("href")):
                        links.append({'text': atag.text, 'url': atag.get("href")})
            clear_content.append(str(content.text).replace('\xa0', ' '))
        text = "\n".join(clear_content)
        yield {'name': str(announcement['name']), 'content': announcement['content'], 'attachments': announcement['attachments'], 'post_date': announcement['post_date'], 'author': announcement['author'], 'id': announcement['id']}

# Функция нахождения новых объектов
async def getNew(old_data: tuple[dict], new_data: tuple[dict]):
    new_objects = list(new_data)
    old_objects = list(old_data)
    for old in old_objects:
        for new in new_objects:
            if old['id'] == new['id']:
                new_objects.remove(new)
    return new_objects

async def sendAnnouncement(chat_id: int, announcement, with_author=True, with_date=True):
    tree = BeautifulSoup(unescape(announcement["content"]), 'html.parser')
    contents = tree.find_all("p")
    clear_content = []
    clear_atags = []
    offset = 0
    for content in contents:
        offset += len(content.text) - 7
        atags = content.find_all("a", href=True)
        line_breaks = content.find_all("br")
        if line_breaks:
            for br in line_breaks:
                br.replace_with('\n')
        if atags:
            for atag in atags:
                text = str(atag.text).replace('\xa0', ' ')
                start = str(content).find(str(atag))
                end = start + len(text)
                if text.replace(' ', '') != str(atag.get("href")):
                    clear_atags.append(
                        {'text': text, 'href': atag.get("href"), 'offset': offset - end})
                    atag.unwrap()
        clear_content.append(content.text)
    date = announcement['post_date']
    info = str(announcement['name'])
    if with_author:
         info += "\n🗣 " + str(announcement['author']['nickName'])
    if with_date:
         info += "\n📅 " + str(date.strftime("%d.%m.%Y %H:%M:%S"))
    entity = [types.MessageEntity(type="bold", offset=0, length=len(announcement["name"])), types.MessageEntity(
        type="underline", offset=0, length=len(announcement["name"]))]
    text = "\n" + "\n".join(clear_content).replace('\xa0', ' ')
    message_text = str(info) + str(text)
    for atag in clear_atags:
        entity.append(types.MessageEntity(type="text_link", offset=text.find(
            atag["text"]) + len(info) + 2, length=len(atag["text"]), url=atag["href"]))
    attachments = announcement['attachments']
    if attachments:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for attachment in attachments:
            markup.add(types.InlineKeyboardButton("📎 "+str(attachment['name']), callback_data=cb_account.new(action='get_file', value=attachment['id'])))
        await bot.send_message(chat_id, message_text, entities=entity, reply_markup=markup)
    else:
        await bot.send_message(chat_id, message_text, entities=entity)

# def run_event_loop(coroutine):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.кгт(coroutine)
#     loop.close()

# def run_and_get(coroutine):
#     import nest_asyncio, asyncio
#     nest_asyncio.apply()
#     task = asyncio.create_task(coroutine)
#     asyncio.get_running_loop().run_until_complete(task)
#     return task.result()

async def add_checkThread(account_id, ns):
    loop = asyncio.get_running_loop()
    thread = alert_threads[account_id] = threading.Thread(name=str(account_id), target=asyncio.run_coroutine_threadsafe, args=(checkNew(account_id, ns),loop,))
    thread.start()

async def reStore():
    accounts = await db.executeall("SELECT id, alert, chat_id FROM accounts WHERE status = 'active'")
    for account in accounts:
        try:
            ns = await accountLogin(account['id'])
            if account['alert']:
                await add_checkThread(account['id'], ns)
            # print(account)
            # await asyncio.sleep(0.5)
        except Exception as e:
            await log.write("ОШИБКА", "Неожиданная ошибка при восстановлении сессии в СГО ("+str(e)+")")
            await bot.send_message(account['chat_id'], "❗️ Неожиданная ошибка при восстановлении сессии")
            raise e

async def closeAll():
    await log.close()
    for account_id, ns in tuple(ns_sessions.items()):
        await ns.logout()
        await ns._client.aclose()
        del ns_sessions[account_id]

async def checkNew(account_id, ns: NetSchoolAPI):
    try:
        account = await db.execute("SELECT id, alert, chat_id, display_name FROM accounts WHERE id = %s", [account_id])
        old_data = [announcemet async for announcemet in getAnnouncements(ns, take=-1)]
        while account['alert']:
            account = await db.execute("SELECT id, alert, chat_id, display_name FROM accounts WHERE id = %s", [account_id])
            if account['alert']:
                try:
                    await log.write(account['id'], "Check announcement updates")
                    new_data = [announcemet async for announcemet in getAnnouncements(ns, take=-1)]
                    if new_data != old_data:
                        await log.write(account['id'], "Find the announcement updates")
                        new_objects = await getNew(tuple(old_data), tuple(new_data))
                        if new_objects:
                            await log.write(account['id'], "Find the new announcement")
                            for new in new_objects:
                                await sendAnnouncement(account['chat_id'], new, with_date=False)
                        old_data = new_data
                except httpx.HTTPError as e:
                    # await bot.send_message(account['chat_id'], "⚠ Ошибка подключения при получении объявлений")
                    await log.write(str(account['id']), "Ошибка подключения: " + str(e))
                    await log.write(str(account['id']), "Аргументы: " + str(e.args))
                    if hasattr(e, 'request'):
                        await log.write(str(account['id']), "Запрос: " + str(e.request))
                    if hasattr(e, 'response'):
                        await log.write(str(account['id']), "Ответ: " + str(e.response))
                    continue
                finally:
                    await asyncio.sleep(latency)
            else:
                break
    except errors.AuthError as e:
        await bot.send_message(account['chat_id'], "⚠️ Ошибка входа в учётную запись "+str(account['display_name'])+", функция уведомлений отключена.")
        await log.write(str(account['id']), "Обработанная ошибка входа во время запроса: "+str(e))
        await db.execute("UPDATE accounts SET alert = False WHERE id = %s", [account['id']])
    except KeyError as e:
        await log.write(str(account['id']), "Ошибка ключа: "+str(e))
        await bot.send_message(account['chat_id'], "⚠️ Похоже, что какие-то данные учётной записи пропали")
    except TypeError as e:
        await log.write(str(account['id']), "Ошибка ключа: "+str(e))
        await bot.send_message(account['chat_id'], "⚠️ Кажется, что учётная запись исчезла")
    except Exception as e:
        await log.write(str(account['id']), "НЕОЖИДАННОЕ ИСКЛЮЧЕНИЕ: "+str(e))
        await bot.send_message(account['chat_id'], "❗️ Неожиданная ошибка при получении объявлений")
        raise e