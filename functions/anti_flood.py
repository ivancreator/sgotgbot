from aiogram import types
async def anti_flood(message: types.Message):
    await message.answer("Слишком частый запрос, попробуйте немного позже")