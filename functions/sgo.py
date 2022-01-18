from bot import bot
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from callbacks import cb_account
from states import addAccount, selectAccount
from netschoolapi import NetSchoolAPI, errors
from html import unescape
from bs4 import BeautifulSoup
from utils.db import InitDb
from datetime import datetime
import httpx, asyncio

latency = 5
ns_sessions = {}

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

async def accountLogin(message: types.Message, user_id: int, url: str, login: str, password: str, cid, sid, pid, cn, sft, scid):
    try:
        ns = ns_sessions[user_id]
        if not ns._login_data:
            raise KeyError("No login data")
    except KeyError:
        try:
            ns = NetSchoolAPI(url)
            await ns.login(login, password, cid, sid, pid, cn, sft, scid)
        except httpx.HTTPStatusError as e:
            await message.edit_text("⚠️ Ошибка подключения к СГО, попробуйте ещё раз.")
            await log.write("Ошибка кода HTTP", str(e))
            await log.write("Аргументы", str(e.args))
            await log.write("Запрос", str(e.request))
            raise e
        except httpx.TimeoutException as e:
            await message.edit_text("⚠️ Слишком долгое ожидание, попробуйте ещё раз")
            await log.write("Долгое ожидание", "Во время запроса: TimeoutException ("+str(e)+")")
            raise e
        except errors.AuthError as e:
            await message.edit_text("⚠️ "+str(e))
            await log.write("Ошибка входа", "Во время запроса: Не верные данные для входа, AuthError ("+str(e)+")")
            raise e
        except errors.NetSchoolAPIError as e:
            await message.edit_text("⚠️ "+str(e))
            await log.write("Ошибка в форме СГО", "Во время запроса: NetSchoolAPIError ("+str(e)+")")
            raise e
        else:
            ns_sessions[user_id] = ns

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

async def sendAnnouncement(chat_id: int, announcement):
    tree = BeautifulSoup(unescape(announcement["content"]), 'html.parser')
    contents = tree.find_all("p")
    clear_content = []
    atags_raw = []
    for content in contents:
        atags = content.find_all("a", href=True)
        if atags:
            for atag in atags:
                if str(atag.text).replace('\xa0', ' ').replace(' ', '') != str(atag.get("href")):
                    atags_raw.append(
                        {'text': atag.text, 'href': atag.get("href")})
        clear_content.append(content.text)
    # date = announcement['post_date']
    info = str(announcement['name']) + "\n🗣 " + str(announcement['author']['nickName']) + "\n"
    entity = [types.MessageEntity(type="bold", offset=0, length=len(announcement["name"])), types.MessageEntity(
        type="underline", offset=0, length=len(announcement["name"]))]
    text = "\n".join(clear_content)
    message_text = str(info) + str(text)
    for atag in atags_raw:
        entity.append(types.MessageEntity(type="text_link", offset=text.find(
            atag["text"]) + len(info) + 1, length=len(atag["text"]), url=atag["href"]))
    attachments = announcement['attachments']
    if attachments:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for attachment in attachments:
            markup.add(types.InlineKeyboardButton("📎 "+str(attachment['name']), callback_data=cb_account.new(action='getFile', value=attachment['id'])))
        await bot.send_message(chat_id, message_text, entities=entity, reply_markup=markup)
    else:
        await bot.send_message(chat_id, message_text, entities=entity)

async def checkAlerts():
    db = InitDb()
    accounts = await db.executeall("SELECT * FROM accounts WHERE alert = True AND status = 'active'")
    for account in accounts:
        try:
            ns = ns_sessions[account[1]] = NetSchoolAPI(account[10])
            await ns.login(account[8], account[9], account[2], account[3], account[4], account[5], account[6], account[7])
            await checkNew(account[1], account[15], ns)
        except errors.AuthError as e:
            await log.write("ОБРАБОТАННАЯ ОШИБКА", "При запуске: Не верные данные для входа ("+str(e)+")")
            await db.execute("UPDATE accounts SET alert = False WHERE id = %s", [account[0]])
            await bot.send_message(account[15], "⚠️ Ошибка входа в учётную запись ("+str(account[12])+"), функция уведомлений отключена.")
        except Exception as e:
            await log.write("ОШИБКА", "Неожиданная ошибка при входе в СГО ("+str(e)+")")
            await bot.send_message(account[15], "❗️ Неожиданная ошибка")

async def closeAll():
    await log.close()
    print("Logout all sessions\n"+str(ns_sessions))
    for session in ns_sessions.items():
        print(str("tgID: ")+str(session[0]))
        ns = session[1]
        print("Class object: "+str(session[1]))
        await ns.logout()

async def checkNew(telegram_id, chat_id, ns: NetSchoolAPI):
    try:
        db = InitDb()
        account = await db.execute("SELECT id, alert FROM accounts WHERE telegram_id = %s AND status = 'active'", [telegram_id])
        old_data = [announcemet async for announcemet in getAnnouncements(ns, take=2)]
        while account[1]:
            account = await db.execute("SELECT id, alert FROM accounts WHERE id = %s", [account[0]])
            await log.write(account[0], "Check announcement updates")
            new_data = [announcemet async for announcemet in getAnnouncements(ns, take=2)]
            if new_data != old_data:
                await log.write(account[0], "Find the announcement updates")
                new_objects = await getNew(tuple(old_data), tuple(new_data))
                if new_objects:
                    await log.write(account[0], "Find the new announcement")
                    for new in new_objects:
                        await sendAnnouncement(chat_id, new)
                old_data = new_data
            await asyncio.sleep(latency)
    except (httpx.HTTPError) as e:
        await bot.send_message(chat_id, "⚠ Ошибка подключения при получении объявлений")
        await log.write("Ошибка подключения", str(e))
        await log.write("Аргументы", str(e.args))
        await log.write("Запрос", str(e._request))
        await checkNew(telegram_id, chat_id, ns)
    except errors.AuthError as e:
        await bot.send_message(chat_id, "⚠️ Ошибка входа в учётную запись ("+str(account[12])+"), функция уведомлений отключена.")
        await log.write("ОБРАБОТАННАЯ ОШИБКА", "Во время запроса: Не верные данные для входа ("+str(e)+")")
        await db.execute("UPDATE accounts SET alert = False WHERE id = %s", [account[0]])
    except Exception as e:
        await log.write("НЕОЖИДАННОЕ ИСКЛЮЧЕНИЕ", str(e))
        await bot.send_message(chat_id, "❗️ Неожиданная ошибка при получении объявлений")
        raise Exception("Unknown exception") from e