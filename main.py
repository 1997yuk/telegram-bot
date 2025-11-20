# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import sqlite3
import io
import csv

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 🔐 ТОКЕН ТВОЕГО БОТА
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ (по username без @) =====
ADMIN_USERNAMES = {"yusubovk", "DSharafeev_TVD"}  # добавляешь ники через запятую


def is_admin(user: types.User) -> bool:
    return bool(user.username and user.username.lower() in ADMIN_USERNAMES)


# ===== СПИСОК МАРКЕТОВ ЧЕРЕЗ МНОГОСТРОЧНУЮ СТРОКУ =====
MARKETS_TEXT = """
Маркет B-01
Маркет B-02
Маркет B-03
Маркет B-04
Маркет B-05
Маркет B-06
Маркет B-07
Маркет B-08
Маркет B-09
Маркет D-01
Маркет D-02
Маркет D-03
Маркет D-04
Маркет D-05
Маркет D-06
Маркет D-07
Маркет D-08
Маркет D-09
Маркет D-10
Маркет D-12
Маркет D-14
Маркет D-16
Маркет D-18
Маркет Dz-01
Маркет Dz-02
Маркет Dz-03
Маркет K-01
Маркет K-02
Маркет K-03
Маркет K-04
Маркет K-05
Маркет K-06
Маркет K-07
Маркет А-01
Маркет А-02
Маркет А-03
Маркет А-04
Маркет А-05
Маркет А-06
Маркет А-07
Маркет А-08
Маркет А-09
Маркет А-10
Маркет А-11
Маркет А-12
Маркет А-13
Маркет А-14
Маркет А-15
Маркет А-16
Маркет А-17
Маркет А-18
Маркет А-19
Маркет А-20
Маркет А-21
Маркет А-22
Маркет А-23
Маркет А-24
Маркет А-25
Маркет А-27
Маркет А-28
Маркет А-29
Маркет А-30
Маркет А-31
Маркет А-32
Маркет А-34
Маркет А-35
Маркет М-02
Маркет М-03
Маркет М-04
Маркет М-05
Маркет М-06
Маркет М-07
Маркет М-08
Маркет М-101
Маркет М-102
Маркет М-103
Маркет М-104
Маркет М-105
Маркет М-106
Маркет М-107
Маркет М-108
Маркет М-109
Маркет М-11
Маркет М-110
Маркет М-111
Маркет М-112
Маркет М-113
Маркет М-114
Маркет М-115
Маркет М-116
Маркет М-117
Маркет М-118
Маркет М-119
Маркет М-12
Маркет М-120
Маркет М-121
Маркет М-122
Маркет М-123
Маркет М-124
Маркет М-125
Маркет М-126
Маркет М-127
Маркет М-128
Маркет М-129
Маркет М-13
Маркет М-130
Маркет М-131
Маркет М-132
Маркет М-133
Маркет М-134
Маркет М-135
Маркет М-137
Маркет М-139
Маркет М-14
Маркет М-140
Маркет М-141
Маркет М-142
Маркет М-143
Маркет М-144
Маркет М-145
Маркет М-146
Маркет М-147
Маркет М-148
Маркет М-149
Маркет М-151
Маркет М-156
Маркет М-16
Маркет М-161
Маркет М-164
Маркет М-18
Маркет М-19
Маркет М-20
Маркет М-21
Маркет М-22
Маркет М-23
Маркет М-25
Маркет М-26
Маркет М-27
Маркет М-28
Маркет М-30
Маркет М-31
Маркет М-32
Маркет М-33
Маркет М-34
Маркет М-35
Маркет М-36
Маркет М-37
Маркет М-40
Маркет М-41
Маркет М-42
Маркет М-43
Маркет М-44
Маркет М-45
Маркет М-46
Маркет М-47
Маркет М-48
Маркет М-49
Маркет М-50
Маркет М-51
Маркет М-53
Маркет М-55
Маркет М-56
Маркет М-57
Маркет М-58
Маркет М-59
Маркет М-60
Маркет М-61
Маркет М-62
Маркет М-63
Маркет М-64
Маркет М-65
Маркет М-66
Маркет М-67
Маркет М-68
Маркет М-69
Маркет М-70
Маркет М-71
Маркет М-72
Маркет М-73
Маркет М-74
Маркет М-75
Маркет М-76
Маркет М-78
Маркет М-79
Маркет М-80
Маркет М-81
Маркет М-82
Маркет М-83
Маркет М-84
Маркет М-85
Маркет М-86
Маркет М-87
Маркет М-88
Маркет М-89
Маркет М-90
Маркет М-91
Маркет М-92
Маркет М-93
Маркет М-95
Маркет М-96
Маркет М-97
Маркет М-98
Маркет М-99
Маркет С-01
Маркет С-03
Маркет С-04
Маркет С-05
Маркет С-06
Маркет С-07
Маркет С-08
Маркет С-09
Маркет С-10
Маркет С-11
Маркет С-12
Маркет С-13
Маркет С-14
Маркет С-15
Маркет С-16Т
Маркет С-17
Маркет С-18
Маркет С-19
Маркет С-20
Маркет С-21
Маркет С-22
Маркет С-27
Маркет М-153
Маркет D-17
Маркет D-15
Маркет С-23
Маркет А-37
Маркет S-01
Маркет S-03
Маркет S-06
Маркет S-09
Маркет С-25
Маркет Dz-04
"""

MARKETS = [line.strip() for line in MARKETS_TEXT.splitlines() if line.strip()]

# ===== ГРУППИРОВКА МАРКЕТОВ ПО БУКВЕ/КОДУ =====
from collections import defaultdict

MARKET_GROUPS = defaultdict(list)
for m in MARKETS:
    code = m.replace("Маркет", "").strip()  # "B-01", "Dz-01", "А-01"
    prefix = code.split('-')[0].strip()     # "B", "Dz", "А"
    MARKET_GROUPS[prefix].append(m)

MARKET_GROUP_CODES = sorted(MARKET_GROUPS.keys())

# ===== БАЗА ДАННЫХ =====

DB_PATH = "reports.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        market TEXT,
        bread TEXT,
        lepeshki TEXT,
        patyr TEXT,
        assortment TEXT,
        raw_text TEXT,
        photo_file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()
logging.info("База данных и таблица reports готовы")


def save_report(user: types.User, market: str, photo_file_id: str,
                bread: str, lepeshki: str, patyr: str, assortment: str,
                raw_text: str):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reports
        (user_id, username, full_name, market,
         bread, lepeshki, patyr, assortment,
         raw_text, photo_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.full_name,
            market,
            bread,
            lepeshki,
            patyr,
            assortment,
            raw_text,
            photo_file_id,
        ),
    )
    conn.commit()
    logging.info(f"Сохранён отчёт: {market}, user_id={user.id}")


# ===== СОСТОЯНИЕ ПО ПОЛЬЗОВАТЕЛЮ =====
# user_id -> dict(step, chat_id, photo_file_id, market_group, market, ostatki, bread, lepeshki, patyr, assortment)
user_states = {}


# ===== ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ =====

def kb_market_groups():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    row = []
    for code in MARKET_GROUP_CODES:
        row.append(KeyboardButton(code))
        if len(row) == 4:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    return kb


def kb_markets_for_group(group_code: str):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for m in MARKET_GROUPS[group_code]:
        kb.add(KeyboardButton(m))
    return kb


def kb_ostatki():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("корректные"), KeyboardButton("некорректные"))
    return kb


def kb_level():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("мало"), KeyboardButton("норм"), KeyboardButton("много"))
    return kb


# ===== КОМАНДЫ =====

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = (
        "Привет! Я бот для фото-отчётов по магазинам.\n\n"
        "Как работать:\n"
        "1️⃣ Отправьте <b>фото</b> в группу или в личку боту.\n"
        "2️⃣ После фото я спрошу:\n"
        "   • Группу маркета (букву)\n"
        "   • Конкретный маркет из списка\n"
        "   • Остатки: корректные / некорректные\n"
        "   • Хлеб: мало / норм / много\n"
        "   • Лепешки: мало / норм / много\n"
        "   • Патыр: мало / норм / много\n"
        "   • Ассортимент: мало / норм / много\n"
        "3️⃣ В конце я отправлю итоговый отчёт с фото и сохраню его в базе.\n\n"
        "Команды (в личке или в группе):\n"
        "/status – кто уже отправил отчёт за сегодня\n"
        "/reset  – удалить отчёты за сегодня (админ)\n"
        "/export – выгрузить все отчёты в CSV (админ)\n"
        "/photos_today – фото отчётов за сегодня (админ)\n"
        "   • /photos_today – все маркеты\n"
        "   • /photos_today Маркет М-11 – только один маркет"
    )
    await message.reply(text)


@dp.message_handler(commands=["reset"])
async def cmd_reset(message: types.Message):
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        """
    )
    conn.commit()
    await message.answer("Все отчёты за сегодня удалены. Можно собирать заново.")


@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT market
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        """
    )
    rows = cur.fetchall()
    reported = {r[0] for r in rows}

    done = []
    not_done = []

    for m in MARKETS:
        if m in reported:
            done.append(f"✅ {m}")
        else:
            not_done.append(f"❌ {m}")

    text = "Статус отчётов на сегодня (UTC+5):\n\n"
    if done:
        text += "Отправили отчёт:\n" + "\n".join(done) + "\n\n"
    else:
        text += "Пока никто не отправил отчёт.\n\n"

    if not_done:
        text += "Ещё НЕ отправили:\n" + "\n".join(not_done)

    await message.answer(text)


@dp.message_handler(commands=["export"])
async def cmd_export(message: types.Message):
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            datetime(created_at, '+5 hours') AS created_at_uz,
            market,
            bread,
            lepeshki,
            patyr,
            assortment,
            user_id,
            username,
            full_name
        FROM reports
        ORDER BY datetime(created_at) ASC
        """
    )
    rows = cur.fetchall()
    if not rows:
        await message.reply("В базе пока нет отчётов.")
        return

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        "id", "created_at", "market",
        "Буханку", "лепешки", "патир", "ассортимент",
        "user_id", "username", "full_name",
    ])
    for r in rows:
        writer.writerow(r)

    data = output.getvalue().encode("utf-8-sig")
    buf = io.BytesIO(data)
    buf.name = "reports.csv"

    await message.reply_document(buf, caption="Выгрузка всех отчётов из базы.")


@dp.message_handler(commands=["photos_today"])
async def cmd_photos_today(message: types.Message):
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    args = message.get_args().strip()
    market_filter = None

    if args:
        if args.lower() in ("все", "all"):
            market_filter = None
        else:
            if args not in MARKETS:
                await message.reply(
                    "Не нашёл такой магазин.\n"
                    "Напишите точно как в списке, например:\n"
                    "<code>/photos_today Маркет М-11</code>\n"
                    "или\n"
                    "<code>/photos_today все</code>",
                )
                return
            market_filter = args

    cur = conn.cursor()
    base_sql = """
        SELECT
            market,
            photo_file_id,
            datetime(created_at, '+5 hours') AS created_at_uz
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
          AND photo_file_id IS NOT NULL
    """
    params = []
    if market_filter:
        base_sql += " AND market = ?"
        params.append(market_filter)

    base_sql += " ORDER BY datetime(created_at) ASC"

    cur.execute(base_sql, params)
    rows = cur.fetchall()

    if not rows:
        if market_filter:
            await message.reply(f"За сегодня нет фото-отчётов по {market_filter}.")
        else:
            await message.reply("За сегодня ещё нет фото-отчётов.")
        return

    if market_filter:
        await message.reply(
            f"Фото-отчёты за сегодня по {market_filter}: {len(rows)} шт."
        )
    else:
        await message.reply(
            f"Фото-отчёты за сегодня по всем маркетам: {len(rows)} шт."
        )

    for market, file_id, created_at_uz in rows:
        caption = f"{market}\n{created_at_uz}"
        try:
            await message.reply_photo(file_id, caption=caption)
        except Exception as e:
            logging.error(f"Ошибка отправки фото: {e}")


# ===== ОСНОВНОЙ ПРОЦЕСС: ФОТО + ОПРОС В ТГ =====

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """
    Магазин присылает фото (в группу или в личку).
    Запускаем диалог по шагам.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    photo = message.photo[-1]
    file_id = photo.file_id

    logging.info(f"[PHOTO] user_id={user_id}, chat_id={chat_id}, file_id={file_id}")

    user_states[user_id] = {
        "step": "market_group",
        "chat_id": chat_id,
        "photo_file_id": file_id,
        "market_group": None,
        "market": None,
        "ostatki": None,
        "bread": None,
        "lepeshki": None,
        "patyr": None,
        "assortment": None,
    }

    await message.reply(
        "Фото получено ✅\n"
        "Сначала выберите группу маркета (букву):",
        reply_markup=kb_market_groups()
    )


@dp.message_handler(lambda m: m.text is not None and m.from_user.id in user_states)
async def handle_steps(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states[user_id]
    step = state["step"]
    chat_id = state["chat_id"]

    # ===== ВЫБОР ГРУППЫ МАРКЕТА =====
    if step == "market_group":
        if text not in MARKET_GROUPS:
            await message.reply(
                "Выберите группу маркета из списка ниже:",
                reply_markup=kb_market_groups()
            )
            return
        state["market_group"] = text
        state["step"] = "market"
        await message.reply(
            f"Группа <b>{text}</b> выбрана.\n"
            f"Теперь выберите конкретный маркет:",
            reply_markup=kb_markets_for_group(text)
        )
        return

    # ===== ВЫБОР КОНКРЕТНОГО МАРКЕТА =====
    if step == "market":
        valid_markets = MARKET_GROUPS.get(state["market_group"], [])
        if text not in valid_markets:
            await message.reply(
                "Выберите маркет из списка кнопок ниже.",
                reply_markup=kb_markets_for_group(state["market_group"])
            )
            return
        state["market"] = text
        state["step"] = "ostatki"
        await message.reply(
            "Остатки: выберите <b>корректные</b> или <b>некорректные</b>.",
            reply_markup=kb_ostatki()
        )
        return

    # ===== ОСТАТКИ =====
    if step == "ostatki":
        if text not in ["корректные", "некорректные"]:
            await message.reply(
                "Выберите один из вариантов: <b>корректные</b> / <b>некорректные</b>.",
                reply_markup=kb_ostatki()
            )
            return
        state["ostatki"] = text
        state["step"] = "bread"
        await message.reply(
            "Хлеб: <b>мало</b> / <b>норм</b> / <b>много</b>",
            reply_markup=kb_level()
        )
        return

    # ===== ХЛЕБ =====
    if step == "bread":
        if text not in ["мало", "норм", "много"]:
            await message.reply(
                "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>",
                reply_markup=kb_level()
            )
            return
        state["bread"] = text
        state["step"] = "lepeshki"
        await message.reply(
            "Лепешки: <b>мало</b> / <b>норм</b> / <b>много</b>",
            reply_markup=kb_level()
        )
        return

    # ===== ЛЕПЕШКИ =====
    if step == "lepeshki":
        if text not in ["мало", "норм", "много"]:
            await message.reply(
                "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>",
                reply_markup=kb_level()
            )
            return
        state["lepeshki"] = text
        state["step"] = "patyr"
        await message.reply(
            "Патыр: <b>мало</b> / <b>норм</b> / <b>много</b>",
            reply_markup=kb_level()
        )
        return

    # ===== ПАТЫР =====
    if step == "patyr":
        if text not in ["мало", "норм", "много"]:
            await message.reply(
                "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>",
                reply_markup=kb_level()
            )
            return
        state["patyr"] = text
        state["step"] = "assortment"
        await message.reply(
            "Ассортимент: <b>мало</b> / <b>норм</b> / <b>много</b>",
            reply_markup=kb_level()
        )
        return

    # ===== АССОРТИМЕНТ (ФИНАЛ) =====
    if step == "assortment":
        if text not in ["мало", "норм", "много"]:
            await message.reply(
                "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>",
                reply_markup=kb_level()
            )
            return
        state["assortment"] = text

        market = state["market"]
        ostatki = state["ostatki"]
        bread = state["bread"]
        lepeshki = state["lepeshki"]
        patyr = state["patyr"]
        assortment = state["assortment"]
        photo_file_id = state["photo_file_id"]

        raw_text = (
            f"#Магазин: {market}\n"
            f"Остатки: {ostatki}\n"
            f"Хлеб: {bread}\n"
            f"Лепешки: {lepeshki}\n"
            f"Патыр: {patyr}\n"
            f"Ассортимент: {assortment}"
        )

        # Сохраняем в БД
        save_report(
            user=message.from_user,
            market=market,
            photo_file_id=photo_file_id,
            bread=bread,
            lepeshki=lepeshki,
            patyr=patyr,
            assortment=assortment,
            raw_text=raw_text,
        )

        # Удаляем состояние
        user_states.pop(user_id, None)

        # Убираем клавиатуру
        rm = types.ReplyKeyboardRemove()

        # Итоговый отчёт в тот же чат (группа или личка)
        try:
            await bot.send_photo(
                chat_id,
                photo_file_id,
                caption=raw_text,
                reply_markup=rm
            )
        except Exception as e:
            logging.error(f"Ошибка отправки фото в чат {chat_id}: {e}")
            await message.reply(raw_text, reply_markup=rm)

        await message.reply("Отчёт сохранён и отправлен ✅", reply_markup=rm)
        return


# Логируем остальные тексты, чтобы видеть активность
@dp.message_handler(content_types=types.ContentType.TEXT)
async def debug_text(message: types.Message):
    logging.info(f"[TEXT] user_id={message.from_user.id}, chat_id={message.chat.id}, text={message.text}")


if __name__ == "__main__":
    logging.info("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
