from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = "TOKEN"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

