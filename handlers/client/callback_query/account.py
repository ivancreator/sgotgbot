from aiogram.dispatcher.filters import state
from aiogram.types.callback_query import CallbackQuery
from netschoolapi import NetSchoolAPI, errors
from netschoolapi.data import Announcement
from bot import dp, bot
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from filters import Main, IsOwner
from functions.client import cidSelect, sidSelect, pidSelect, cnSelect, sftSelect, scidSelect, getloginState
from states import addAccount, selectAccount
import states
from utils.db import InitDb
from aiogram.utils.callback_data import CallbackData
from callbacks import cb_account
import httpx, typing
from functions import getAnnouncements, accountsCheck, accountMenu, ns_sessions, accountLogin
from os import remove, path
from urllib.parse import unquote

@dp.callback_query_handler(Main(), cb_account.filter(action='account_select'), state=selectAccount.select)
async def accountSelect(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 Войти", callback_data=cb_account.new(action='account_selectConfirm', value=callback_data['value'])))
    markup.add(types.InlineKeyboardButton("🗑 Удалить", callback_data=cb_account.new(action='account_remove', value=callback_data['value'])))
    markup.add(types.InlineKeyboardButton("◀️ Вернуться", callback_data=cb_account.new(action='account_selectConfirm', value='')))
    await call.answer()
    await call.message.edit_text("✴️ Выберите действие", reply_markup=markup)

@dp.callback_query_handler(Main(), cb_account.filter(action='account_remove'), state=[selectAccount.select, selectAccount.menu])
async def accountRemove(call: types.CallbackQuery(), callback_data: dict, state: FSMContext):
    db = InitDb()
    data = await state.get_data()
    await db.execute(f"DELETE FROM accounts WHERE id = {callback_data['value']}")
    await call.answer("🗑 Учётная запись успешно удалена")
    await accountsCheck(data['usermsg'], state)
    await call.message.delete()

@dp.callback_query_handler(Main(), cb_account.filter(action='account_selectConfirm'), state=selectAccount.select)
async def accountselectConfirm(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    account_id = callback_data['value']
    if account_id:
        db = InitDb()
        account_tg_id = await db.execute("SELECT telegram_id FROM accounts WHERE id = %s", [account_id])
        if account_tg_id[0] == call.from_user.id:
            await call.answer()
            await call.message.edit_text("🕐 Выполняется вход в учётную запись")
            account = await db.execute("SELECT * FROM accounts WHERE id = %s", [account_id])
            try:
                await accountLogin(call.message, call.from_user.id, account[10], account[8], account[9], account[2], account[3], account[4], account[5], account[6], account[7])
            except Exception as e:
                raise e
            else:
                await db.execute("UPDATE accounts SET status = 'active' WHERE id = %s", [account_id])
                ns = ns_sessions[account_tg_id[0]]
                await accountMenu(call.message, state, ns)
        else:
            await call.answer("⚠ Это учётная запись принадлежит другому пользователю")
    else:
        data = await state.get_data()
        await call.answer()
        await accountsCheck(data['usermsg'], state)
        await call.message.delete()
        
@dp.callback_query_handler(Main(), cb_account.filter(action='getFile'), state=['*'])
async def getAttachments(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    try:
        await call.answer()
        file_msg = await call.message.answer("🕐 Немного подождите")
        db = InitDb()
        account = await db.execute("SELECT * FROM accounts WHERE telegram_id = %s AND status = 'active'", [call.from_user.id])
        ns = ns_sessions[call.from_user.id]
        await file_msg.edit_text("🔍 Поиск документа")
        attachments = [announcement async for announcement in getAnnouncements(ns) for attachment in announcement['attachments'] if attachment['id'] == int(callback_data['value'])][0]['attachments']
        for attachment in attachments:
            if attachment['id'] == int(callback_data['value']):
                try:
                    await file_msg.edit_text("📥 Загрузка документа")
                    response = await ns._client.get("attachments/"+str(attachment['id']))
                    filename = unquote(str(response.headers.get('filename')))
                    file = open(filename, "wb")
                    file.write(response.content)
                    file.close()
                    await file_msg.edit_text("📤 Отправка документа")
                    await call.message.answer_document(document=types.InputFile(filename))
                    await file_msg.delete()
                    remove(path.abspath(attachment['name']))
                except Exception as e:
                    print("Ошибка при получении документа: "+str(e))
                    print("Аргументы: "+str(e.args))
                    raise Exception("Unknown exception").with_traceback(e)
    except TypeError as e:
        await file_msg.edit_text("⚠️ Нет активных учётных записей")
    except IndexError as e:
        await file_msg.edit_text("📑 Документ не найден")
    except Exception as e:
        print("Ошибка при получении документа: "+ str(e))
        await file_msg.edit_text("⚠️ Неожиданная ошибка при получении документа")