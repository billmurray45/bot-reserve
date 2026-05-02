from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.product_kb import (
    categories_choose_kb,
    confirm_delete_product_kb,
    confirm_save_kb,
    product_actions_kb,
    products_list_kb,
)
from bot.services import api_client as api
from bot.states.product_states import ProductForm, ProductQuick

router = Router()


def product_summary(data: dict) -> str:
    specs = "\n".join(f"  {s['label']}: {s['value']}" for s in data.get("specs", []))
    image = data.get("icon_name") or data.get("image_filename") or "нет"
    return (
        f"<b>{data.get('title', '—')}</b>\n"
        f"{data.get('description', '—')}\n\n"
        f"Характеристики:\n{specs or '—'}\n\n"
        f"Цена: {data.get('price', '—')} ₸ {data.get('price_unit', '/ КГ')}\n"
        f"Изображение: {image}"
    )


# ── Список товаров ────────────────────────────────────────────────────────────

@router.message(F.text == "📦 Товары")
async def products_menu(message: Message):
    categories = await api.get_categories()
    if not categories:
        await message.answer("Категорий нет. Сначала создайте категорию.")
        return
    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_choose_kb(categories),
    )


@router.callback_query(F.data.startswith("prod_list:"))
async def cb_prod_list(callback: CallbackQuery):
    _, category_id, page = callback.data.split(":")
    category_id, page = int(category_id), int(page)
    products = await api.get_products(category_id=category_id)
    cat = await api.get_category(category_id)
    await callback.message.edit_text(
        f"📦 <b>{cat['name']}</b> — {len(products)} товаров",
        reply_markup=products_list_kb(products, category_id, page),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_set_cat:"))
async def cb_prod_set_cat(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    products = await api.get_products(category_id=category_id)
    cat = await api.get_category(category_id)
    await callback.message.edit_text(
        f"📦 <b>{cat['name']}</b> — {len(products)} товаров",
        reply_markup=products_list_kb(products, category_id, 0),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Просмотр товара ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_view:"))
async def cb_prod_view(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    specs = "\n".join(f"  {s['label']}: {s['value']}" for s in p["specs"])
    status = "✅ активен" if p["is_active"] else "🔴 скрыт"
    text = (
        f"<b>{p['title']}</b> [{status}]\n"
        f"{p['description']}\n\n"
        f"{specs}\n\n"
        f"💰 {p['price']} ₸ {p['price_unit']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=product_actions_kb(p),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Добавить товар (FSM) ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_add:"))
async def cb_prod_add(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(category_id=category_id, specs=[], edit_id=None)
    await state.set_state(ProductForm.waiting_title)
    await callback.message.answer("Введите название товара:")
    await callback.answer()


@router.message(ProductForm.waiting_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip().upper())
    await state.set_state(ProductForm.waiting_description)
    await message.answer("Введите описание товара:")


@router.message(ProductForm.waiting_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip().upper())
    await state.set_state(ProductForm.waiting_specs)
    await message.answer(
        "Введите характеристики. Каждая строка: <b>МЕТКА: ЗНАЧЕНИЕ</b>\n"
        "Например:\n  ВЕС: 1.6-2.2 КГ\n  УПАКОВКА: 15 КГ\n\n"
        "Когда закончите — напишите <b>готово</b>.",
        parse_mode="HTML",
    )


@router.message(ProductForm.waiting_specs)
async def process_specs(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == "готово":
        await state.set_state(ProductForm.waiting_price)
        await message.answer("Введите цену (только число):")
        return

    data = await state.get_data()
    specs = data.get("specs", [])
    for line in text.splitlines():
        if ":" in line:
            label, _, value = line.partition(":")
            specs.append({"label": label.strip().upper(), "value": value.strip().upper(), "sort_order": len(specs)})

    await state.update_data(specs=specs)
    await message.answer(f"Принято {len(specs)} характеристик. Продолжайте или напишите <b>готово</b>.", parse_mode="HTML")


@router.message(ProductForm.waiting_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите число, например: 185")
        return
    await state.update_data(price=price)
    await state.set_state(ProductForm.waiting_price_unit)
    await message.answer("Единица цены (например: / КГ, / ШТ) или <b>пропустить</b>:", parse_mode="HTML")


@router.message(ProductForm.waiting_price_unit)
async def process_price_unit(message: Message, state: FSMContext):
    text = message.text.strip()
    unit = "/ КГ" if text.lower() == "пропустить" else text.upper()
    await state.update_data(price_unit=unit)
    await state.set_state(ProductForm.waiting_image)
    await message.answer(
        "Отправьте фото товара, введите название иконки (например: <code>ph-fish</code>) "
        "или напишите <b>пропустить</b>:",
        parse_mode="HTML",
    )


@router.message(ProductForm.waiting_image, F.photo)
async def process_image_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    content = await message.bot.download_file(file.file_path)
    await state.update_data(image_bytes=content.read(), image_filename="photo.jpg", icon_name=None)
    await _show_confirm(message, state)


@router.message(ProductForm.waiting_image, F.text)
async def process_image_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == "пропустить":
        await state.update_data(icon_name=None, image_bytes=None)
    else:
        await state.update_data(icon_name=text, image_bytes=None)
    await _show_confirm(message, state)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(ProductForm.confirm)
    await message.answer(
        f"Проверьте данные:\n\n{product_summary(data)}",
        reply_markup=confirm_save_kb("prod_save"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "prod_save_confirm", ProductForm.confirm)
async def cb_prod_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    edit_id = data.get("edit_id")

    payload = {
        "category_id": data["category_id"],
        "title": data["title"],
        "description": data["description"],
        "price": data["price"],
        "price_unit": data.get("price_unit", "/ КГ"),
        "icon_name": data.get("icon_name"),
        "specs": data.get("specs", []),
    }

    if edit_id:
        product = await api.update_product(edit_id, payload)
    else:
        product = await api.create_product(payload)

    if data.get("image_bytes"):
        await api.upload_product_image(product["id"], data.get("image_filename", "photo.jpg"), data["image_bytes"])

    await state.clear()
    await callback.message.edit_text(
        f"✅ Товар <b>{product['title']}</b> {'обновлён' if edit_id else 'добавлен'}.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "prod_save_cancel", ProductForm.confirm)
async def cb_prod_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


# ── Редактировать товар ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_edit:"))
async def cb_prod_edit(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    await state.clear()
    await state.update_data(
        edit_id=product_id,
        category_id=p["category_id"],
        title=p["title"],
        description=p["description"],
        price=p["price"],
        price_unit=p["price_unit"],
        icon_name=p.get("icon_name"),
        specs=p["specs"],
        image_bytes=None,
    )
    await state.set_state(ProductForm.waiting_title)
    await callback.message.answer(f"Текущее название: <b>{p['title']}</b>\nВведите новое (или отправьте то же):", parse_mode="HTML")
    await callback.answer()


# ── Быстрая смена цены ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_price:"))
async def cb_prod_price(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    await state.set_state(ProductQuick.waiting_price)
    await state.update_data(product_id=product_id)
    await callback.message.answer(f"Текущая цена: <b>{p['price']} ₸ {p['price_unit']}</b>\nВведите новую цену:", parse_mode="HTML")
    await callback.answer()


@router.message(ProductQuick.waiting_price)
async def process_quick_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите число.")
        return
    data = await state.get_data()
    await api.update_product(data["product_id"], {"price": price})
    await state.clear()
    await message.answer(f"✅ Цена обновлена: <b>{price} ₸</b>", parse_mode="HTML")


# ── Быстрая замена фото ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_photo:"))
async def cb_prod_photo(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.set_state(ProductQuick.waiting_photo)
    await state.update_data(product_id=product_id)
    await callback.message.answer("Отправьте новое фото товара:")
    await callback.answer()


@router.message(ProductQuick.waiting_photo, F.photo)
async def process_quick_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    content = await message.bot.download_file(file.file_path)
    await api.upload_product_image(data["product_id"], "photo.jpg", content.read())
    await state.clear()
    await message.answer("✅ Фото обновлено.")


# ── Скрыть / показать ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_toggle:"))
async def cb_prod_toggle(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    updated = await api.update_product(product_id, {"is_active": not p["is_active"]})
    status = "показан" if updated["is_active"] else "скрыт"
    await callback.message.edit_text(
        f"✅ Товар <b>{updated['title']}</b> {status}.",
        reply_markup=product_actions_kb(updated),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Удалить товар ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_delete:"))
async def cb_prod_delete(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    await callback.message.edit_text(
        f"⚠️ Удалить товар <b>{p['title']}</b>?",
        reply_markup=confirm_delete_product_kb(product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_delete_confirm:"))
async def cb_prod_delete_confirm(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    p = await api.get_product(product_id)
    category_id = p["category_id"]
    await api.delete_product(product_id)
    products = await api.get_products(category_id=category_id)
    cat = await api.get_category(category_id)
    await callback.message.edit_text(
        f"✅ Товар удалён.\n\n📦 <b>{cat['name']}</b> — {len(products)} товаров",
        reply_markup=products_list_kb(products, category_id, 0),
        parse_mode="HTML",
    )
    await callback.answer()
