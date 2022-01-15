from data import InitData, Update
import asyncio

asyncio.run(InitData().dataSetup())
asyncio.run(Update().regionsUpdate())
