from psycopg2 import ProgrammingError, IntegrityError
import psycopg2
from config import DB_CONFIG

# def run_and_get(coroutine):
#     import nest_asyncio, asyncio
#     nest_asyncio.apply()
#     task = asyncio.create_task(coroutine)
#     asyncio.get_running_loop().run_until_complete(task)
#     return task.result()

class InitDb():

    def __init__(self, *args, **kwargs):
        self.conn = psycopg2.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], dbname=DB_CONFIG['db'], password=DB_CONFIG['password'])
        self.cursor = self.conn.cursor()

    async def execute(self, query, vars = None):
        try:
            with self.conn as conn:
                with conn.cursor() as curs:
                    try:
                        curs.execute(query, vars)
                        conn.commit()
                        return curs.fetchone()
                    except ProgrammingError as e:
                        return None
                    except IntegrityError as e:
                        if hasattr(e, 'pgerror'):
                            print("Ошибка выполнения запроса в базе данных: "+str(e))
        except Exception as e:
            raise e

    async def executeall(self, query, vars = None):
        try:
            with self.conn as conn:
                with conn.cursor() as curs:
                    curs.execute(query, vars)
                    conn.commit()
                    try:
                        return curs.fetchall()
                    except ProgrammingError as e:
                        print(e)
                        return None
        except Exception as e:
            raise e

    async def executemany(self, query, vars_list):
        try:
            with self.conn as conn:
                with conn.cursor() as curs:
                    curs.executemany(query, vars_list)
                    conn.commit()
                    try:
                        return curs.fetchmany()
                    except ProgrammingError as e:
                        print(e)
                        return None
        except Exception as e:
            raise e