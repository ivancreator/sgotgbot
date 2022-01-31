from aiogram.dispatcher.filters.state import State, StatesGroup


class addAccount(StatesGroup):
    url = State()
    wait_url = State()
    wait_geo = State()
    cid = State()
    sid = State()
    pid = State()
    cn = State()
    sft = State()
    scid = State()
    confirm = State()
    login = State()
    password = State()

class selectAccount(StatesGroup):
    select = State()
    menu = State()
    settings = State()
    announcements = State()
    remove = State()
