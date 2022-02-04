from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from bot import dp, bot
from utils.db import db, User
from filters import IsOwner, Main, userAdd
from states import addAccount
from functions import cidSelect, ns_sessions
from netschoolapi import NetSchoolAPI
import httpx

from utils.db.data import Account

@dp.message_handler(Main(), content_types=["location"], state=addAccount.wait_geo)
async def test(message: types.Message, state: FSMContext):
    nmessage = await bot.send_message(message.chat.id, "🕐 Немного подождите")
    data = await state.get_data()
    old_message = data["message"]
    await old_message.delete()
    await message.delete()
    response = httpx.get("https://nominatim.openstreetmap.org/reverse?format=json&lat="+str(
        message.location.latitude)+"&lon="+str(message.location.longitude))
    if response.status_code == 200:
        result = response.json()
        try:
            city = result["address"]["city"]
        except KeyError as e:
            await nmessage.edit_text("❗️ Не удалось определить регион")
        except Exception as e:
            print("Неожиданная ошибка при определении региона пользователя")
            raise e
        await nmessage.edit_text("🕐 Загрузка данных ("+city+")")
        region = await db.execute("SELECT * FROM regions WHERE display_name = %s", [city])
        if region:
            account_id = await Account.add(message.from_user.id, region[0])
            await addAccount.cid.set()
            ns_sessions[account_id] = NetSchoolAPI(region[0])
            await cidSelect(account_id, nmessage)
        else:
            await nmessage.edit_text("⚠ Вашего региона нет в базе данных\n📎 Введите ссылку на СГО")
            await addAccount.wait_url.set()
    else:
        await nmessage.edit_text("❌ Прозошла ошибка при нахождении вашего метстоположения, попробуйте позже")
        await state.finish()