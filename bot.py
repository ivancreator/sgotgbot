from config import API
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = API['token']

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

