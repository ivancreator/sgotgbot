# from bot import dp
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from callbacks import cb_account
import httpx
from states import addAccount, selectAccount
from netschoolapi import NetSchoolAPI, errors
from html import unescape
from bs4 import BeautifulSoup
from utils.db import InitDb
from os import path, remove
from functions.sgo import getAnnouncements, sendAnnouncement, ns_sessions, log

async def accountMenu(message: types.Message, state: FSMContext, ns):
    db = InitDb()
    await selectAccount.menu.set()
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton("📋 Просмотр объявлений"))
    markup.row(types.KeyboardButton("⚙️ Настройки"), types.KeyboardButton("🚪 Выход"))
    msg = await message.answer("🗂 Меню управления учётной записью", reply_markup=markup)
    async with state.proxy() as data:
        data['message'] = msg
    await message.delete()

async def accountAdd(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(
        '➕ Добавить учётную запись', callback_data=cb_account.new(action='add', value='')))
    await message.answer(
        '➕Нажмите на соответствующую кнопку чтобы добавить данные для входа в учётную запись Сетевого Города', reply_markup=markup)

async def accountsCheck(message: types.Message, state: FSMContext):
    db = InitDb()
    data = await db.executeall(f"SELECT * FROM accounts WHERE telegram_id = {message.from_user.id}")
    if data:
        await accountsList(message, state)
    else:
        await accountAdd(message)

async def accountsList(message: types.Message, state: FSMContext):
    db = InitDb()
    accounts_data = await db.executeall(f"SELECT * FROM accounts WHERE telegram_id = {message.from_user.id}")
    await selectAccount.select.set()
    async with state.proxy() as data:
        data['usermsg'] = message
    markup = types.InlineKeyboardMarkup()
    for x in accounts_data:
        markup.add(types.InlineKeyboardButton(x[12], callback_data=cb_account.new(action='account_select', value=str(x[0]))))
    markup.row(types.InlineKeyboardButton(
        '➕ Добавить учётную запись', callback_data=cb_account.new(action='add', value='')))
    await message.answer("📃 Выберите учётную запись", reply_markup=markup)

async def admin_menu(message: types.Message):
    db = InitDb()
    users = await db.executeall("SELECT * FROM users")
    markup = types.InlineKeyboardMarkup()
    for x in users:
        markup.add(types.InlineKeyboardButton(
            x[3] + " " + x[4] + " ("+x[2]+")", callback_data="admin_user_select~"+str(x[0])))
    text = "Выберите пользователя"
    if message.text != "/admin":
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)

async def admin_userEdit(message: types.Message, x):
    users_db = InitDb()
    user = await users_db.execute(f"SELECT * FROM users WHERE id = {x[0]}")
    markup = types.InlineKeyboardMarkup()
    if user[5]:
        markup.add(types.InlineKeyboardButton(
            "Забрать владение", callback_data="admin_user_update~owner~"+str(user[0])+"~0"))
    else:
        markup.add(types.InlineKeyboardButton(
            "Сделать владельцем", callback_data="admin_user_update~owner~"+str(user[0])+"~1"))
    if user[6]:
        markup.add(types.InlineKeyboardButton(
            "Запретить бета-доступ", callback_data="admin_user_update~beta_access~"+str(user[0])+"~0"))
    else:
        markup.add(types.InlineKeyboardButton(
            "Выдать бета-доступ", callback_data="admin_user_update~beta_access~"+str(user[0])+"~1"))
    if user[7]:
        markup.add(types.InlineKeyboardButton(
            "Сбросить приветствие", callback_data="admin_user_update~start~"+str(user[0])+"~0"))
    else:
        markup.add(types.InlineKeyboardButton(
            "Убрать приветствие", callback_data="admin_user_update~start~"+str(user[0])+"~1"))

    markup.add(types.InlineKeyboardButton(
        "◀️ Назад", callback_data="admin_menu"))
    await message.edit_text("Информация о пользователе\nИмя: "+user[3]+"\nФамилия: "+user[4]+"\nИмя пользователя: "+user[2]+"\nTelegram ID: "+str(user[1])+"\nВладелец: "+str(user[5])+"\nБета-доступ: "+str(user[6])+"\nПриветствие: "+str(user[7]), reply_markup=markup)

async def sendAnnouncements(message: types.Message, ns: NetSchoolAPI, state, sft = None):
    data = await state.get_data()
    announcements = [x async for x in getAnnouncements(ns)]
    for announcement in announcements:
        await sendAnnouncement(message.chat.id, announcement)

async def schoolInfo(message: types.Message, state: FSMContext, url: str, sft, scid, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    school_info = await ns._client.get("schools/" +
                         str(scid)+"/card")
    markup = types.InlineKeyboardMarkup()
    if school_info.status_code == 200:
        school = school_info.json()
        markup.add(types.InlineKeyboardButton(
            "🔐 Войти", callback_data=cb_account.new(action='login_select', value=scid)))
        await message.edit_text("🏫 "+school["commonInfo"]["schoolName"]+" ("+school["commonInfo"]["status"]+")\n👤 "+school["managementInfo"]["director"]+"\n📍 "+school["contactInfo"]["postAddress"]+"\n⁉️ Проверьте правильность данных об учреждении", reply_markup=markup)
    else:
        await message.edit_text("⚠ Произошла ошибка")

async def getloginState(message: types.Message, state: FSMContext):
    await message.edit_text("👤 Введите имя пользователя")
    async with state.proxy() as data:
        data["message"] = message
    await addAccount.login.set()

async def getpasswordState(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data["message"]
    await msg.edit_text("🔑 Введите пароль")
    await state.update_data(login=str(message.text))
    await message.delete()
    await addAccount.password.set()

async def scidSelect(message: types.Message, state: FSMContext, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("loginform?cid="+str(data['cid'])+"&sid="+str(data['sid'])+"&pid="+str(data['pid'])+"&cn="+str(data['cn'])+"&sft="+str(data['sft'])+"&LASTNAME=sft")
    schools = response.json()["items"]
    if len(schools) >= 2:
        markup = types.InlineKeyboardMarkup()
        await addAccount.scid.set()
        for x in schools[:68]:
            markup.add(types.InlineKeyboardButton(x['name'][:38], callback_data=cb_account.new(action='select_scid', value=x['id'])))
        await message.edit_text("🏫 Выберите учреждение", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['scid'] = schools[0]['id']
        await schoolInfo(message, state, data['url'], data['sft'], data['scid'], user_id)

async def sftSelect(message: types.Message, state: FSMContext, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("loginform?cid="+str(data['cid'])+"&sid="+str(data['sid'])+"&pid="+str(data['pid'])+"&cn="+str(data['cn'])+"&LASTNAME=cn")
    funcs = response.json()["items"]
    if len(funcs) >= 2:
        await addAccount.sft.set()
        markup = types.InlineKeyboardMarkup()
        for x in funcs:
            markup.add(types.InlineKeyboardButton(x['name'], callback_data=cb_account.new(action='select_sft', value=x['id'])))
        await message.edit_text("🎒 Выберите тип учреждения", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['sft'] = funcs[0]['id']
        await scidSelect(message, state, user_id)

async def cnSelect(message: types.Message, state: FSMContext, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("loginform?cid="+str(data['cid'])+"&sid="+str(data['sid'])+"&pid="+str(data['pid'])+"&LASTNAME=pid")
    cities = response.json()["items"]
    if len(cities) >= 2:
        await addAccount.cn.set()
        markup = types.InlineKeyboardMarkup()
        for x in cities:
            markup.add(types.InlineKeyboardButton(x['name'], callback_data=cb_account.new(action='select_cn', value=x['id'])))
        await message.edit_text("🏙 Выберите город", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['cn'] = cities[0]['id']
        await sftSelect(message, state, user_id)

async def pidSelect(message: types.Message, state: FSMContext, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("loginform?cid="+str(data['cid'])+"&sid="+str(data['sid'])+"&LASTNAME=sid")
    provinces = response.json()["items"]
    if len(provinces) >= 2:
        await addAccount.pid.set()
        markup = types.InlineKeyboardMarkup()
        for x in provinces:
            markup.add(types.InlineKeyboardButton(x['name'], callback_data=cb_account.new(action='select_pid', value=x['id'])))
        await message.edit_text("🌆 Выберите район", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['pid'] = provinces[0]['id']
        await cnSelect(message, state, user_id)

async def sidSelect(message: types.Message, state: FSMContext, user_id):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("loginform?cid="+str(data['cid'])+"&LASTNAME=cid")
    states = response.json()["items"]
    if len(states) >= 2:
        await addAccount.sid.set()
        markup = types.InlineKeyboardMarkup()
        for x in states:
            markup.add(types.InlineKeyboardButton(x['name'], callback_data=cb_account.new(action='select_sid', value=x['id'])))
        await message.edit_text("🌇 Выберите регион", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['sid'] = states[0]['id']
        await pidSelect(message, state, user_id)

async def cidSelect(user_id: int, bemessage: types.Message, state: FSMContext):
    data = await state.get_data()
    ns = ns_sessions[user_id]
    response = await ns._client.get("prepareloginform")
    countries = response.json()["countries"]
    if len(countries) >= 2:
        await addAccount.cid.set()
        markup = types.InlineKeyboardMarkup()
        for x in countries:
            markup.add(types.InlineKeyboardButton(x['name'], callback_data=cb_account.new(action='select_cid', value=x['id'])))
        await bemessage.edit_text("🏳️ Выберите страну", reply_markup=markup)
    else:
        async with state.proxy() as data:
            data['cid'] = countries[0]['id']
        await sidSelect(bemessage, state, user_id)