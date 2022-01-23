import asyncio
import sys
from functions.sgo import reStore, closeAll
async def on_startup(x):
    asyncio.create_task(reStore())

async def on_shutdown(x):
    asyncio.create_task(closeAll())
    sys.exit(0)