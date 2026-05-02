from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_list_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=f"cat_view:{cat['id']}",
        )
    builder.button(text="➕ Добавить категорию", callback_data="cat_add")
    builder.adjust(1)
    return builder.as_markup()


def category_actions_kb(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Переименовать", callback_data=f"cat_rename:{category_id}")
    builder.button(text="🗑 Удалить", callback_data=f"cat_delete:{category_id}")
    builder.button(text="◀️ Назад", callback_data="cat_list")
    builder.adjust(2, 1)
    return builder.as_markup()


def confirm_delete_category_kb(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"cat_delete_confirm:{category_id}")
    builder.button(text="❌ Отмена", callback_data=f"cat_view:{category_id}")
    builder.adjust(2)
    return builder.as_markup()
