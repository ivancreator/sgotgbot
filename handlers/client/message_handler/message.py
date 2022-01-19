from aiogram import types
from aiogram.types.message import ParseMode
from bot import dp
from handlers.client.callback_query.add import nsSelect
from utils.db import db, User, Account
from filters import Main, IsLink, userAdd
# from handlers.client.callback_query import add, schooltypeSelect
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
    if not user[7]:
        await message.answer('👋 Приветствую, пользователь Сетевого Города. Образование. Это бот "Сетевой Город. Объявления"\n\n⚠️ Данный бот не имеет никакого отношения к компании ИрТех и не является партнёром данной компании.\n\n👉 Данный бот создан для\n📢 Просмотра списка объявлений с возможностью\n🛎 Уведомления о новых объявлениях и прикреплённых к ним файлов\n\n🛡 Для использования данного бота потребуется вход в систему "Сетевой Город. Образование" под своей учётной записью')
        await db.execute(f"UPDATE users SET welcome_message = True WHERE telegram_id = {message.from_user.id}")
        await message.delete()
    await accountsCheck(message, state)

@dp.message_handler(commands="account_add")
async def accountaddCall(message: types.Message):
    await accountAdd(message)

@dp.message_handler(Main(), state=addAccount.wait_url)
async def userConnect(message: types.Message, state: FSMContext):
    ns = NetSchoolAPI(str(message.text))
    url = ns._url
    try:
        response = httpx.get(url, verify=False)
        if response.status_code == 200:
            data = await state.get_data()
            bemessage = data["message"]
            await message.delete()
            ns_sessions[message.from_user.id] = ns
            await addAccount.cid.set()
            await cidSelect(message.from_user.id, bemessage, state)
        else:
            await message.reply("Ошибка обработки запроса ("+str(response.status_code)+")")
    except httpx.UnsupportedProtocol:
        await message.reply("Не верная ссылка, отсутствует или введён неподдерживаемый протокол. (Поддерживаются https:// и http://)")
    except httpx.RequestError:
        await message.reply("Не удалось подключиться")
    except Exception as e:
        await message.reply("Неожиданная ошибка при выполнении запроса")
        print(f"Неожиданная ошибка при подключении {url}")

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
    await state.update_data(login=str(message.text))
    await message.delete()
    await addAccount.password.set()

async def add(message: types.Message, state: FSMContext, fail: str = None):
    data = await state.get_data()
    markup = types.InlineKeyboardMarkup()
    # markup.add(types.InlineKeyboardButton("◀️ Вернуться",
    #            callback_data=cb_account.new(action='select_sft', value=data['sft'])))
    if fail == "AuthError":
        await message.edit_text("❗️ Не верные данные, повторите попытку.\n👤 Введите имя пользователя", reply_markup=markup)
    elif fail == "UnknownError":
        await message.edit_text("❗️ Возникла неожиданная ошибка, попробуйте позже", reply_markup=markup)
        await state.reset_state(with_data=True)
    else:
        await message.edit_text("👤 Введите имя пользователя", reply_markup=markup)
    async with state.proxy() as data:
        data["message"] = message
    await addAccount.login.set()

async def checkData(message: types.Message, msg, state):
    data = await state.get_data()
    ns = ns_sessions[message.from_user.id]
    response = await ns._client.get("schools/" +
                         str(data['scid'])+"/card")
    if response.status_code == 200:
        await msg.edit_text("🕐 Проверка данных")
        school_name = str(response.json()["commonInfo"]["schoolName"])
        try:
            await ns.login(data['login'], data['password'], data['cid'], data['sid'], data['pid'], data['cn'], data['sft'], data['scid'])
            init = await ns._request_with_optional_relogin('student/diary/init')
            nickname = str(init.json()['students'][0]['nickName'])
            display_name = nickname + " ("+ school_name +")"
            account = await Account.add(message.from_user.id, data['cid'], data['sid'], data['pid'], data['cn'], data['sft'], data['scid'], data['login'], data['password'], ns._url, display_name)
            await db.execute("UPDATE accounts SET status = 'active' WHERE id = %s", [account[0]])
            await state.reset_state(with_data=True)
            account = await db.execute(f"SELECT * FROM accounts WHERE telegram_id = {message.from_user.id}")
            await selectAccount.menu.set()
            await accountMenu(msg, state, account[0])
        except errors.AuthError as e:
            await msg.edit_text("⚠ "+str(e))
        except Exception as e:
            print("Ошибка при входе в СГО: " + str(e))
            await msg.edit_text("❗️ Возникла неожиданная ошибка, попробуйте ещё раз")

@dp.message_handler(state=addAccount.password)
async def getPassword(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    await message.delete()
    await checkData(message, data["message"], state)
