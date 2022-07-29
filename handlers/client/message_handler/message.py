from aiogram import types
from aiogram.types.message import ParseMode
from bot import dp
from functions.sgo import accountLogin
from handlers.client.callback_query.add import nsSelect
from utils.db import db, User, Account
from filters import Main, userAdd
from aiogram.dispatcher.storage import FSMContext
from states import addAccount, selectAccount
from netschoolapi import NetSchoolAPI, errors
from callbacks import cb_account
from functions import cidSelect, getAnnouncements, accountsCheck, accountAdd, accountMenu, ns_sessions
import httpx

@dp.message_handler(Main(), commands="start", state="*")
async def start(message: types.Message, state: FSMContext):
    user = await User.data(message.from_user.id)
    if not user:
        await userAdd(message)
        user = await User.data(message.from_user.id)
    if not user['welcome_message']:
        await message.answer('👋 Приветствую, пользователь Сетевого Города. Образование. Это бот "Сетевой Город. Объявления"\n\n⚠️ Данный бот не имеет никакого отношения к компании ИрТех и не является партнёром данной компании.\n\n👉 Данный бот создан для\n📢 Просмотра списка объявлений с возможностью\n🛎 Уведомления о новых объявлениях и прикреплённых к ним файлов\n\n🛡 Для использования данного бота потребуется вход в систему "Сетевой Город. Образование" под своей учётной записью')
        await db.execute(f"UPDATE users SET welcome_message = True WHERE telegram_id = {message.from_user.id}")
        await message.delete()
    await accountsCheck(message, state)

@dp.message_handler(commands="account_add")
async def accountaddCall(message: types.Message):
    await accountAdd(message)

@dp.message_handler(Main(), state=addAccount.wait_url)
async def userConnect(message: types.Message, state: FSMContext):
    raw_url = message.text
    url = raw_url
    try:
        ns = NetSchoolAPI(str(raw_url))
        url = ns._url
        response = await ns._client.get(url)
        if response.status_code == 200:
            data = await state.get_data()
            bemessage = data["message"]
            account = await Account.get_registerAccount(message.from_user.id)
            if account:
                await Account.update(account['id'], **{'url': url})
            else:
                account = await Account.add(message.from_user.id, url)
            account_id = account['id']
            ns_sessions[account_id] = ns
            await addAccount.cid.set()
            await message.delete()
            await cidSelect(account_id, bemessage)
        else:
            await message.reply("Ошибка обработки запроса ("+str(response.status_code)+")")
    except httpx.UnsupportedProtocol:
        await message.reply("Не верная ссылка, отсутствует или введён неподдерживаемый протокол. (Поддерживаются https:// и http://)")
    except httpx.RequestError:
        await message.reply("Не удалось подключиться")
    except Exception as e:
        await message.reply("Неожиданная ошибка при выполнении запроса")
        print(f"Неожиданная ошибка при подключении по ссылке {url}")
        raise e

@dp.message_handler(Main(), text='❌ Отмена', state=addAccount.wait_geo)
async def cancelGeo(message: types.Message, state: FSMContext):
    await message.delete()
    msg = await message.answer("🕐 Немного подождите")
    data = await state.get_data()
    await data['message'].delete()
    await nsSelect(msg)
    await addAccount.url.set()

@dp.message_handler(state=addAccount.login)
async def getLogin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data["message"]
    await msg.edit_text("🔑 Введите пароль")
    account = await Account.get_registerAccount(message.from_user.id)
    ns = ns_sessions[account['id']]
    ns._prelogin_data['username'] = message.text
    await Account.update(account['id'], **ns._prelogin_data)
    await message.delete()
    await addAccount.password.set()

async def checkData(message: types.Message, msg: types.Message, state):
    account = await Account.get_registerAccount(message.from_user.id)
    account_id = account['id']
    ns = ns_sessions[account_id]
    data = ns._prelogin_data
    response = await ns._client.get("schools/" +
                         str(data['scid'])+"/card")
    if response.status_code == 200:
        await msg.edit_text("🕐 Проверка данных")
        school_name = str(response.json()["commonInfo"]["schoolName"])
        try:
            ns = await accountLogin(account_id)
            student = ns._student
            nickname = str(student['nickName'])
            default_display_name = nickname + " ("+ school_name +")"
            data = {
                **data,
                'status': 'active',
                'nickname': nickname,
                'school_name': school_name,
                'display_name': default_display_name,
                'chat_id': message.chat.id
            }
            await Account.update(account_id, **data)
            await accountMenu(message, state)
            await msg.delete()
        except errors.AuthError as e:
            await addAccount.scid.set()
            markup = types.InlineKeyboardMarkup()
            ns._prelogin_data['password'] = None
            await Account.update(account_id, **ns._prelogin_data)
            markup.add(types.InlineKeyboardButton("🔏 Изменить данные", callback_data=cb_account.new(action='select_scid', value=data['scid'])))
            await msg.edit_text("⚠ "+str(e), reply_markup=markup)
        except Exception as e:
            await state.reset_state(with_data=True)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🏠 Вернуться в начало", callback_data=cb_account.new(action='list', value='')))
            print("Ошибка при входе в СГО: " + str(e))
            await msg.edit_text("❗️ Возникла неожиданная ошибка, попробуйте ещё раз", reply_markup=markup)
            raise e

@dp.message_handler(state=addAccount.password)
async def getPassword(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    account = await Account.get_registerAccount(message.from_user.id)
    ns = ns_sessions[account['id']]
    ns._prelogin_data['password'] = message.text
    await Account.update(account['id'], **ns._prelogin_data)
    await message.delete()
    await checkData(message, data["message"], state)
