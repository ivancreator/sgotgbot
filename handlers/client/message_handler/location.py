from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from bot import dp, bot
from utils.db import InitDb, User
from filters import IsOwner, Main, IsLink, userAdd
from states import addAccount
from functions import cidSelect, ns_sessions
from netschoolapi import NetSchoolAPI
import httpx

@dp.message_handler(Main(), content_types=["location"], state=addAccount.wait_geo)
async def test(message: types.Message, state: FSMContext):
    db = InitDb()
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
            await nmessage.edit_text("⚠ Не удалось определить регион")
            raise e
        bemessage = await nmessage.edit_text("🕐 Загрузка данных ("+city+")")
        region = await db.execute("SELECT * FROM regions WHERE display_name = %s", [city])
        if region:
            await addAccount.cid.set()
            ns = NetSchoolAPI(region[2])
            ns_sessions[message.from_user.id] = ns
            await cidSelect(message.from_user.id, bemessage, state)
        else:
            await nmessage.edit_text("❗️ Ваш регион не поддерживается")
            await state.finish()
    else:
        await old_message.edit_text("❌ Прозошла ошибка при нахождении вашего метстоположения, попробуйте позже")
        await state.finish()