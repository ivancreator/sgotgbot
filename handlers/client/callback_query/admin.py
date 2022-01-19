from aiogram.dispatcher.storage import FSMContext
from bot import dp, bot
from aiogram import types
from filters import IsOwner
from callbacks import cb_account
from functions import admin_menu, admin_userEdit
from utils.db import db

@dp.callback_query_handler(IsOwner(), cb_account.filter(action='admin_user_select'))
async def admin_userSelect(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    users = db.executeall("SELECT * FROM users")
    for x in users:
        if int(callback_data['user_id']) == x[0]:
            await bot.answer_callback_query(call.id)
            await admin_userEdit(call.message, x)
    await call.answer()

@dp.callback_query_handler(IsOwner(), cb_account.filter(action='admin_menu'))
async def admin_userSelect(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await admin_menu(call.message)
    await call.answer()

@dp.callback_query_handler(IsOwner(), cb_account.filter(action='admin_user_update'))
async def admin_userSelect(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    users = db.executeall("SELECT * FROM users")
    for x in users:
        await bot.answer_callback_query(call.id)
        if int(callback_data['user_id']) == x[0]:
            if callback_data['value'] == "beta_access":
                await db.execute(
                    f"UPDATE users SET beta_access = {query[3]} WHERE id = {query[2]}")
                await admin_userEdit(call.message, x)
            elif callback_data['value'] == "owner":
                await db.execute(
                    f"UPDATE users SET is_owner = {query[3]} WHERE id = {query[2]}")
                await admin_userEdit(call.message, x)
            elif callback_data['value'] == "start":
                await db.execute(
                    f"UPDATE users SET start = {query[3]} WHERE id = {query[2]}")
                await admin_userEdit(call.message, x)
    await call.answer()