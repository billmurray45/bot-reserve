import asyncio
import logging
import signal

import uvicorn

from app.database import init_db
from bot.main import bot, dp
from bot.handlers import start, category, product

logging.basicConfig(level=logging.INFO)

dp.include_router(start.router)
dp.include_router(category.router)
dp.include_router(product.router)


async def main():
    await init_db()

    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)

    loop = asyncio.get_running_loop()

    def _shutdown():
        server.should_exit = True
        dp.stop_polling()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        return_exceptions=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
