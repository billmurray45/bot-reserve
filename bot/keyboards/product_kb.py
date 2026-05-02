from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 5


def products_list_kb(
    products: list[dict],
    category_id: int,
    page: int = 0,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    chunk = products[start: start + PAGE_SIZE]

    for p in chunk:
        status = "" if p["is_active"] else "🔴 "
        builder.button(
            text=f"{status}{p['title']}",
            callback_data=f"prod_view:{p['id']}",
        )

    nav = []
    if page > 0:
        nav.append(("◀️", f"prod_list:{category_id}:{page - 1}"))
    if start + PAGE_SIZE < len(products):
        nav.append(("▶️", f"prod_list:{category_id}:{page + 1}"))
    for label, cb in nav:
        builder.button(text=label, callback_data=cb)

    builder.button(text="➕ Добавить товар", callback_data=f"prod_add:{category_id}")
    builder.button(text="◀️ К категориям", callback_data="cat_list")
    builder.adjust(1)
    return builder.as_markup()


def product_actions_kb(product: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"prod_edit:{product['id']}")
    builder.button(text="💰 Цена", callback_data=f"prod_price:{product['id']}")
    builder.button(text="🖼 Фото", callback_data=f"prod_photo:{product['id']}")
    toggle = "👁 Показать" if not product["is_active"] else "🙈 Скрыть"
    builder.button(text=toggle, callback_data=f"prod_toggle:{product['id']}")
    builder.button(text="🗑 Удалить", callback_data=f"prod_delete:{product['id']}")
    builder.button(text="◀️ Назад", callback_data=f"prod_list:{product['category_id']}:0")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def confirm_delete_product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"prod_delete_confirm:{product_id}")
    builder.button(text="❌ Отмена", callback_data=f"prod_view:{product_id}")
    builder.adjust(2)
    return builder.as_markup()


def confirm_save_kb(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Сохранить", callback_data=f"{prefix}_confirm")
    builder.button(text="❌ Отмена", callback_data=f"{prefix}_cancel")
    builder.adjust(2)
    return builder.as_markup()


def categories_choose_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"prod_set_cat:{cat['id']}")
    builder.adjust(1)
    return builder.as_markup()
