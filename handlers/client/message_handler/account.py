from typing import final
from bot import dp, bot
from aiogram import types
from filters import Main
from aiogram.dispatcher import FSMContext
from functions.anti_flood import anti_flood
from states import selectAccount
from functions.client import sendAnnouncements, accountsList
from functions.sgo import AnnouncementsError, add_checkThread, checkNew, ns_sessions
from netschoolapi import NetSchoolAPI
from utils.db.data import Account, db

@dp.message_handler(Main(), text="📋 Просмотр объявлений", state=selectAccount.menu)
@dp.throttled(anti_flood, rate=3)
async def announcements(message: types.Message, state: FSMContext):
    wait_message = await message.answer("🕐 Немного подождите")
    await message.delete()
    accounts = await Account.get_activeAccounts(message.from_user.id)
    account = accounts[0]
    account_id = account['id']
    ns = ns_sessions[account_id]
    try:
        await sendAnnouncements(message, ns, state)
    except AnnouncementsError:
        await message.answer("📋 Список объявлений пуст")
    await wait_message.delete()

@dp.message_handler(Main(), text="⚙️ Настройки", state=selectAccount.menu)
@dp.throttled(anti_flood, rate=3)
async def setting(message: types.Message, state: FSMContext):
    accounts = await Account.get_activeAccounts(message.from_user.id)
    account = accounts[0]
    account_id = account['id']
    if account['alert']:
        await db.execute("UPDATE accounts SET alert = False WHERE id = %s", [account_id])
        await message.answer("🔕 Уведомления отключены")
    else:
        ns = ns_sessions[account_id]
        await db.execute("UPDATE accounts SET alert = True WHERE id = %s ", [account_id])
        await message.answer("🔔 Уведомления включены")
        await add_checkThread(account_id, ns)
    await message.delete()

@dp.message_handler(Main(), text="🚪 Выход", state=selectAccount.menu)
async def exit(message: types.Message, state: FSMContext):
    exit_msg = await message.answer("🚪 Выполняется выход из учётной записи")
    await message.delete()
    accounts = await Account.get_activeAccounts(message.from_user.id)
    account = accounts[0]
    account_id = account['id']
    await Account.logout(account_id)
    data = await state.get_data()
    await data['message'].delete()
    await accountsList(message, state)
    try:
        await exit_msg.edit_text("🕐 Отправляется запрос на выход")
        ns = ns_sessions[account_id]
        await ns.logout()
        await ns._client.aclose()
        del ns_sessions[account_id]
    except Exception as e:
        print("Ошибка при выходе из учётной записи: %s" % e)
        await exit_msg.edit_text("❗ Возникла неожиданная ошибка при выходе из учётной записи")
    else:
        await exit_msg.delete()
