from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from filters import Main, IsOwner
from states import addAccount
from utils.db import InitDb
from aiogram.utils.callback_data import CallbackData
from callbacks import cb_account
from .add import dp, bot
from .account import dp, bot
from bot import dp, bot
import httpx

@dp.callback_query_handler(Main(), state='*')
async def undefined(call: types.CallbackQuery, state: FSMContext):
    print(call.data)
    await call.answer("⚠️ Функция временно не доступна")
