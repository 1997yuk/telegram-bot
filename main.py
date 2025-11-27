# -*- coding: utf-8 -*-
import logging
import sqlite3
import io
import csv
from collections import defaultdict

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# 🔐 Токен бота
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

# 🔗 ID группы, куда отправляем итоговый отчёт
TARGET_GROUP_ID = -1003247828545  # <<< ЗАМЕНИ НА РЕАЛЬНЫЙ chat_id ГРУППЫ

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ ПО ID =====
# Обычные админы (могут status, photos_today, report, report_store, report_day, tm_status)
ADMIN_IDS = {
    7299148874,  # <<< сюда поставь свой Telegram ID и других админов через запятую
}

# Суперадмины (reset, export + всё, что у обычных админов)
SUPER_ADMIN_IDS = {
    7299148874,  # <<< сюда тоже свой ID (может быть тот же, что и выше)
}


def is_admin(user: types.User) -> bool:
    """Обычный админ (по id)."""
    return user.id in ADMIN_IDS or user.id in SUPER_ADMIN_IDS


def is_super_admin(user: types.User) -> bool:
    """Суперадмин (по id)."""
    return user.id in SUPER_ADMIN_IDS


# ===== СПИСОК МАРКЕТОВ (ТОЛЬКО НУЖНЫЕ) =====
MARKETS_TEXT = """
Маркет С-16
Маркет С-17
Маркет С-19
Маркет С-20
Маркет М-53
Маркет М-64
Маркет М-66
Маркет М-72
Маркет М-75
Маркет М-107
Маркет М-109
Маркет М-137
Маркет М-144
Маркет М-151
"""

MARKETS = [line.strip() for line in MARKETS_TEXT.splitlines() if line.strip()]

# 🔹 РАСПРЕДЕЛЕНИЕ МАРКЕТОВ ПО ТЕРРИТОРИАЛЬНЫМ МЕНЕДЖЕРАМ
# TODO: заполни реальными ТМ и их магазинами
TERRITORIAL_MANAGERS = {
    "tm1": {
        "title": "ТМ 1 (пример)",
        "markets": [
            "Маркет С-16",
            "Маркет С-17",
        ],
    },
    "tm2": {
        "title": "ТМ 2 (пример)",
        "markets": [
            "Маркет С-19",
            "Маркет С-20",
            "Маркет М-53",
        ],
    },
    # добавь сюда остальных ТМ по аналогии
}

# Группировка по префиксу (С, М...)
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

# таблица отчётов
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        market TEXT,
        ostatki TEXT,
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

# таблица языков пользователей
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS user_lang (
        user_id INTEGER PRIMARY KEY,
        lang TEXT
    )
    """
)
conn.commit()

# Добавляем поля, если таблица reports была старой
cur.execute("PRAGMA table_info(reports)")
cols = [row[1] for row in cur.fetchall()]
if "ostatki" not in cols:
    cur.execute("ALTER TABLE reports ADD COLUMN ostatki TEXT")
    conn.commit()
    logging.info("Добавлена колонка ostatki в таблицу reports")
if "incoming" not in cols:
    cur.execute("ALTER TABLE reports ADD COLUMN incoming TEXT")
    conn.commit()
    logging.info("Добавлена колонка incoming в таблицу reports")

logging.info("База данных и таблицы (SQLite) готовы")

# ===== КЭШ ЯЗЫКА В ПАМЯТИ =====
USER_LANG = {}  # user_id -> 'ru' / 'uz'


def set_lang(user_id: int, lang: str):
    """Сохранить язык в памяти и в БД."""
    if lang not in ("ru", "uz"):
        lang = "ru"
    USER_LANG[user_id] = lang
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO user_lang (user_id, lang)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang
        """,
        (user_id, lang),
    )
    conn.commit()


def get_lang(user_id: int) -> str:
    """Получить язык пользователя (сначала из памяти, потом из БД)."""
    if user_id in USER_LANG:
        return USER_LANG[user_id]
    c = conn.cursor()
    c.execute("SELECT lang FROM user_lang WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and row[0] in ("ru", "uz"):
        USER_LANG[user_id] = row[0]
        return row[0]
    return "ru"


def save_report(
    user: types.User,
    market: str,
    photo_file_id: str,
    ostatki: str,
    incoming: str,
    bread: str,
    lepeshki: str,
    patyr: str,
    assortment: str,
    raw_text: str,
):
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO reports
        (user_id, username, full_name, market,
         ostatki, incoming, bread, lepeshki, patyr, assortment,
         raw_text, photo_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.full_name,
            market,
            ostatki,
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


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ОТЧЁТОВ ПО ДАТЕ =====
def build_text_report_for_date(date_str):
    """
    Строит текстовый сводный отчёт за указанный день.
    date_str = None  -> сегодня (UTC+5)
    date_str = 'YYYY-MM-DD' -> конкретная дата (UTC+5)
    """
    c = conn.cursor()

    if date_str is None:
        # сегодня
        date_label = "сегодня (UTC+5)"
        c.execute(
            """
            SELECT market, ostatki, incoming, bread, lepeshki, patyr, assortment, id
            FROM reports
            WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
            ORDER BY id
            """
        )
    else:
        date_label = f"{date_str} (UTC+5)"
        c.execute(
            """
            SELECT market, ostatki, incoming, bread, lepeshki, patyr, assortment, id
            FROM reports
            WHERE date(datetime(created_at, '+5 hours')) = ?
            ORDER BY id
            """,
            (date_str,),
        )

    rows = c.fetchall()

    # market -> (ostatki, incoming, bread, lepeshki, patyr, assortment)
    last_by_market = {}
    for market, ostatki, incoming, bread, lepeshki, patyr, assortment, _id in rows:
        last_by_market[market] = (ostatki, incoming, bread, lepeshki, patyr, assortment)

    done_rows = []
    for m in MARKETS:
        if m in last_by_market:
            code = m.replace("Маркет", "").strip()
            ost, inc, br, le, pa, ass = last_by_market[m]
            done_rows.append((code, ost, inc, br, le, pa, ass))

    if not done_rows:
        return f"За {date_label} отчётов по магазинам нет."

    text = f"Отчёт за {date_label}:\n\n<pre>"
    for code, ost, inc, br, le, pa, ass in done_rows:
        line = (
            f"{code:<6} "
            f"Ост:{ost:<4} "
            f"Прх:{inc:<4} "
            f"Б:{br:<5} "
            f"Л:{le:<5} "
            f"П:{pa:<5} "
            f"Ас:{ass:<5}"
        )
        text += f"{line}\n"
    text += "</pre>"

    return text


def get_last_reports_for_date(date_str):
    """
    Возвращает список последних отчётов по каждому магазину за день:
    [(market, raw_text, photo_file_id, created_at_uz), ...]
    """
    c = conn.cursor()

    if date_str is None:
        c.execute(
            """
            SELECT
                market,
                raw_text,
                photo_file_id,
                datetime(created_at, '+5 hours') AS created_at_uz,
                id
            FROM reports
            WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
            ORDER BY id
            """
        )
    else:
        c.execute(
            """
            SELECT
                market,
                raw_text,
                photo_file_id,
                datetime(created_at, '+5 hours') AS created_at_uz,
                id
            FROM reports
            WHERE date(datetime(created_at, '+5 hours')) = ?
            ORDER BY id
            """,
            (date_str,),
        )

    rows = c.fetchall()

    # Оставляем по одному последнему отчёту на каждый магазин
    last_by_market = {}
    for market, raw_text, photo_file_id, created_at_uz, _id in rows:
        last_by_market[market] = (raw_text, photo_file_id, created_at_uz)

    result = []
    for m in MARKETS:
        if m in last_by_market:
            raw_text, photo_file_id, created_at_uz = last_by_market[m]
            result.append((m, raw_text, photo_file_id, created_at_uz))

    return result


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
        kb.row(KeyboardButton("ha"), KeyboardButton("yoq"))
    else:
        kb.row(KeyboardButton("да"), KeyboardButton("нет"))
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
    # В ГРУППЕ: обычных пользователей игнорируем, админам говорим, что бот работает в личке
    if message.chat.type != "private":
        if not is_admin(message.from_user):
            return
        await message.reply(
            "Этот бот собирает отчёты только в личных сообщениях.\n"
            "Попросите сотрудников отправлять фото и ответы боту в личку."
        )
        return

    # В ЛИЧКЕ: выбор языка
    text = "Выберите язык / Tilni tanlang:\n\nРусский 🇷🇺 / O‘zbekcha 🇺🇿"
    await message.reply(text, reply_markup=kb_lang())


@dp.message_handler(
    lambda m: m.chat.type == "private"
    and m.text in ("Русский 🇷🇺", "O‘zbekcha 🇺🇿")
)
async def set_language(message: types.Message):
    user_id = message.from_user.id
    if message.text == "O‘zbekcha 🇺🇿":
        set_lang(user_id, "uz")
        text = (
            "Til o'rnatildi: O‘zbekcha 🇺🇿\n\n"
            "Endi vitrina fotosini shu chatga yuboring."
        )
    else:
        set_lang(user_id, "ru")
        text = (
            "Язык установлен: русский 🇷🇺\n\n"
            "Теперь отправьте фото витрины в этот чат."
        )
    await message.reply(text, reply_markup=ReplyKeyboardRemove())


@dp.message_handler(commands=["reset"])
async def cmd_reset(message: types.Message):
    # ❗Только супер-админ
    if not is_super_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    c = conn.cursor()
    c.execute(
        """
        DELETE FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        """
    )
    conn.commit()
    await message.answer("Все отчёты за сегодня удалены. Можно собирать заново.")


@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    # только для админов (в личке и в группах)
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    c = conn.cursor()
    # Берём все отчёты за сегодня и по каждому маркету оставляем последний (по id)
    c.execute(
        """
        SELECT market, ostatki, incoming, bread, lepeshki, patyr, assortment, id
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        ORDER BY id
        """
    )
    rows = c.fetchall()

    last_by_market = {}
    for market, ostatki, incoming, bread, lepeshki, patyr, assortment, _id in rows:
        last_by_market[market] = (ostatki, incoming, bread, lepeshki, patyr, assortment)

    done_rows = []
    not_done = []

    for m in MARKETS:
        code = m.replace("Маркет", "").strip()
        if m in last_by_market:
            ost, inc, br, le, pa, ass = last_by_market[m]
            done_rows.append((code, ost, inc, br, le, pa, ass))
        else:
            not_done.append(f"❌ {code}")

    text = "Статус отчётов на сегодня (UTC+5):\n\n"

    if done_rows:
        text += "<pre>"
        for code, ost, inc, br, le, pa, ass in done_rows:
            line = (
                f"{code:<6} "
                f"Ост:{ost:<4} "
                f"Прх:{inc:<4} "
                f"Б:{br:<5} "
                f"Л:{le:<5} "
                f"П:{pa:<5} "
                f"Ас:{ass:<5}"
            )
            text += f"✅ {line}\n"
        text += "</pre>\n\n"
    else:
        text += "Пока никто не отправил отчёт.\n\n"

    if not_done:
        text += "Ещё НЕ отправили:\n" + "\n".join(not_done)

    await message.answer(text)


@dp.message_handler(commands=["tm_status"])
async def cmd_tm_status(message: types.Message):
    """
    /tm_status — динамический отчёт по территориальным менеджерам.
    Сначала показываем список ТМ, далее по клику — маркеты, кто отправил/нет.
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    kb = InlineKeyboardMarkup()
    for key, info in TERRITORIAL_MANAGERS.items():
        title = info["title"]
        kb.add(InlineKeyboardButton(title, callback_data=f"tm:{key}"))

    await message.reply("Выберите территориального менеджера:", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("tm:"))
async def tm_status_details(callback_query: types.CallbackQuery):
    """
    Обработка нажатия на ТМ:
    показываем, какие его маркеты отправили отчёт, а какие нет.
    """
    if not is_admin(callback_query.from_user):
        await callback_query.answer("Нет прав", show_alert=True)
        return

    key = callback_query.data.split(":", 1)[1]
    if key not in TERRITORIAL_MANAGERS:
        await callback_query.answer("Неизвестный ТМ", show_alert=True)
        return

    info = TERRITORIAL_MANAGERS[key]
    title = info["title"]
    markets = info["markets"]

    if not markets:
        await callback_query.message.edit_text(
            f"{title}\n\nУ этого ТМ нет привязанных маркетов."
        )
        await callback_query.answer()
        return

    c = conn.cursor()
    placeholders = ",".join("?" * len(markets))
    sql = f"""
        SELECT
            market,
            username,
            full_name,
            datetime(created_at, '+5 hours') AS created_at_uz,
            id
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
          AND market IN ({placeholders})
        ORDER BY id
    """
    c.execute(sql, markets)
    rows = c.fetchall()

    last_by_market = {}
    for market, username, full_name, created_at_uz, _id in rows:
        last_by_market[market] = (username, full_name, created_at_uz)

    sent_lines = []
    not_sent_lines = []

    for m in markets:
        code = m.replace("Маркет", "").strip()
        if m in last_by_market:
            username, full_name, created_at_uz = last_by_market[m]
            if username and full_name:
                sender = f"@{username} ({full_name})"
            elif username:
                sender = f"@{username}"
            elif full_name:
                sender = full_name
            else:
                sender = "неизвестно"

            sent_lines.append(f"✅ {code} — {sender}")
        else:
            not_sent_lines.append(f"❌ {code}")

    text = f"{title}\nСтатус за сегодня (UTC+5):\n\n"

    if sent_lines:
        text += "Отправили:\n" + "\n".join(sent_lines) + "\n\n"
    else:
        text += "Отправивших пока нет.\n\n"

    if not_sent_lines:
        text += "Не отправили:\n" + "\n".join(not_sent_lines)

    await callback_query.message.edit_text(text)
    await callback_query.answer()


@dp.message_handler(commands=["report"])
async def cmd_report(message: types.Message):
    """
    /report  -> текстовый + фото отчёт за СЕГОДНЯ по всем магазинам.
    (для конкретного магазина: /report_store,
     для другой даты: /report_day YYYY-MM-DD)
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    args = message.get_args().strip()
    if args:
        await message.reply(
            "Для отчёта по конкретному магазину используйте:\n"
            "<code>/report_store Маркет М-53</code>\n\n"
            "Для отчёта за конкретный день:\n"
            "<code>/report_day 2025-11-21</code>"
        )
        return

    # 1) текстовая сводка за сегодня
    text = build_text_report_for_date(None)  # сегодня
    await message.reply(text)

    # 2) фото-отчёты за сегодня (последний отчёт по каждому магазину)
    reports = get_last_reports_for_date(None)
    if not reports:
        return

    await message.reply("Фото-отчёты за сегодня по магазинам:")

    for market, raw_text, photo_file_id, created_at_uz in reports:
        if photo_file_id:
            try:
                await message.reply_photo(photo_file_id, caption=raw_text)
            except Exception as e:
                logging.error(f"Ошибка отправки фото в /report: {e}")
                await message.reply(raw_text)
        else:
            await message.reply(raw_text)


@dp.message_handler(commands=["report_store"])
async def cmd_report_store(message: types.Message):
    """
    /report_store Маркет М-53
    Показывает последний отчёт за сегодня по указанному магазину (фото + текст).
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    args = message.get_args().strip()
    if not args:
        await message.reply(
            "Укажите магазин, например:\n"
            "<code>/report_store Маркет М-53</code>"
        )
        return

    if args not in MARKETS:
        await message.reply(
            "Не нашёл такой магазин.\n"
            "Напишите точно как в списке, например:\n"
            "<code>/report_store Маркет М-53</code>"
        )
        return

    market = args
    c = conn.cursor()
    c.execute(
        """
        SELECT
            id,
            datetime(created_at, '+5 hours') AS created_at_uz,
            raw_text,
            photo_file_id
        FROM reports
        WHERE market = ?
          AND date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        ORDER BY id DESC
        LIMIT 1
        """,
        (market,),
    )
    row = c.fetchone()

    if not row:
        await message.reply("Сегодня по этому магазину ещё нет отчёта.")
        return

    _id, created_at_uz, raw_text, photo_file_id = row
    caption = f"{raw_text}\n\nВремя (UTC+5): {created_at_uz}"

    if photo_file_id:
        await message.reply_photo(photo_file_id, caption=caption)
    else:
        await message.reply(caption)


@dp.message_handler(commands=["report_day"])
async def cmd_report_day(message: types.Message):
    """
    /report_day YYYY-MM-DD
    Текстовый + фото отчёт за выбранный день по всем магазинам.
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    args = message.get_args().strip()
    if not args:
        await message.reply(
            "Укажите дату в формате YYYY-MM-DD, например:\n"
            "<code>/report_day 2025-11-21</code>"
        )
        return

    date_str = args

    # 1) текстовая сводка за день
    text = build_text_report_for_date(date_str)
    await message.reply(text)

    # 2) фото-отчёты за выбранный день
    reports = get_last_reports_for_date(date_str)
    if not reports:
        return

    await message.reply(f"Фото-отчёты за {date_str}:")

    for market, raw_text, photo_file_id, created_at_uz in reports:
        if photo_file_id:
            try:
                await message.reply_photo(photo_file_id, caption=raw_text)
            except Exception as e:
                logging.error(f"Ошибка отправки фото в /report_day: {e}")
                await message.reply(raw_text)
        else:
            await message.reply(raw_text)


@dp.message_handler(commands=["export"])
async def cmd_export(message: types.Message):
    # ❗Только супер-админ
    if not is_super_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    c = conn.cursor()
    c.execute(
        """
        SELECT
            id,
            datetime(created_at, '+5 hours') AS created_at_uz,
            market,
            ostatki,
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
    rows = c.fetchall()
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
            "остатки",
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
    buf.name = "reports_all.csv"

    await message.reply_document(buf, caption="Выгрузка всех отчётов из базы.")


@dp.message_handler(commands=["photos_today"])
async def cmd_photos_today(message: types.Message):
    # Обычные админы + супер-админы
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
                    "<code>/photos_today Маркет М-53</code>\n"
                    "или\n"
                    "<code>/photos_today все</code>",
                )
                return
            market_filter = args

    c = conn.cursor()
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

    c.execute(base_sql, params)
    rows = c.fetchall()

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
        code = market.replace("Маркет", "").strip()
        caption = f"{code}\n{created_at_uz}"
        try:
            await message.reply_photo(file_id, caption=caption)
        except Exception as e:
            logging.error(f"Ошибка отправки фото: {e}")


# ===== ОБРАБОТКА ФОТО (ТОЛЬКО ЛИЧКА) =====
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    # если это группа и отправитель не админ — вообще молчим
    if message.chat.type != "private":
        if not is_admin(message.from_user):
            return
   (""")


::contentReference[oaicite:0]{index=0}
