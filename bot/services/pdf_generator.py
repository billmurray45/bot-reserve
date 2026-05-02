from playwright.async_api import async_playwright

from app.config import settings


async def generate_catalog_pdf(show_prices: bool = True) -> bytes:
    url = f"{settings.BASE_URL}/catalog"
    if not show_prices:
        url += "?show_prices=false"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        pdf = await page.pdf(
            format="A4",
            print_background=True,
        )
        await browser.close()
    return pdf
