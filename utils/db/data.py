from .database import InitDb
import json


class InitData():

    async def dataSetup(self):
        db = InitDb()
        await db.execute(
            'CREATE TABLE IF NOT EXISTS regions (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, display_name text, site text)')
        await db.execute(
            'CREATE TABLE IF NOT EXISTS users (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, telegram_id integer, username text, first_name text, last_name text, is_owner integer, beta_access integer, start integer)')
        await db.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, telegram_id integer, cid integer, sid integer, pid integer, cn integer, sft integer, scid integer, login text, password text, url text, nickname text, school_name text, class_name text)")


class Update():

    async def regionsUpdate(self):
        regions = json.load(open("regions.json", mode="r", encoding="utf-8"))
        regions_db = InitDb()
        await regions_db.executemany(
            'INSERT INTO regions (display_name, site) VALUES (%s, %s) ON CONFLICT DO NOTHING', regions)


class Account():
    async def add(telegram_id: int, cid: int, sid: int, pid: int, cn: int, sft: int, scid: int, login: str, password: str, url: str, nickname: str):
        data_db = InitDb()
        return await data_db.execute("INSERT INTO accounts (telegram_id, cid, sid, pid, cn, sft, scid, login, password, url, display_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING id", 
        (telegram_id, cid, sid, pid, cn, sft, scid, login, password, url, nickname))


class User():
    async def add(telegram_id, username, first_name, last_name, isOwner = False, BetaAccess = False, StartStatus = False):
        db = InitDb()
        await db.executemany(
            "INSERT INTO public.users(telegram_id, username, first_name, last_name, is_owner, beta_access, welcome_message) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", [(telegram_id, username, first_name, last_name, isOwner, BetaAccess, StartStatus)])

    # Возвращает данные пользователя по Telegram ID
    async def data(telegram_id):
        db = InitDb()
        response = await db.execute(
            f"SELECT * FROM users WHERE telegram_id = {telegram_id}")
        return response
