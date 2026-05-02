from aiogram.fsm.state import State, StatesGroup


class ProductForm(StatesGroup):
    waiting_category = State()
    waiting_title = State()
    waiting_description = State()
    waiting_specs = State()
    waiting_price = State()
    waiting_price_unit = State()
    waiting_image = State()
    confirm = State()


class ProductQuick(StatesGroup):
    waiting_price = State()   # быстрое изменение цены
    waiting_photo = State()   # быстрая замена фото
