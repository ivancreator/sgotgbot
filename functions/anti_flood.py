async def anti_flood(*args, **kwargs):
    await args[0].answer("Слишком частый запрос, попробуйте немного позже")
