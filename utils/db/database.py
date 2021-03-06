from psycopg2 import ProgrammingError, IntegrityError
import psycopg2
import psycopg2.extras
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
        self.conn.autocommit = True

    async def execute(self, query, vars = None):
        try:
            with self.conn as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
                    curs.execute(query, vars)
                    try:
                        return curs.fetchone()
                    except ProgrammingError as e:
                        if hasattr(e, 'args'):
                            if 'no results to fetch' in e.args:
                                return None
                        raise e

                    except IntegrityError as e:
                        if hasattr(e, 'pgerror'):
                            print("Ошибка выполнения запроса в базе данных: "+str(e))
                        raise e
        except Exception as e:
            raise e

    async def executeall(self, query, vars = None):
        try:
            with self.conn as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
                    curs.execute(query, vars)
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
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
                    curs.executemany(query, vars_list)
                    try:
                        return curs.fetchmany()
                    except ProgrammingError as e:
                        print(e)
                        return None
        except Exception as e:
            raise e