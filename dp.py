from aiogram.utils import executor
from utils.aiogram import on_startup, on_shutdown

if __name__ == "__main__":
    from handlers import dp
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)