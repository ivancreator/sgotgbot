from .database import InitDb
from psycopg2 import sql
import json

db = InitDb()

class InitData():

    async def dataSetup(self):
        await db.execute(
            'CREATE TABLE IF NOT EXISTS regions (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, display_name text, site text)')
        await db.execute(
            'CREATE TABLE IF NOT EXISTS users (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, telegram_id integer, username text, first_name text, last_name text, is_owner integer, beta_access integer, start integer)')
        await db.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, telegram_id integer, cid integer, sid integer, pid integer, cn integer, sft integer, scid integer, login text, password text, url text, nickname text, school_name text, class_name text)")


class Update():

    async def regionsUpdate(self):
        regions = json.load(open("regions.json", mode="r", encoding="utf-8"))
        await db.executemany(
            'INSERT INTO regions (display_name, site) VALUES (%s, %s) ON CONFLICT DO NOTHING', regions)

class Account():
    async def add(telegram_id: int, url: str, get=['id'], **kwargs):
        kwargs.update({'telegram_id': telegram_id, 'url': url, 'status': 'register'})
        query = await db.execute(sql.SQL("INSERT INTO accounts ({columns}) VALUES ({values}) ON CONFLICT DO NOTHING RETURNING ({returning})").format(
            columns=sql.SQL(', ').join(map(sql.Identifier, kwargs.keys())),
            values=sql.SQL(', ').join(sql.Placeholder() * len(kwargs)),
            returning=sql.SQL(', ').join(map(sql.Identifier, get))
            ), 
        [kwargs.values()])
        return query[0]

    async def update(account_id: int, **kwargs):
        return await db.execute(sql.SQL("UPDATE accounts SET ({columns}) = ({values}) WHERE id = %s".format(
            columns=sql.SQL(', ').join(map(sql.Identifier, kwargs.keys())),
            values=sql.SQL(', ').join(sql.Placeholder() * len(kwargs))
        ),
        [kwargs.values(), account_id]))

    async def get_activeAccounts(telegram_id: int):
        return await db.executeall(sql.SQL("SELECT * FROM accounts WHERE telegram_id = %s AND status = 'active'"), [telegram_id])

    async def get_registerAccount(telegram_id: int):
        return await db.execute(sql.SQL("SELECT * FROM accounts WHERE telegram_id = %s AND status = 'register'"), [telegram_id])

    async def logout(account_id: int):
        return await db.execute("UPDATE accounts SET status = 'inactive', alert = False WHERE id = %s", [account_id])

class User():
    async def add(telegram_id, username, first_name, last_name, isOwner = False, BetaAccess = False, StartStatus = False):
        await db.execute(
            "INSERT INTO public.users(telegram_id, username, first_name, last_name, is_owner, beta_access, welcome_message) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (telegram_id, username, first_name, last_name, isOwner, BetaAccess, StartStatus))

    # Возвращает данные пользователя по Telegram ID
    async def data(telegram_id):
        response = await db.execute(
            f"SELECT * FROM users WHERE telegram_id = {telegram_id}")
        return response
