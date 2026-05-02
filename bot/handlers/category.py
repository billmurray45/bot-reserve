from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.category_kb import (
    categories_list_kb,
    category_actions_kb,
    confirm_delete_category_kb,
)
from bot.services import api_client as api
from bot.states.category_states import CategoryForm

router = Router()


# Список категорий

async def show_categories(target: Message | CallbackQuery, edit: bool = False):
    categories = await api.get_categories()
    text = "🗂 <b>Категории</b>" if categories else "🗂 Категорий пока нет."
    kb = categories_list_kb(categories)
    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    elif isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "🗂 Категории")
async def categories_menu(message: Message):
    await show_categories(message)


@router.callback_query(F.data == "cat_list")
async def cb_cat_list(callback: CallbackQuery):
    await show_categories(callback, edit=True)
    await callback.answer()


# Просмотр категории

@router.callback_query(F.data.startswith("cat_view:"))
async def cb_cat_view(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    cat = await api.get_category(category_id)
    text = f"🗂 <b>{cat['name']}</b>"
    await callback.message.edit_text(
        text,
        reply_markup=category_actions_kb(category_id),
        parse_mode="HTML",
    )
    await callback.answer()


# Добавить категорию

@router.callback_query(F.data == "cat_add")
async def cb_cat_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryForm.waiting_name)
    await callback.message.answer("Введите название новой категории:")
    await callback.answer()


# Переименовать категорию

@router.callback_query(F.data.startswith("cat_rename:"))
async def cb_cat_rename(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.set_state(CategoryForm.waiting_name)
    await state.update_data(rename_id=category_id)
    await callback.message.answer("Введите новое название категории:")
    await callback.answer()


@router.message(CategoryForm.waiting_name)
async def process_cat_name(message: Message, state: FSMContext):
    data = await state.get_data()
    rename_id = data.get("rename_id")
    name = message.text.strip().upper()

    if rename_id:
        await api.update_category(rename_id, {"name": name})
        await state.clear()
        categories = await api.get_categories()
        await message.answer(
            f"✅ Категория переименована в <b>{name}</b>.",
            reply_markup=categories_list_kb(categories),
            parse_mode="HTML",
        )
    else:
        slug = name.lower().replace(" ", "_").replace(".", "")
        await api.create_category({"name": name, "slug": slug})
        await state.clear()
        categories = await api.get_categories()
        await message.answer(
            f"✅ Категория <b>{name}</b> добавлена.",
            reply_markup=categories_list_kb(categories),
            parse_mode="HTML",
        )


# Удалить категорию

@router.callback_query(F.data.startswith("cat_delete:"))
async def cb_cat_delete(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    cat = await api.get_category(category_id)
    await callback.message.edit_text(
        f"⚠️ Удалить категорию <b>{cat['name']}</b> и все её товары?",
        reply_markup=confirm_delete_category_kb(category_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_delete_confirm:"))
async def cb_cat_delete_confirm(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    await api.delete_category(category_id)
    categories = await api.get_categories()
    await callback.message.edit_text(
        "✅ Категория удалена.",
        reply_markup=categories_list_kb(categories),
    )
    await callback.answer()
