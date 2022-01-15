from bot import dp, bot
from aiogram import types
from filters import Main
from aiogram.dispatcher import FSMContext
from states import selectAccount
from functions.client import sendAnnouncements, accountsList
from functions.sgo import checkNew, ns_sessions
from netschoolapi import NetSchoolAPI
from utils.db.database import InitDb

@dp.message_handler(Main(), text="📋 Просмотр объявлений", state=selectAccount.menu)
async def announcements(message: types.Message, state: FSMContext):
    wait_message = await message.answer("🕐 Немного подождите")
    await message.delete()
    ns = ns_sessions[message.from_user.id]
    await sendAnnouncements(message, ns, state)
    await wait_message.delete()

@dp.message_handler(Main(), text="⚙️ Настройки", state=selectAccount.menu)
async def setting(message: types.Message, state: FSMContext):
    db = InitDb()
    account = await db.execute("SELECT * FROM accounts WHERE telegram_id = %s AND status = 'active'", [message.from_user.id])
    if account[16]:
        await db.execute("UPDATE accounts SET alert = False WHERE telegram_id = %s AND status = 'active'", [message.from_user.id])
        await message.answer("🔕 Уведомления отключены")
    else:
        ns = ns_sessions[message.from_user.id]
        await db.execute("UPDATE accounts SET alert = True, chat_id = %s WHERE telegram_id = %s AND status = 'active'", [message.chat.id, message.from_user.id])
        await message.answer("🔔 Уведомления включены")
        await checkNew(message.from_user.id, message.chat.id, ns)
    await message.delete()

@dp.message_handler(Main(), text="🚪 Выход", state=selectAccount.menu)
async def exit(message: types.Message, state: FSMContext):
    db = InitDb()
    account_id = await db.execute("SELECT id FROM accounts WHERE telegram_id = %s AND status = 'active'", [message.from_user.id])
    await db.execute("UPDATE accounts SET status = 'inactive' AND alert = False WHERE id = %s", [account_id])
    data = await state.get_data()
    ns = ns_sessions[message.from_user.id]
    await ns.logout()
    del ns_sessions[message.from_user.id]
    await accountsList(message, state)
    await data['message'].delete()
    await message.delete()
