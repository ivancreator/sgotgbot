import asyncio
from functions.sgo import checkAlerts, closeAll
async def on_startup(x):
    asyncio.create_task(checkAlerts())

async def on_shutdown(x):
    asyncio.create_task(closeAll())