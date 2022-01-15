from aiogram.types.callback_query import CallbackQuery
from bot import dp, bot
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from filters import Main, IsOwner
from functions.client import cidSelect, sidSelect, pidSelect, cnSelect, sftSelect, scidSelect, getloginState, schoolInfo
from states import addAccount
from utils.db import InitDb
from aiogram.utils.callback_data import CallbackData
from callbacks import cb_account
from functions.sgo import ns_sessions
from netschoolapi import NetSchoolAPI
import httpx, typing

@dp.callback_query_handler(Main(), cb_account.filter(action='login_select'), state='*')
async def select_login_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    await call.answer()
    await getloginState(call.message, state)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_scid'), state=addAccount.scid)
async def select_sft_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["scid"] = callback_data.get('value')
    ns = ns_sessions[call.from_user.id]
    await call.answer()
    await schoolInfo(call.message, state, ns._url, data['sft'], data['scid'], call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_sft'), state=[addAccount.sft, '*'])
async def select_sft_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["sft"] = callback_data.get('value')
    await call.answer()
    await scidSelect(call.message, state, call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_cn'), state=addAccount.cn)
async def select_cn_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["cn"] = callback_data.get('value')
    await call.answer()
    await sftSelect(call.message, state, call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_pid'), state=addAccount.pid)
async def select_pid_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["pid"] = callback_data.get('value')
    await call.answer()
    await cnSelect(call.message, state, call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_sid'), state=addAccount.sid)
async def select_sid_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["sid"] = callback_data.get('value')
    await call.answer()
    await pidSelect(call.message, state, call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='select_cid'), state=addAccount.cid)
async def select_cid_handler(call: types.CallbackQuery, callback_data: dict, state=FSMContext):
    async with state.proxy() as data:
        data["cid"] = callback_data.get('value')
    await call.answer()
    await sidSelect(call.message, state, call.from_user.id)

@dp.callback_query_handler(Main(), cb_account.filter(action='add', value=''), state=[addAccount.url, addAccount.wait_url, '*'])
async def account_add(call: types.CallbackQuery, state=FSMContext):
    await bot.answer_callback_query(call.id)
    await addAccount.url.set()
    db = InitDb()
    regions = await db.executeall("SELECT * FROM regions ORDER BY users_count DESC NULLS LAST LIMIT 3")
    if regions:
        await nsSelect(call.message)
    else:
        async with state.proxy() as data:
            data['message'] = call.message
        await call.message.edit_text("📎 Введите ссылку на ваш СГО")
        await addAccount.wait_url.set()

@dp.callback_query_handler(Main(), cb_account.filter(action='region_select'), state=['*'])
async def regionSelect(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    db = InitDb()
    region = await db.execute("SELECT url FROM regions WHERE id = %s", [callback_data['value']])
    await addAccount.cid.set()
    ns_sessions[call.from_user.id] = NetSchoolAPI(region[0])
    await cidSelect(call.from_user.id, call.message, state)
    

async def nsSelect(message: types.Message):
    db = InitDb()
    regions = await db.executeall("SELECT * FROM regions ORDER BY users_count DESC NULLS LAST LIMIT 3")
    markup = types.InlineKeyboardMarkup()
    button_loc = types.InlineKeyboardButton(
        "📍 Определить регион", callback_data=cb_account.new(action='geo', value=''))
    button_custom = types.InlineKeyboardButton(
        "✏️ Ввести свою ссылку", callback_data=cb_account.new(action='url', value=''))
    markup.row(button_loc, button_custom)
    for x in regions:
        markup.add(types.InlineKeyboardButton(
            x[1], callback_data=cb_account.new(action='region_select', value=str(x[0]))))
    text = "🏙 Выбрите город или другой метод добавления Сетевого Города. Образование"
    if message.text != text:
        await message.edit_text(text, reply_markup=markup)

@dp.callback_query_handler(Main(), cb_account.filter(action='geo', value=''), state=addAccount.url)
async def requestGeo(call: types.CallbackQuery, state=FSMContext):
    await bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(
        "📍 Оптравить местоположение", request_location=True))
    markup.add(types.KeyboardButton(
        "❌ Отмена"))
    georequest_msg = await call.message.answer("📍 Воспользуйтесь специальной кнопкой для отправки своего местоположения", reply_markup=markup)
    await call.message.delete()
    async with state.proxy() as data:
        data["message"] = georequest_msg
    await addAccount.wait_geo.set()

@dp.callback_query_handler(Main(), cb_account.filter(action='url', value=''), state=addAccount.url)
async def waitUrl(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "◀️ Вернуться к другим методам", callback_data=cb_account.new(action='add', value='')))
    async with state.proxy() as data:
        data["message"] = call.message
    await addAccount.wait_url.set()
    await call.message.edit_text("💬 Отправьте ссылку на свою систему Сетевой Город. Образование, скопировав её из адресной строки вашего браузера", reply_markup=markup)