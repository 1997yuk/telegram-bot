# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from collections import defaultdict
import sqlite3
import io
import csv

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# 🔐 ТОКЕН ТВОЕГО БОТА
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ (по username без @) =====
ADMIN_USERNAMES = {"yusubovk"}  # сюда можно добавлять ещё ники


def is_admin(user: types.User) -> bool:
    return bool(user.username and user.username.lower() in ADMIN_USERNAMES)


# ===== СПИСОК МАРКЕТОВ =====
MARKETS = [
    "Маркет B-01",
    "Маркет B-02",
    "Маркет B-03",
    "Маркет B-04",
    "Маркет B-05",
    "Маркет B-06",
    "Маркет B-07",
    "Маркет B-08",
    "Маркет B-09",
    "Маркет D-01",
    "Маркет D-02",
    "Маркет D-03",
    "Маркет D-04",
    "Маркет D-05",
    "Маркет D-06",
    "Маркет D-07",
    "Маркет D-08",
    "Маркет D-09",
    "Маркет D-10",
    "Маркет D-12",
    "Маркет D-14",
    "Маркет D-16",
    "Маркет D-18",
    "Маркет Dz-01",
    "Маркет Dz-02",
    "Маркет Dz-03",
    "Маркет K-01",
    "Маркет K-02",
    "Маркет K-03",
    "Маркет K-04",
    "Маркет K-05",
    "Маркет K-06",
    "Маркет K-07",
    "Маркет А-01",
    "Маркет А-02",
    "Маркет А-03",
    "Маркет А-04",
    "Маркет А-05",
    "Маркет А-06",
    "Маркет А-07",
    "Маркет А-08",
    "Маркет А-09",
    "Маркет А-10",
    "Маркет А-11",
    "Маркет А-12",
    "Маркет А-13",
    "Маркет А-14",
    "Маркет А-15",
    "Маркет А-16",
    "Маркет А-17",
    "Маркет А-18",
    "Маркет А-19",
    "Маркет А-20",
    "Маркет А-21",
    "Маркет А-22",
    "Маркет А-23",
    "Маркет А-24",
    "Маркет А-25",
    "Маркет А-27",
    "Маркет А-28",
    "Маркет А-29",
    "Маркет А-30",
    "Маркет А-31",
    "Маркет А-32",
    "Маркет А-34",
    "Маркет А-35",
    "Маркет М-02",
    "Маркет М-03",
    "Маркет М-04",
    "Маркет М-05",
    "Маркет М-06",
    "Маркет М-07",
    "Маркет М-08",
    "Маркет М-101",
    "Маркет М-102",
    "Маркет М-103",
    "Маркет М-104",
    "Маркет М-105",
    "Маркет М-106",
    "Маркет М-107",
    "Маркет М-108",
    "Маркет М-109",
    "Маркет М-11",
    "Маркет М-110",
    "Маркет М-111",
    "Маркет М-112",
    "Маркет М-113",
    "Маркет М-114",
    "Маркет М-115",
    "Маркет М-116",
    "Маркет М-117",
    "Маркет М-118",
    "Маркет М-119",
    "Маркет М-12",
    "Маркет М-120",
    "Маркет М-121",
    "Маркет М-122",
    "Маркет М-123",
    "Маркет М-124",
    "Маркет М-125",
    "Маркет М-126",
    "Маркет М-127",
    "Маркет М-128",
    "Маркет М-129",
    "Маркет М-13",
    "Маркет М-130",
    "Маркет М-131",
    "Маркет М-132",
    "Маркет М-133",
    "Маркет М-134",
    "Маркет М-135",
    "Маркет М-137",
    "Маркет М-139",
    "Маркет М-14",
    "Маркет М-140",
    "Маркет М-141",
    "Маркет М-142",
    "Маркет М-143",
    "Маркет М-144",
    "Маркет М-145",
    "Маркет М-146",
    "Маркет М-147",
    "Маркет М-148",
    "Маркет М-149",
    "Маркет М-151",
    "Маркет М-156",
    "Маркет М-16",
    "Маркет М-161",
    "Маркет М-164",
    "Маркет М-18",
    "Маркет М-19",
    "Маркет М-20",
    "Маркет М-21",
    "Маркет М-22",
    "Маркет М-23",
    "Маркет М-25",
    "Маркет М-26",
    "Маркет М-27",
    "Маркет М-28",
    "Маркет М-30",
    "Маркет М-31",
    "Маркет М-32",
    "Маркет М-33",
    "Маркет М-34",
    "Маркет М-35",
    "Маркет М-36",
    "Маркет М-37",
    "Маркет М-40",
    "Маркет М-41",
    "Маркет М-42",
    "Маркет М-43",
    "Маркет М-44",
    "Маркет М-45",
    "Маркет М-46",
    "Маркет М-47",
    "Маркет М-48",
    "Маркет М-49",
    "Маркет М-50",
    "Маркет М-51",
    "Маркет М-53",
    "Маркет М-55",
    "Маркет М-56",
    "Маркет М-57",
    "Маркет М-58",
    "Маркет М-59",
    "Маркет М-60",
    "Маркет М-61",
    "Маркет М-62",
    "Маркет М-63",
    "Маркет М-64",
    "Маркет М-65",
    "Маркет М-66",
    "Маркет М-67",
    "Маркет М-68",
    "Маркет М-69",
    "Маркет М-70",
    "Маркет М-71",
    "Маркет М-72",
    "Маркет М-73",
    "Маркет М-74",
    "Маркет М-75",
    "Маркет М-76",
    "Маркет М-78",
    "Маркет М-79",
    "Маркет М-80",
    "Маркет М-81",
    "Маркет М-82",
    "Маркет М-83",
    "Маркет М-84",
    "Маркет М-85",
    "Маркет М-86",
    "Маркет М-87",
    "Маркет М-88",
    "Маркет М-89",
    "Маркет М-90",
    "Маркет М-91",
    "Маркет М-92",
    "Маркет М-93",
    "Маркет М-95",
    "Маркет М-96",
    "Маркет М-97",
    "Маркет М-98",
    "Маркет М-99",
    "Маркет С-01",
    "Маркет С-03",
    "Маркет С-04",
    "Маркет С-05",
    "Маркет С-06",
    "Маркет С-07",
    "Маркет С-08",
    "Маркет С-09",
    "Маркет С-10",
    "Маркет С-11",
    "Маркет С-12",
    "Маркет С-13",
    "Маркет С-14",
    "Маркет С-15",
    "Маркет С-16Т",
    "Маркет С-17",
    "Маркет С-18",
    "Маркет С-19",
    "Маркет С-20",
    "Маркет С-21",
    "Маркет С-22",
    "Маркет С-27",
    "Маркет М-153",
    "Маркет D-17",
    "Маркет D-15",
    "Маркет С-23",
    "Маркет А-37",
    "Маркет S-01",
    "Маркет S-03",
    "Маркет S-06",
    "Маркет S-09",
    "Маркет С-25",
    "Маркет Dz-04",
]

# ===== ГРУППИРОВКА ПО ПРЕФИКСАМ =====

def get_prefix(market_name: str) -> str:
    code = market_name.replace("Маркет", "").strip()
    return code.split("-")[0]


MARKETS_BY_PREFIX = defaultdict(list)
for m in MARKETS:
    MARKETS_BY_PREFIX[get_prefix(m)].append(m)

PREFIXES = sorted(MARKETS_BY_PREFIX.keys())

# ===== СОСТОЯНИЯ И ЕЖЕДНЕВНЫЙ СТАТУС =====

# user_id -> {"step", "prefix", "market", "photo_file_id"}
pending_reports = {}
daily_reports = {name: False for name in MARKETS}
current_date = datetime.now().date()


def reset_reports():
    global daily_reports, current_date
    current_date = datetime.now().date()
    daily_reports = {name: False for name in MARKETS}


def check_date_and_reset():
    global current_date
    today = datetime.now().date()
    if today != current_date:
        reset_reports()


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
        bread INTEGER,
        lepeshki INTEGER,
        patyr INTEGER,
        assortment INTEGER,
        raw_text TEXT,
        photo_file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()


def parse_report_text(text: str):
    """
    Парсер строк:
    Хлеб: 10
    Лепешки: 5
    Патыр: 3
    Ассортимент: 20
    """
    bread = lep = patyr = assort = None
    lines = text.splitlines()
    for line in lines:
        l = line.strip()
        lower = l.lower()
        if lower.startswith("хлеб"):
            part = l.split(":", 1)[-1].strip()
            bread = int(part) if part.isdigit() else None
        elif lower.startswith("лепешк"):
            part = l.split(":", 1)[-1].strip()
            lep = int(part) if part.isdigit() else None
        elif lower.startswith("патыр"):
            part = l.split(":", 1)[-1].strip()
            patyr = int(part) if part.isdigit() else None
        elif "ассортимент" in lower:
            part = l.split(":", 1)[-1].strip()
            assort = int(part) if part.isdigit() else None
    return bread, lep, patyr, assort


def save_report(user: types.User, market: str, photo_file_id: str, text: str):
    bread, lep, patyr, assort = parse_report_text(text)
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
            lep,
            patyr,
            assort,
            text,
            photo_file_id,
        ),
    )
    conn.commit()


# ===== КЛАВИАТУРЫ =====

def prefix_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    row = []
    for i, p in enumerate(PREFIXES, start=1):
        row.append(types.KeyboardButton(p))
        if i % 4 == 0:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row(types.KeyboardButton("Отмена"))
    return kb


def markets_keyboard(prefix: str) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markets = MARKETS_BY_PREFIX[prefix]
    row = []
    for i, name in enumerate(markets, start=1):
        row.append(types.KeyboardButton(name))
        if i % 2 == 0:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row(types.KeyboardButton("Отмена"))
    return kb


# ===== ХЕНДЛЕРЫ КОМАНД =====

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = (
        "Привет! Я бот для фото-отчётов по магазинам.\n\n"
        "Как работать:\n"
        "1️⃣ В группе отправь фото отчёта.\n"
        "2️⃣ Я напишу тебе в личные сообщения (если ты нажал /start в ЛС).\n"
        "3️⃣ В личке выберешь префикс маркета и сам магазин.\n"
        "4️⃣ Я пришлю шаблон отчёта:\n"
        "<code>#Магазин: ...\n"
        "Хлеб:\n"
        "Лепешки:\n"
        "Патыр:\n"
        "Ассортимент:</code>\n"
        "Заполняешь числа и отправляешь одним сообщением.\n\n"
        "Команды:\n"
        "/status – кто уже отправил отчёт за сегодня\n"
        "/reset  – обнулить отчёты (для админов)\n"
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
    reset_reports()
    await message.answer("Отчёты обнулены на сегодня. Жду фото от всех маркетов.")


@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    check_date_and_reset()

    done = []
    not_done = []

    for name in MARKETS:
        if daily_reports.get(name):
            done.append(f"✅ {name}")
        else:
            not_done.append(f"❌ {name}")

    today = datetime.now().date()
    text = f"Статус отчётов на сегодня ({today}):\n\n"
    if done:
        text += "Отправили отчёт:\n" + "\n".join(done) + "\n\n"
    else:
        text += "Пока никто не отправил отчёт.\n\n"

    if not_done:
        text += "Ещё НЕ отправили:\n" + "\n".join(not_done)
    else:
        text += "Все маркеты отправили отчёт. 👍"

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

    # Аргументы после команды: /photos_today Маркет М-11
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
            logging.error(f"Ошибка отправки фото {file_id}: {e}")


# ===== ОСНОВНОЙ ПРОЦЕСС ОТЧЁТА =====

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """
    Фото может прийти из группы или из лички.
    Логику делаем такой:
    - состояние отчёта создаём всегда по user_id;
    - дальнейшее общение стараемся вести в личке (chat_id = user_id);
    - если бот не может написать в личку (пользователь не нажал /start),
      коротко сообщаем об этом в том чате, откуда пришло фото.
    """
    check_date_and_reset()

    user_id = message.from_user.id
    photo = message.photo[-1]
    file_id = photo.file_id

    pending_reports[user_id] = {
        "step": "choose_prefix",
        "prefix": None,
        "market": None,
        "photo_file_id": file_id,
    }

    # Пытаемся продолжить общение в личке
    try:
        # сначала отправим фото, чтобы человек видел, какой отчёт заполняет
        await bot.send_photo(
            user_id,
            file_id,
            caption="Это фото будет прикреплено к вашему отчёту."
        )
        await bot.send_message(
            user_id,
            "Выбери префикс своего маркета (буква/сочетание букв):",
            reply_markup=prefix_keyboard(),
        )

        # Если фото пришло из группы — можно ничего не писать туда
        # (всё общение пойдёт в личке)
    except Exception as e:
        logging.error(f"Не удалось написать пользователю в личку: {e}")
        # Сообщаем минимально в тот чат, откуда пришло фото
        await message.reply(
            "Я не могу написать вам в личные сообщения.\n"
            "Откройте чат со мной и нажмите /start, затем отправьте фото ещё раз."
        )


@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Отмена
    if text.lower() == "отмена":
        if user_id in pending_reports:
            pending_reports.pop(user_id, None)
        await message.reply(
            "Операция отменена.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    state = pending_reports.get(user_id)

    # Нет активного процесса отчёта — игнорируем
    if not state:
        return

    step = state.get("step")

    # Шаг 1: выбор префикса
    if step == "choose_prefix":
        if text not in PREFIXES:
            await message.reply(
                "Такого префикса нет. Выбери из клавиатуры ниже.",
                reply_markup=prefix_keyboard(),
            )
            return

        state["prefix"] = text
        state["step"] = "choose_market"

        await message.reply(
            f"Теперь выбери конкретный магазин с префиксом {text}:",
            reply_markup=markets_keyboard(text),
        )
        return

    # Шаг 2: выбор конкретного маркета
    if step == "choose_market":
        prefix = state.get("prefix")
        markets = MARKETS_BY_PREFIX.get(prefix, [])
        if text not in markets:
            await message.reply(
                "Такого магазина нет в списке. Выбери из клавиатуры ниже.",
                reply_markup=markets_keyboard(prefix),
            )
            return

        state["market"] = text
        state["step"] = "fill_template"

        template_text = (
            f"#Магазин: {text}\n"
            f"Хлеб: \n"
            f"Лепешки: \n"
            f"Патыр: \n"
            f"Ассортимент: "
        )

        await message.reply(
            "Теперь заполни шаблон, указав количества по каждому пункту "
            "и отправь СЛЕДУЮЩИМ сообщением:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await message.reply(f"<code>{template_text}</code>")
        return

    # Шаг 3: приём заполненного шаблона
    if step == "fill_template":
        market_name = state.get("market")
        photo_file_id = state.get("photo_file_id")
        if not market_name:
            pending_reports.pop(user_id, None)
            await message.reply("Ошибка состояния, начни заново (отправь фото).")
            return

        check_date_and_reset()
        daily_reports[market_name] = True

        # сохраняем в базу
        save_report(message.from_user, market_name, photo_file_id, text)

        pending_reports.pop(user_id, None)
        await message.reply(
            f"Отчёт для <b>{market_name}</b> сохранён ✅ Спасибо!"
        )
        return


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
