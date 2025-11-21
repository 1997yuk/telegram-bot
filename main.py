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
TARGET_GROUP_ID = -1003247828545  # <<< ЗАМЕНИ НА РЕАЛЬНЫЙ chat_id ГРУППЫ

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ ПО ID =====
# Обычные админы (могут status, photos_today, report)
ADMIN_IDS = {
    7299148874,
    44405876, # <<< сюда поставь свой Telegram ID и других админов через запятую
}

# Суперадмины (reset, export + всё, что у обычных админов)
SUPER_ADMIN_IDS = {
    7299148874, # <<< сюда тоже свой ID (может быть тот же, что и выше)
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

    # market -> (ostatki, incoming, bread, lepeshki, patyr, assortment)
    last_by_market = {}
    for market, ostatki, incoming, bread, lepeshki, patyr, assortment, _id in rows:
        last_by_market[market] = (ostatki, incoming, bread, lepeshki, patyr, assortment)

    done_rows = []   # список строк для тех, кто сдал
    not_done = []    # список строк для тех, кто не сдал

    for m in MARKETS:
        code = m.replace("Маркет", "").strip()  # оставляем только C-16 / M-53 и т.п.
        if m in last_by_market:
            ost, inc, br, le, pa, ass = last_by_market[m]
            done_rows.append((code, ost, inc, br, le, pa, ass))
        else:
            not_done.append(f"❌ {code}")

    text = "Статус отчётов на сегодня (UTC+5):\n\n"

    if done_rows:
        # Формируем ровный столбец в <pre>, чтобы всё было выровнено
        text += "<pre>"
        for code, ost, inc, br, le, pa, ass in done_rows:
            line = (
                f"{code:<6} "          # код магазина
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

@dp.message_handler(commands=["report"])
async def cmd_report(message: types.Message):
    """
    /report Маркет М-53
    Показывает последний отчёт за сегодня по указанному маркету.
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    args = message.get_args().strip()
    if not args:
        await message.reply(
            "Укажите магазин, например:\n"
            "<code>/report Маркет М-53</code>"
        )
        return

    if args not in MARKETS:
        await message.reply(
            "Не нашёл такой магазин.\n"
            "Напишите точно как в списке, например:\n"
            "<code>/report Маркет М-53</code>"
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
        await message.reply("Сегодня по этому маркету ещё нет отчёта.")
        return

    _id, created_at_uz, raw_text, photo_file_id = row
    caption = f"{raw_text}\n\nВремя (UTC+5): {created_at_uz}"

    if photo_file_id:
        await message.reply_photo(photo_file_id, caption=caption)
    else:
        await message.reply(caption)


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
    buf.name = "reports.csv"

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
        # админу в группе можем подсказать, что бот работает только в личке
        await message.reply(
            "Бот принимает отчёты только в личных сообщениях.\n"
            "Пожалуйста, отправьте фото боту в личку."
        )
        return

    user_id = message.from_user.id
    photo = message.photo[-1]
    file_id = photo.file_id
    lang = get_lang(user_id)

    logging.info(
        f"[PHOTO] user_id={user_id}, private chat, file_id={file_id}, lang={lang}"
    )

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
                txt = "Quyidagi ro'yхatdan guruhni tanlang:"
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
            txt = "ostatok tekshirdingmi? <b>ha</b> / <b>yoq</b>"
        else:
            txt = "Остатки проверил? <b>да</b> / <b>нет</b>"
        await message.reply(txt, reply_markup=kb_ostatki(lang))
        return

    # остатки (да/нет)
    if step == "ostatki":
        if lang == "uz":
            allowed = ["ha", "yoq"]
        else:
            allowed = ["да", "нет"]

        if text not in allowed:
            if lang == "uz":
                txt = "Tanlang: <b>ha</b> yoki <b>yoq</b>."
            else:
                txt = "Выберите: <b>да</b> или <b>нет</b>."
            await message.reply(txt, reply_markup=kb_ostatki(lang))
            return

        state["ostatki"] = text
        state["step"] = "incoming"
        if lang == "uz":
            txt = "Prixod boldimi? <b>Ha</b> / <b>Yo'q</b>"
        else:
            txt = "Приход был? <b>Да</b> / <b>Нет</b>"
        await message.reply(txt, reply_markup=kb_incoming(lang))
        return

    # приход был?
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
            txt = "Буханка: <b>мало</b> / <b>норм</b> / <b>много</b>"
        await message.reply(txt, reply_markup=kb_level(lang))
        return

    # буханка
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
            if lang == "уз":
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

        market = state["market"]
        ostatki = state["ostatki"]
        incoming = state["incoming"]
        bread = state["bread"]
        lepeshki = state["lepeshki"]
        patyr = state["patyr"]
        assortment = state["assortment"]
        photo_file_id = state["photo_file_id"]

        # маппинг ответов в русские значения
        def map_yesno_ru_from_ostatki(v: str) -> str:
            v_lower = v.lower()
            if v_lower in ("да", "ha"):
                return "Да"
            if v_lower in ("нет", "yoq"):
                return "Нет"
            return v

        def map_yesno_ru(v: str) -> str:
            v_lower = v.lower()
            if v_lower in ("да", "ha"):
                return "Да"
            if v_lower in ("нет", "yo'q", "yoq"):
                return "Нет"
            return v

        def map_level_ru(v: str) -> str:
            v_lower = v.lower()
            if v_lower in ("мало", "kam"):
                return "мало"
            if v_lower in ("норм", "yetarli"):
                return "норм"
            if v_lower in ("много", "ko'p"):
                return "много"
            return v

        ru_ostatki = map_yesno_ru_from_ostatki(ostatki)
        ru_incoming = map_yesno_ru(incoming)
        ru_bread = map_level_ru(bread)
        ru_lepeshki = map_level_ru(lepeshki)
        ru_patyr = map_level_ru(patyr)
        ru_assortment = map_level_ru(assortment)

        market_code = market.replace("Маркет", "").strip()

        raw_text = (
            f"#Магазин: {market_code}\n"
            f"Остатки проверил?: {ru_ostatki}\n"
            f"Приход был?: {ru_incoming}\n"
            f"Буханка: {ru_bread}\n"
            f"Лепешки: {ru_lepeshki}\n"
            f"Патыр: {ru_patyr}\n"
            f"Ассортимент: {ru_assortment}"
        )

        save_report(
            user=message.from_user,
            market=market,  # в базе оставляем полное название "Маркет С-16"
            photo_file_id=photo_file_id,
            ostatki=ru_ostatki,
            incoming=ru_incoming,
            bread=ru_bread,
            lepeshki=ru_lepeshki,
            patyr=ru_patyr,
            assortment=ru_assortment,
            raw_text=raw_text,
        )

        user_states.pop(user_id, None)
        rm = ReplyKeyboardRemove()

        # отправляем отчёт в рабочую группу (только на русском, с кодом магазина)
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
    # В группах не отвечаем обычным пользователям вообще
    if message.chat.type != "private" and not is_admin(message.from_user):
        return

    logging.info(
        f"[TEXT] user_id={message.from_user.id}, chat_type={message.chat.type}, text={message.text}"
    )


if __name__ == "__main__":
    logging.info(
        "Бот запускается (SQLite, RU/UZ, админы по user_id, роли админ/суперадмин)..."
    )
    executor.start_polling(dp, skip_updates=True)
