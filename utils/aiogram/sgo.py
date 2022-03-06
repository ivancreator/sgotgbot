import asyncio
import sys
from functions.sgo import reStore, closeAll
async def on_startup(x):
    await reStore()

async def on_shutdown(x):
    await closeAll()
    sys.exit(0)