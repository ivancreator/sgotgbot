from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from filters import Main
from .add import dp
from .account import dp
from bot import dp

@dp.callback_query_handler(Main(), state='*')
async def undefined(call: types.CallbackQuery, state: FSMContext):
    print(call.data)
    await call.answer("⚠️ Такого запроса нет")
