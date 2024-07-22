from aiogram.enums import ParseMode
import dbhelper
import settings.config
import settings.courses
import excelhelper
import asyncio
import aiogram
import logging
from handlers.start import start_router, normalize

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = aiogram.Bot(token=settings.config.bot_token, default=aiogram.client.default.DefaultBotProperties(parse_mode=aiogram.enums.ParseMode.HTML))
dp = aiogram.Dispatcher(storage=aiogram.fsm.storage.memory.MemoryStorage())

async def processing():
    while True:
        excelhelper.report = excelhelper.Report()
        for user in dbhelper.User.get_all():
            for abitur_id in range(len(user.watching)):
                try:
                    message = f"<b>Обновление рейтинга абитуриента {normalize(user.watching[abitur_id]["user_data"])}</b>\n"
                    watching_courses = user.watching[abitur_id]["watching_courses"]
                    for course in list(user.watching[abitur_id]["watching_courses"]):
                        if user.watching[abitur_id]["user_data"] not in excelhelper.report.courses[int(course) - 1].applicants:
                            del watching_courses[course]
                            message += f"\nОтозвано заявление на «{excelhelper.report.courses[int(course) - 1].course_data.title}»"

                    for course_index in range(len(settings.courses.course_ord)):
                        if user.watching[abitur_id]["user_data"] in excelhelper.report.courses[course_index].applicants:
                            rating = excelhelper.report.courses[course_index].applicants[user.watching[abitur_id]["user_data"]].rating
                            if str(course_index + 1) not in watching_courses:
                                message += f"\nПодано заявление на «{excelhelper.report.courses[course_index].course_data.title}». Место в рейтинге: <b>{rating}</b>"
                            elif watching_courses[str(course_index + 1)] != rating:
                                message += f"\nИзменение места в рейтинге «{excelhelper.report.courses[course_index].course_data.title}». Текущая позиция: <b>{rating}</b>"
                            watching_courses[str(course_index + 1)] = rating
                    user.watching[abitur_id]["watching_courses"] = watching_courses

                    if message != f"<b>Обновление рейтинга абитуриента {normalize(user.watching[abitur_id]["user_data"])}</b>\n":
                        await bot.send_message(user.id, message, parse_mode=ParseMode.HTML)
                except:
                    pass
            user.update()

        await asyncio.sleep(settings.config.update_delay)
        pass

async def main():
    dp.include_router(start_router)
    await bot.delete_webhook(drop_pending_updates=True)
    loop = asyncio.get_event_loop()
    loop.create_task(processing())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())