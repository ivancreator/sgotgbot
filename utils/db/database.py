# import asyncio
import nest_asyncio, asyncio
import psycopg2
nest_asyncio.apply()

def run_and_get(coroutine):
    task = asyncio.create_task(coroutine)
    asyncio.get_running_loop().run_until_complete(task)
    return task.result()

class InitDb():

    def __init__(self, *args, **kwargs):
        self.conn = psycopg2.connect(host='localhost', user='user', dbname='database', password='password')
        self.cursor = self.conn.cursor()

    async def execute(self, query, vars = None):
        self.cursor.execute(query, vars)
        self.conn.commit()
        try:
            return self.cursor.fetchone()
        except:
            return None

    async def executeall(self, query, vars = None):
        self.cursor.execute(query, vars)
        self.conn.commit()
        try:
            return self.cursor.fetchall()
        except:
            return None

    async def executemany(self, query, vars_list):
        self.cursor.executemany(query, vars_list)
        self.conn.commit()
        try:
            return self.cursor.fetchmany()
        except:
            return None