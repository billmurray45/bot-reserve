from aiogram.fsm.state import State, StatesGroup


class CategoryForm(StatesGroup):
    waiting_name = State()
