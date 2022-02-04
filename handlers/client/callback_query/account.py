import tempfile
from bot import dp, bot
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from filters import Main, IsOwner
from handlers.client.callback_query.add import account_add
from states import addAccount, selectAccount
from utils.db import db
from callbacks import cb_account
from functions import getAnnouncements, accountsCheck, accountMenu, ns_sessions, accountLogin
from urllib.parse import unquote
from utils.db.data import Account

@dp.callback_query_handler(Main(), cb_account.filter(action='select'), state=selectAccount.select)
async def accountSelect(call: types.CallbackQuery, callback_data: dict):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 Войти", callback_data=cb_account.new(action='select_confirm', value=callback_data['value'])))
    markup.add(types.InlineKeyboardButton("🗑 Удалить", callback_data=cb_account.new(action='remove', value=callback_data['value'])))
    markup.add(types.InlineKeyboardButton("◀️ Вернуться", callback_data=cb_account.new(action='list', value='')))
    await call.answer()
    await call.message.edit_text("✴️ Выберите действие", reply_markup=markup)

@dp.callback_query_handler(Main(), cb_account.filter(action='remove'), state=[selectAccount.select, selectAccount.menu])
async def accountRemove(call: types.CallbackQuery(), callback_data: dict, state: FSMContext):
    account_id = int(callback_data['value'])
    data = await state.get_data()
    try:
        ns = ns_sessions[account_id]
        await ns.logout()
        await ns._client.aclose()
        del ns_sessions[account_id]
    finally:
        await db.execute("DELETE FROM accounts WHERE id = %s", [account_id])
        await call.answer("🗑 Учётная запись успешно удалена")
        await accountsCheck(data['usermsg'], state)
        await call.message.delete()

@dp.callback_query_handler(Main(), cb_account.filter(action='list'), state=['*', selectAccount.select])
async def accountsList(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    await accountsCheck(data['usermsg'], state)
    await call.message.delete()

@dp.callback_query_handler(Main(), cb_account.filter(action='select_confirm'), state=selectAccount.select)
async def accountselectConfirm(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    account_id = int(callback_data['value'])
    account = await db.execute("SELECT telegram_id FROM accounts WHERE id = %s", [account_id])
    if call.from_user.id == account['telegram_id']:
        await call.answer()
        await call.message.edit_text("🕐 Выполняется вход в учётную запись")
        try:
            await accountLogin(account_id, message=call.message)
        except Exception as e:
            raise e
        else:
            ns = ns_sessions[account_id]
            await accountMenu(call.message, state)
            await call.message.delete()
    else:
        await call.answer("⚠ Это учётная запись принадлежит другому пользователю")
        
@dp.callback_query_handler(Main(), cb_account.filter(action='get_file'), state=['*'])
async def getAttachments(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    try:
        await call.answer()
        file_msg = await call.message.answer("🕐 Немного подождите")
        active_accounts = await Account.get_activeAccounts(call.from_user.id)
        for account in active_accounts:
            account_id = account['id']
            ns = ns_sessions[account_id]
            await file_msg.edit_text("🔍 Поиск документа")
            attachments = [announcement async for announcement in getAnnouncements(ns) for attachment in announcement['attachments'] if attachment['id'] == int(callback_data['value'])][0]['attachments']
            for attachment in attachments:
                if attachment['id'] == int(callback_data['value']):
                    try:
                        await file_msg.edit_text("📥 Загрузка документа")
                        response = await ns._request_with_optional_relogin("attachments/"+str(attachment['id']))
                        filename = unquote(str(response.headers.get('filename')))
                        with tempfile.TemporaryDirectory() as directory, open("%s/%s" % (directory, filename), "wb") as file:
                            file.write(response.content)
                            await file_msg.edit_text("📤 Отправка документа")
                            await call.message.answer_document(document=types.InputFile("%s/%s" % (directory, filename)))
                            await file_msg.delete()
                    except Exception as e:
                        print("Ошибка при получении документа: "+str(e))
                        print("Аргументы: "+str(e.args))
                        raise e
    except (TypeError, KeyError) as e:
        await file_msg.edit_text("⚠️ Нет активных учётных записей")
    except IndexError as e:
        await file_msg.edit_text("📑 Документ не найден")
    except Exception as e:
        print("Ошибка при получении документа: "+ str(e))
        await file_msg.edit_text("⚠️ Неожиданная ошибка при получении документа")
        raise e