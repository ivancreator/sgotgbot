from .database import InitDb
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

async def unpack_data(**kwargs):
    keys, values = []
    for key, value in kwargs:
        keys.append(key)
        values.append(value)
    return (*keys, *values)

class Account():
    async def add(telegram_id: int, url: str, get='id', **kwargs):
        kwargs = await unpack_data(**kwargs)
        keys, values = kwargs[0], kwargs[1]
        return await db.execute(f"INSERT INTO accounts ({keys}) VALUES (%s) ON CONFLICT DO NOTHING RETURNING {get}", 
        (values))

    async def update(account_id: int, **kwargs):
        kwargs = await unpack_data(**kwargs)
        keys, values = kwargs[0], kwargs[1]
        return await db.execute(f"UPDATE accounts SET ({keys}) VALUES (%s) WHERE id = %s",
        (values, account_id))

    async def get_activeAccounts(telegram_id: int, select='*'):
        return await db.executeall(f"SELECT {select} FROM accounts WHERE telegram_id = %s AND status = 'active'", (select, telegram_id))

    async def get_registerAccount(telegram_id: int, select='*'):
        return await db.execute(f"SELECT {select} FROM accounts WHERE telegram_id = %s AND status = 'register'", (select, telegram_id))

    async def logout(account_id: int):
        return await db.execute("UPDATE accounts SET status = 'inactive', alert = False WHERE id = %s", (account_id))

class User():
    async def add(telegram_id, username, first_name, last_name, isOwner = False, BetaAccess = False, StartStatus = False):
        await db.execute(
            "INSERT INTO public.users(telegram_id, username, first_name, last_name, is_owner, beta_access, welcome_message) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (telegram_id, username, first_name, last_name, isOwner, BetaAccess, StartStatus))

    # Возвращает данные пользователя по Telegram ID
    async def data(telegram_id):
        response = await db.execute(
            f"SELECT * FROM users WHERE telegram_id = {telegram_id}")
        return response
