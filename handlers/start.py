from aiogram import Router, types, F, Bot
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
import re
import dbhelper
import excelhelper

start_router = Router()


def check_snils(data: str):
    return re.fullmatch(r"^\d{3}-\d{3}-\d{3} \d{2}$", data)


def check_id(data: str):
    return re.fullmatch(r"^\d{2}-\d{9}$", data)


def normalize(data: str):
    if len(data) != 11:
        return data
    if data.startswith("00"):
        return f'{data[0:2]}-{data[2:]}'
    return f'{data[0:3]}-{data[3:6]}-{data[6:9]} {data[9:11]}'


def get_abiturs_ik(user: dbhelper.User):
    ind = 0
    ik = [[types.InlineKeyboardButton(text="Добавить по СНИЛС/ID", callback_data=f'add_watching')]]
    for abitur in user.watching:
        ik.append([types.InlineKeyboardButton(
            text=normalize(abitur.user_data if isinstance(abitur, dbhelper.WatchingUser) else abitur["user_data"]),
            callback_data=f'watch_{ind}')])
        ind += 1
    ik.append([types.InlineKeyboardButton(text="Назад", callback_data=f'back_menu')])
    return ik


def get_courses_ik(user: dbhelper.User, abitur_id: int):
    ik = [[types.InlineKeyboardButton(text="Перестать отслеживать", callback_data=f'del_{abitur_id}')]]
    for course in user.watching[abitur_id]["watching_courses"]:
        ik.append([types.InlineKeyboardButton(
            text=excelhelper.report.courses[int(course) - 1].course_data.title,
            callback_data=f'more_course_{abitur_id}_{course}')])
    ik.append([types.InlineKeyboardButton(text="Назад", callback_data=f'back_watching')])
    return ik


def generate_message(watching_user: dict):
    message = f'СНИЛС/ID: <b>{normalize(watching_user["user_data"])}</b>\nОбновлено: {excelhelper.report.update_time:%d.%m.%Y %H:%M:%S%z}'
    for s_course_id in watching_user["watching_courses"]:
        course_id = int(s_course_id) - 1
        message += f"\n\n<b>{excelhelper.report.courses[course_id].course_data.code} {excelhelper.report.courses[course_id].course_data.title}</b>"
        message += f"\nМесто в рейтинге: {watching_user["watching_courses"][s_course_id]}"

    return message


def place_to_str(place_id: str):
    if place_id == 0b10:
        return "Бюджет"
    if place_id == 0b01:
        return "Квазибюджет"
    return "Бюджет/квазибюджет"


def generate_course_message(watching_user: dict, course_table: excelhelper.CourseTable):
    message = f"<b>{course_table.course_data.code} {course_table.course_data.title}</b>"
    message += f"\n\nСтатистика поданных заявлений"
    message += f"\nБюджет: <b>{course_table.places_got.budget}/{course_table.places_all.budget}</b>"
    message += f"\nАбитуриенты с БВИ: <b>{course_table.places_bvi}</b>"
    message += f"\nСпециальная квота: <b>{course_table.places_got.special}/{course_table.places_all.special}</b>"
    message += f"\nОтдельная квота: <b>{course_table.places_got.separate}/{course_table.places_all.separate}</b>"
    message += f"\nБВИ в рамках отдельной квоты: <b>{course_table.places_separate_bvi}</b>"
    message += f"\nЦелевое обучение: <b>{course_table.places_got.target}/{course_table.places_all.target}</b>"
    message += f"\nПлатное обучение: <b>{course_table.places_got.paid}/{course_table.places_all.paid}</b>"
    message += f"\n\nИнформация об абитуриенте"
    message += f"\nМесто в рейтинге: <b>{course_table.applicants[watching_user["user_data"]].rating}</b>"
    message += f"\nЛьгота БВИ: <b>{'Да' if course_table.applicants[watching_user["user_data"]].BVI else 'Нет'}</b>"
    if course_table.applicants[watching_user["user_data"]].BVI:
        message += f" ({course_table.applicants[watching_user["user_data"]].olymp_name})"
    message += f"\nОсобое право: <b>{'Да' if course_table.applicants[watching_user["user_data"]].special_quota else 'Нет'}</b>"
    message += f"\nОтдельная квота: <b>{'Да' if course_table.applicants[watching_user["user_data"]].separate_quota else 'Нет'}</b>"
    message += f"\nЦелевое обучение: <b>{'Да' if course_table.applicants[watching_user["user_data"]].target_quota else 'Нет'}</b>"
    message += f"\nПриоритет: <b>{course_table.applicants[watching_user["user_data"]].other_prior}</b>"
    message += f"\nБаллов за ИД: <b>{course_table.applicants[watching_user["user_data"]].additional_result}</b>"
    message += f"\nСумма баллов: <b>{course_table.applicants[watching_user["user_data"]].sum_result}</b>"
    message += f"\nОригинал аттестата: <b>{'Да' if course_table.applicants[watching_user["user_data"]].given_docs else 'Нет'}</b>"
    message += f"\nТребуется общежитие: <b>{'Да' if course_table.applicants[watching_user["user_data"]].dormitory else 'Нет'}</b>"
    message += f"\nВид места: <b>{place_to_str(course_table.applicants[watching_user["user_data"]].place_type)}</b>"
    return message


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type != 'private':
        return
    user = dbhelper.User(id=message.from_user.id)
    user.state = 0
    user.update()

    ik = [[types.InlineKeyboardButton(text=f'Отслеживаемые абитуриенты', callback_data=f'get_watching')],
          [types.InlineKeyboardButton(text=f'Разработчик', url='https://t.me/Irval1337/')]]
    await message.answer("Главное меню", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik))


@start_router.callback_query(F.data == "back_watching")
@start_router.callback_query(F.data == "get_watching")
async def get_watching_query(callback: CallbackQuery):
    user = dbhelper.User(id=callback.from_user.id)

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=get_abiturs_ik(user))
    )


@start_router.callback_query(F.data == "back_menu")
async def back_menu_query(callback: CallbackQuery):
    ik = [[types.InlineKeyboardButton(text=f'Отслеживаемые абитуриенты', callback_data=f'get_watching')],
          [types.InlineKeyboardButton(text=f'Разработчик', url='https://t.me/Irval1337/')]]
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik)
    )


@start_router.callback_query(F.data == "add_watching")
async def add_watching_query(callback: CallbackQuery):
    user = dbhelper.User(id=callback.from_user.id)
    user.state = 1
    user.update()
    ik = [[types.InlineKeyboardButton(text=f'Отмена', callback_data=f'back_add_watching')]]

    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Отправьте боту СНИЛС абитуриента или его уникальный идентификационный номер",
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik))


@start_router.callback_query(F.data == "back_add_watching")
async def back_add_watching_query(callback: CallbackQuery):
    user = dbhelper.User(id=callback.from_user.id)
    user.state = 0
    user.update()
    ik = [[types.InlineKeyboardButton(text=f'Отслеживаемые абитуриенты', callback_data=f'get_watching')],
          [types.InlineKeyboardButton(text=f'Разработчик', url='https://t.me/Irval1337/')]]
    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Меню бота:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik))


@start_router.message()
async def message_handler(message: types.Message):
    user = dbhelper.User(id=message.from_user.id)
    if user.state == 0:
        await message.bot.send_message(message.chat.id, 'Упс, бот не может обработать ваш запрос')
        return
    if (not check_snils(message.text)) and (not check_id(message.text)):
        ik = [[types.InlineKeyboardButton(text=f'Отмена', callback_data=f'back_add_watching')]]
        await message.bot.send_message(message.chat.id, 'Формат сообщения не распознан. Пожалуйста, убедитесь в правильности указания данных:\n\nСНИЛС: XXX-XXX-XXX XX\nУникальный номер: XX-XXXXXXXXX',
                                       reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik))
        return
    user.watching.append(dbhelper.WatchingUser(message.text))
    user.state = 0
    user.update()
    await message.bot.send_message(message.chat.id, 'Абитуриент успешно добавлен',
                                   reply_markup=types.InlineKeyboardMarkup(inline_keyboard=get_abiturs_ik(user)))


@start_router.callback_query(F.data.startswith("watch_"))
async def watch_query(callback: CallbackQuery):
    abitur_id = int(callback.data[len("watch_"):])
    user = dbhelper.User(id=callback.from_user.id)

    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(generate_message(user.watching[abitur_id]),
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=get_courses_ik(user, abitur_id)),
                                  parse_mode=ParseMode.HTML)


@start_router.callback_query(F.data.startswith("more_course_"))
async def more_course_query(callback: CallbackQuery):
    data = callback.data[len("more_course_"):]
    abitur_id, course_id = map(int, data.split('_'))
    user = dbhelper.User(id=callback.from_user.id)

    ik = [[types.InlineKeyboardButton(text=f'Назад', callback_data=f'watch_{abitur_id}')]]
    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(generate_course_message(user.watching[abitur_id], excelhelper.report.courses[course_id - 1]),
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=ik),
                                  parse_mode=ParseMode.HTML)


@start_router.callback_query(F.data.startswith("del_"))
async def del_query(callback: CallbackQuery):
    abitur_id = int(callback.data[len("del_"):])
    user = dbhelper.User(id=callback.from_user.id)
    del user.watching[abitur_id]
    user.update()

    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer("Абитуриент успешно удален",
                                  reply_markup=types.InlineKeyboardMarkup(inline_keyboard=get_abiturs_ik(user)))
