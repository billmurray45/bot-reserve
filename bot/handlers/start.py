from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, Message

from bot.keyboards.main_menu import main_menu
from bot.services.pdf_generator import generate_catalog_pdf

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в KUR OFF管理!\nВыберите действие:",
        reply_markup=main_menu,
    )


@router.message(lambda m: m.text == "📄 PDF с ценами")
async def generate_pdf_with_prices(message: Message):
    msg = await message.answer("⏳ Генерирую каталог с ценами...")
    try:
        pdf_bytes = await generate_catalog_pdf(show_prices=True)
        await message.answer_document(
            BufferedInputFile(pdf_bytes, filename="kuroff-catalog.pdf"),
            caption="📄 Каталог KUR OFF (с ценами)",
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")
    finally:
        await msg.delete()


@router.message(lambda m: m.text == "📄 PDF без цен")
async def generate_pdf_no_prices(message: Message):
    msg = await message.answer("⏳ Генерирую каталог без цен...")
    try:
        pdf_bytes = await generate_catalog_pdf(show_prices=False)
        await message.answer_document(
            BufferedInputFile(pdf_bytes, filename="kuroff-catalog-no-prices.pdf"),
            caption="📄 Каталог KUR OFF (без цен)",
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")
    finally:
        await msg.delete()
