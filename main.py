# -*- coding: utf-8 -*-
import logging
import sqlite3
import io
import csv
from collections import defaultdict

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# 🔐 Токен бота
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

# 🔗 ID группы, куда отправляем итоговый отчёт
# пример: -1001234567890
TARGET_GROUP_ID = -1001234567890  # <<< ЗАМЕНИ НА РЕАЛЬНЫЙ chat_id ГРУППЫ

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ (username без @) =====
ADMIN_USERNAMES = {"yusubovk"}


def is_admin(user: types.User) -> bool:
    return bool(user.username and user.username.lower() in ADMIN_USERNAMES)


# ===== СПИСОК МАРКЕТОВ =====
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

# Группировка по префиксу (B, D, Dz, K, А, М, С, S...)
MARKET_GROUPS = defaultdict(list)
for m in MARKETS:
    code = m.replace("Маркет", "").strip()
    prefix = code.split("-")[0].strip()
    MARKET_GROUPS[prefix].append(m)

MARKET_GROUP_CODES = sorted(MARKET_GROUPS.keys())

# ===== БАЗА ДАННЫХ (SQLite) =====
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
        incoming TEXT,
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

# Добавляем колонку incoming, если её не было
cur.execute("PRAGMA table_info(reports)")
cols = [row[1] for row in cur.fetchall()]
if "incoming" not in cols:
    cur.execute("ALTER TABLE reports ADD COLUMN incoming TEXT")
    conn.commit()
    logging.info("Добавлена колонка incoming в таблицу reports")

logging.info("База данных и таблица reports готовы")


def save_report(user: types.User, market: str, photo_file_id: str,
                incoming: str, bread: str, lepeshki: str,
                patyr: str, assortment: str, raw_text: str):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reports
        (user_id, username, full_name, market,
         incoming, bread, lepeshki, patyr, assortment,
         raw_text, photo_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.full_name,
            market,
            incoming,
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


# ===== ЯЗЫК ПОЛЬЗОВАТЕЛЯ =====
USER_LANG = {}  # user_id -> 'ru' / 'uz'


def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "ru")


# ===== СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ =====
user_states = {}  # step, photo_file_id, market_group, market, ostatki, incoming, bread...


# ===== КЛАВИАТУРЫ =====
def kb_lang():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("Русский 🇷🇺"), KeyboardButton("O‘zbekcha 🇺🇿"))
    return kb


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


def kb_ostatki(lang: str):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == "uz":
        kb.row(KeyboardButton("to'g'ri"), KeyboardButton("noto'g'ri"))
    else:
        kb.row(KeyboardButton("корректные"), KeyboardButton("некорректные"))
    return kb


def kb_incoming(lang: str):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == "uz":
        kb.row(KeyboardButton("Ha"), KeyboardButton("Yo'q"))
    else:
        kb.row(KeyboardButton("Да"), KeyboardButton("Нет"))
    return kb


def kb_level(lang: str):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == "uz":
        kb.row(KeyboardButton("kam"), KeyboardButton("yetarli"), KeyboardButton("ko'p"))
    else:
        kb.row(KeyboardButton("мало"), KeyboardButton("норм"), KeyboardButton("много"))
    return kb


# ===== КОМАНДЫ =====
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = "Выберите язык / Tilni tanlang:\n\nРусский 🇷🇺 / O‘zbekcha 🇺🇿"
    await message.reply(text, reply_markup=kb_lang())


@dp.message_handler(lambda m: m.chat.type == "private" and m.text in ("Русский 🇷🇺", "O‘zbekcha 🇺🇿"))
async def set_language(message: types.Message):
    user_id = message.from_user.id
    if message.text == "O‘zbekcha 🇺🇿":
        USER_LANG[user_id] = "uz"
        text = (
            "Til o'rnatildi: O‘zbekcha 🇺🇿\n\n"
            "Endi vitrina fotosini shu chatga yuboring."
        )
    else:
        USER_LANG[user_id] = "ru"
        text = (
            "Язык установлен: русский 🇷🇺\n\n"
            "Теперь отправьте фото витрины в этот чат."
        )
    await message.reply(text, reply_markup=ReplyKeyboardRemove())


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
            incoming,
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
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        [
            "id",
            "created_at",
            "market",
            "приход",
            "Буханку",
            "лепешки",
            "патир",
            "ассортимент",
            "user_id",
            "username",
            "full_name",
        ]
    )
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


# ===== ОБРАБОТКА ФОТО (ТОЛЬКО ЛИЧКА) =====
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    if message.chat.type != "private":
        await message.reply(
            "Пожалуйста, отправьте фото отчёта в ЛИЧКУ боту. "
            "В группе будут только готовые отчёты."
        )
        return

    user_id = message.from_user.id
    photo = message.photo[-1]
    file_id = photo.file_id
    lang = get_lang(user_id)

    logging.info(f"[PHOTO] user_id={user_id}, private chat, file_id={file_id}")

    user_states[user_id] = {
        "step": "market_group",
        "photo_file_id": file_id,
        "market_group": None,
        "market": None,
        "ostatki": None,
        "incoming": None,
        "bread": None,
        "lepeshki": None,
        "patyr": None,
        "assortment": None,
    }

    if lang == "uz":
        text = "Rasm qabul qilindi ✅\nAvval Do'kon guruhini (harfini) tanlang:"
    else:
        text = "Фото получено ✅\nСначала выберите группу маркета (букву):"

    await message.reply(text, reply_markup=kb_market_groups())


# ===== ОБРАБОТКА ШАГОВ (ЛИЧКА) =====
@dp.message_handler(
    lambda m: m.chat.type == "private"
    and m.text is not None
    and m.from_user.id in user_states
)
async def handle_steps(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states[user_id]
    step = state["step"]
    lang = get_lang(user_id)

    # выбор группы
    if step == "market_group":
        if text not in MARKET_GROUPS:
            if lang == "uz":
                txt = "Quyidagi ro'yxatdan guruhni tanlang:"
            else:
                txt = "Выберите группу маркета из списка ниже:"
            await message.reply(txt, reply_markup=kb_market_groups())
            return
        state["market_group"] = text
        state["step"] = "market"
        if lang == "uz":
            txt = f"Guruh <b>{text}</b> tanlandi.\nEndi aniq Do'konni tanlang:"
        else:
            txt = f"Группа <b>{text}</b> выбрана.\nТеперь выберите конкретный маркет:"
        await message.reply(txt, reply_markup=kb_markets_for_group(text))
        return

    # выбор маркета
    if step == "market":
        valid_markets = MARKET_GROUPS.get(state["market_group"], [])
        if text not in valid_markets:
            if lang == "uz":
                txt = "Quyidagi tugmalardan Do'konni tanlang."
            else:
                txt = "Выберите маркет из списка кнопок ниже."
            await message.reply(
                txt, reply_markup=kb_markets_for_group(state["market_group"])
            )
            return
        state["market"] = text
        state["step"] = "ostatki"
        if lang == "uz":
            txt = "Qoldiq: <b>to'g'ri</b> yoki <b>noto'g'ri</b>ni tanlang."
        else:
            txt = "Остатки: выберите <b>корректные</b> или <b>некорректные</b>."
        await message.reply(txt, reply_markup=kb_ostatki(lang))
        return

    # остатки
    if step == "ostatki":
        if lang == "uz":
            allowed = ["to'g'ri", "noto'g'ri"]
        else:
            allowed = ["корректные", "некорректные"]

        if text not in allowed:
            if lang == "uz":
                txt = "Tanlang: <b>to'g'ri</b> yoki <b>noto'g'ri</b>."
            else:
                txt = "Выберите: <b>корректные</b> или <b>некорректные</b>."
            await message.reply(txt, reply_markup=kb_ostatki(lang))
            return

        state["ostatki"] = text
        state["step"] = "incoming"
        if lang == "uz":
            txt = "Prixod boldimi: <b>Ha</b> / <b>Yo'q</b>"
        else:
            txt = "Приход был: <b>Да</b> / <b>Нет</b>"
        await message.reply(txt, reply_markup=kb_incoming(lang))
        return

    # приход был
    if step == "incoming":
        if lang == "uz":
            allowed = ["Ha", "Yo'q"]
        else:
            allowed = ["Да", "Нет"]

        if text not in allowed:
            if lang == "uz":
                txt = "Tanlang: <b>Ha</b> yoki <b>Yo'q</b>."
            else:
                txt = "Выберите: <b>Да</b> или <b>Нет</b>."
            await message.reply(txt, reply_markup=kb_incoming(lang))
            return

        state["incoming"] = text
        state["step"] = "bread"
        if lang == "uz":
            txt = "Non: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b>"
        else:
            txt = "Хлеб: <b>мало</b> / <b>норм</b> / <b>много</b>"
        await message.reply(txt, reply_markup=kb_level(lang))
        return

    # хлеб
    if step == "bread":
        if lang == "uz":
            allowed = ["kam", "yetarli", "ko'p"]
        else:
            allowed = ["мало", "норм", "много"]

        if text not in allowed:
            if lang == "uz":
                txt = "Non: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b> dan birini tanlang."
            else:
                txt = "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>."
            await message.reply(txt, reply_markup=kb_level(lang))
            return

        state["bread"] = text
        state["step"] = "lepeshki"
        if lang == "uz":
            txt = "Yopgan non: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b>"
        else:
            txt = "Лепешки: <b>мало</b> / <b>норм</b> / <b>много</b>"
        await message.reply(txt, reply_markup=kb_level(lang))
        return

    # лепешки
    if step == "lepeshki":
        if lang == "uz":
            allowed = ["kam", "yetarli", "ko'p"]
        else:
            allowed = ["мало", "норм", "много"]

        if text not in allowed:
            if lang == "uz":
                txt = "Yopgan non: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b> dan birini tanlang."
            else:
                txt = "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>."
            await message.reply(txt, reply_markup=kb_level(lang))
            return

        state["lepeshki"] = text
        state["step"] = "patyr"
        if lang == "uz":
            txt = "Patir: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b>"
        else:
            txt = "Патыр: <b>мало</b> / <b>норм</b> / <b>много</b>"
        await message.reply(txt, reply_markup=kb_level(lang))
        return

    # патыр
    if step == "patyr":
        if lang == "uz":
            allowed = ["kam", "yetarli", "ko'p"]
        else:
            allowed = ["мало", "норм", "много"]

        if text not in allowed:
            if lang == "uz":
                txt = "Patir: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b> dan birini tanlang."
            else:
                txt = "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>."
            await message.reply(txt, reply_markup=kb_level(lang))
            return

        state["patyr"] = text
        state["step"] = "assortment"
        if lang == "uz":
            txt = "Assortiment: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b>"
        else:
            txt = "Ассортимент: <b>мало</b> / <b>норм</b> / <b>много</b>"
        await message.reply(txt, reply_markup=kb_level(lang))
        return

    # ассортимент (финал)
    if step == "assortment":
        if lang == "uz":
            allowed = ["kam", "yetarli", "ko'p"]
        else:
            allowed = ["мало", "норм", "много"]

        if text not in allowed:
            if lang == "uz":
                txt = "Assortiment: <b>kam</b> / <b>yetarli</b> / <b>ko'p</b> dan birini tanlang."
            else:
                txt = "Выберите: <b>мало</b> / <b>норм</b> / <b>много</b>."
            await message.reply(txt, reply_markup=kb_level(lang))
            return

        state["assortment"] = text

        # значения, которые ввёл пользователь (могут быть RU или UZ)
        market = state["market"]
        ostatki = state["ostatki"]
        incoming = state["incoming"]
        bread = state["bread"]
        lepeshki = state["lepeshki"]
        patyr = state["patyr"]
        assortment = state["assortment"]
        photo_file_id = state["photo_file_id"]

        # === Маппинг в РУССКИЕ значения для отчёта и БД ===
        def map_ostatki_ru(v: str) -> str:
            if v in ("корректные", "to'g'ri"):
                return "корректные"
            if v in ("некорректные", "noto'g'ri"):
                return "некорректные"
            return v

        def map_incoming_ru(v: str) -> str:
            if v in ("Да", "Ha"):
                return "Да"
            if v in ("Нет", "Yo'q"):
                return "Нет"
            return v

        def map_level_ru(v: str) -> str:
            if v in ("мало", "kam"):
                return "мало"
            if v in ("норм", "yetarli"):
                return "норм"
            if v in ("много", "ko'p"):
                return "много"
            return v

        ru_ostatki = map_ostatki_ru(ostatki)
        ru_incoming = map_incoming_ru(incoming)
        ru_bread = map_level_ru(bread)
        ru_lepeshki = map_level_ru(lepeshki)
        ru_patyr = map_level_ru(patyr)
        ru_assortment = map_level_ru(assortment)

        # русский текст отчёта (для группы и БД)
        raw_text = (
            f"#Магазин: {market}\n"
            f"Остатки: {ru_ostatki}\n"
            f"Приход был: {ru_incoming}\n"
            f"Хлеб: {ru_bread}\n"
            f"Лепешки: {ru_lepeshki}\n"
            f"Патыр: {ru_patyr}\n"
            f"Ассортимент: {ru_assortment}"
        )

        # сохраняем в БД русские значения
        save_report(
            user=message.from_user,
            market=market,
            photo_file_id=photo_file_id,
            incoming=ru_incoming,
            bread=ru_bread,
            lepeshki=ru_lepeshki,
            patyr=ru_patyr,
            assortment=ru_assortment,
            raw_text=raw_text,
        )

        user_states.pop(user_id, None)
        rm = ReplyKeyboardRemove()

        # отправляем отчёт в рабочую группу (только на русском)
        if TARGET_GROUP_ID:
            try:
                await bot.send_photo(TARGET_GROUP_ID, photo_file_id, caption=raw_text)
            except Exception as e:
                logging.error(f"Ошибка отправки фото в группу {TARGET_GROUP_ID}: {e}")

        if lang == "uz":
            txt = "Hisobot saqlandi va ishchi guruhga yuborildi ✅"
        else:
            txt = "Отчёт сохранён и отправлен в рабочую группу ✅"

        await message.reply(txt, reply_markup=rm)
        return


@dp.message_handler(content_types=types.ContentType.TEXT)
async def debug_text(message: types.Message):
    logging.info(
        f"[TEXT] user_id={message.from_user.id}, chat_type={message.chat.type}, text={message.text}"
    )


if __name__ == "__main__":
    logging.info("Бот запускается (SQLite, RU/UZ, отчёт в группе только на русском)...")
    executor.start_polling(dp, skip_updates=True)
