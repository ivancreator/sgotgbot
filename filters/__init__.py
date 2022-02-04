from aiogram.dispatcher.filters import Filter
from aiogram import types
from utils.db import User, db

class IsOwner(Filter):
    key = 'is_owner'
    async def check(self, message: types.Message):
        response = await db.execute(
            f"SELECT is_owner FROM users WHERE telegram_id = {message.from_user.id}")
        if response[0]:
            return True

class Main(Filter):
    key = 'beta_access'
    async def check(self, message: types.Message):
        if await User.data(message.from_user.id):
            response = await db.execute(
                f"SELECT is_owner, beta_access FROM users WHERE telegram_id = {message.from_user.id}")
            if response:
                return True
            else:
                return True
        else:
            await userAdd(message)
            return True

async def userAdd(message):
    user = message.from_user
    await User.add(user.id, user.username,
                   user.first_name, user.last_name)