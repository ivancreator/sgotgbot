from bot import dp
from filters import IsOwner
from functions import admin_menu

@dp.message_handler(IsOwner(), commands="admin")
async def admin(message):
    await admin_menu(message)