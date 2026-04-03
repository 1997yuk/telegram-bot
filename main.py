# -*- coding: utf-8 -*-
import logging
import sqlite3
import io
import csv

from collections import defaultdict
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

MAX_TG_MESSAGE = 4000  # небольшой запас до лимита 4096


async def send_long_message(message: types.Message, text: str):
    """
    Отправляет длинный текст несколькими сообщениями,
    чтобы не ловить ошибку MessageIsTooLong.
    """
    if len(text) <= MAX_TG_MESSAGE:
        await message.answer(text)
        return

    # режем по строкам, чтобы не рвать <pre> и т.п.
    lines = text.split("\n")
    chunk = ""
    for line in lines:
        # +1 за перенос строки
        if len(chunk) + len(line) + 1 > MAX_TG_MESSAGE:
            await message.answer(chunk)
            chunk = line
        else:
            if chunk:
                chunk += "\n" + line
            else:
                chunk = line

    if chunk:
        await message.answer(chunk)

# 🔐 Токен бота
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

# 🔗 ID группы, куда отправляем итоговый отчёт
TARGET_GROUP_ID = -1003203445630  # <<< ЗАМЕНИ НА РЕАЛЬНЫЙ chat_id ГРУППЫ

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ===== АДМИНЫ ПО ID =====
# Обычные админы (могут status, photos_today, report, report_store, report_day, tm_status)
ADMIN_IDS = {
    7299148874,
    44405876,
    8153551677, # <<< сюда поставь свой Telegram ID и других админов через запятую
}

# Суперадмины (reset, export + всё, что у обычных админов)
SUPER_ADMIN_IDS = {
    7299148874,
    8153551677, # <<< сюда тоже свой ID (может быть тот же, что и выше)
}


def is_admin(user: types.User) -> bool:
    """Обычный админ (по id)."""
    return user.id in ADMIN_IDS or user.id in SUPER_ADMIN_IDS


def is_super_admin(user: types.User) -> bool:
    """Суперадмин (по id)."""
    return user.id in SUPER_ADMIN_IDS


# ===== СПИСОК МАРКЕТОВ (ТОЛЬКО НУЖНЫЕ) =====
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
Маркет B-10 
Маркет B-11 
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
Маркет D-11 
Маркет D-12 
Маркет D-13 
Маркет D-14 
Маркет D-15 
Маркет D-16 
Маркет D-17 
Маркет D-18 
Маркет D-19 
Маркет D-20 
Маркет D-21 
Маркет D-22 
Маркет D-23 
Маркет D-24 
Маркет D-25 
Маркет D-26 
Маркет D-28 
Маркет D-29 
Маркет D-30 
Маркет D-31 
Маркет D-34 
Маркет D-37 
Маркет Dz-01 
Маркет Dz-02 
Маркет Dz-03 
Маркет Dz-04 
Маркет Dz-05 
Маркет Dz-06 
Маркет Dz-07 
Маркет Dz-08 
Маркет Dz-10 
Маркет Dz-11 
Маркет Dz-12 
Маркет K-01 
Маркет K-02 
Маркет K-03 
Маркет K-04 
Маркет K-05 
Маркет K-06 
Маркет K-07 
Маркет K-08 
Маркет K-09 
Маркет K-10 
Маркет K-11 
Маркет N-01 
Маркет N-02 
Маркет N-03 
Маркет N-09 
Маркет Nm-01 
Маркет Nm-02 
Маркет Nm-04 
Маркет S-01 
Маркет S-02 
Маркет S-03 
Маркет S-06 
Маркет S-07 
Маркет S-08 
Маркет S-09 
Маркет S-10 
Маркет S-12 
Маркет S-13 
Маркет S-14 
Маркет S-15 
Маркет S-16 
Маркет S-17 
Маркет S-18 
Маркет S-20 
Маркет S-22 
Маркет S-23 
Маркет S-27 
Маркет S-29 
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
Маркет А-26 
Маркет А-27 
Маркет А-28 
Маркет А-29 
Маркет А-30 
Маркет А-31 
Маркет А-32 
Маркет А-34 
Маркет А-35 
Маркет А-36 
Маркет А-37 
Маркет А-38 
Маркет А-41 
Маркет А-42 
Маркет А-43 
Маркет А-44 
Маркет А-45 
Маркет А-46 
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
Маркет М-150 
Маркет М-151 
Маркет М-153 
Маркет М-156 
Маркет М-157 
Маркет М-158  
Маркет М-159 
Маркет М-16 
Маркет М-160 
Маркет М-161 
Маркет М-162 
Маркет М-163 
Маркет М-164 
Маркет М-165 
Маркет М-166 
Маркет М-167 
Маркет М-168 
Маркет М-169 
Маркет М-170 
Маркет М-173 
Маркет М-175 
Маркет М-176 
Маркет М-178 
Маркет М-179 
Маркет М-18 
Маркет М-180 
Маркет М-181  
Маркет М-182 
Маркет М-183 
Маркет М-184 
Маркет М-185 
Маркет М-187 
Маркет М-188 
Маркет М-19 
Маркет М-190 
Маркет М-191 
Маркет М-193 
Маркет М-194 
Маркет М-195 
Маркет М-196 
Маркет М-197 
Маркет М-198 
Маркет М-20 
Маркет М-200 
Маркет М-201 
Маркет М-202 
Маркет М-207 
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
Маркет С-23 
Маркет С-24 
Маркет С-25 
Маркет С-26 
Маркет С-27 
Маркет С-28 
Маркет С-29 
Маркет С-30 
Маркет С-31
"""

MARKETS = [line.strip() for line in MARKETS_TEXT.splitlines() if line.strip()]

# 🔹 РАСПРЕДЕЛЕНИЕ МАРКЕТОВ ПО ТЕРРИТОРИАЛЬНЫМ МЕНЕДЖЕРАМ
# TODO: заполни реальными ТМ и их магазинами
TERRITORIAL_MANAGERS = {
    "tm1": {
        "title": "Ахматов Мухаммаджон",
        "markets": [
           "Маркет М-40 ",
            "Маркет М-56 ",
            "Маркет М-57 ",
            "Маркет М-114 ",
            "Маркет М-03 ",
            "Маркет М-88 ",
            "Маркет М-105 ",
        ],
    },
    "tm2": {
        "title": "Ирисмухамедова Баян",
        "markets": [
           "Маркет М-116 ",
            "Маркет М-123 ",
            "Маркет М-140 ",
            "Маркет М-175 ",
            "Маркет М-180 ",
            "Маркет М-19 ",
            "Маркет М-191 ",
            "Маркет М-28 ",
            "Маркет М-32 ",
            "Маркет М-42 ",
            "Маркет М-55 ",
            "Маркет М-71 ",
            "Маркет М-86 ",
            "Маркет М-99 ",
        ],
    },
    # добавь сюда остальных ТМ по аналогии
    "tm3": {
        "title": "Курбонов Тимур",
        "markets": [
           "Маркет М-104 ",
            "Маркет М-12 ",
            "Маркет М-120 ",
            "Маркет М-128 ",
            "Маркет М-13 ",
            "Маркет М-176 ",
            "Маркет М-18 ",
            "Маркет М-22 ",
            "Маркет М-50 ",
            "Маркет М-63 ",
            "Маркет М-70 ",
            "Маркет М-73 ",
            "Маркет М-81 ",
            "Маркет М-87 ",
        ],
    },
    "tm4": {
        "title": "Махсетов Бобур",
        "markets": [
           "Маркет М-46 ",
            "Маркет М-182 ",
            "Маркет М-207 ",
            "Маркет М-25 ",
            "Маркет М-65 ",
            "Маркет М-85 ",
            "Маркет М-95 ",
        ],
    },
    "tm5": {
        "title": "Рахматова Нилюфар",
        "markets": [
           "Маркет М-118 ",
            "Маркет М-124 ",
            "Маркет М-14 ",
            "Маркет М-141 ",
            "Маркет М-148 ",
            "Маркет М-149 ",
            "Маркет М-169 ",
            "Маркет М-196 ",
            "Маркет М-37 ",
            "Маркет М-48 ",
            "Маркет М-89 ",
        ],
    },
    "tm6": {
        "title": "Хакимов Сарвар",
        "markets": [
        "Маркет М-08 ",
        "Маркет М-142 ",
        "Маркет М-146 ",
        "Маркет М-34 ",
        "Маркет М-47 ",
        "Маркет М-58 ",
        "Маркет С-23 ",
        "Маркет С-24 ",
        "Маркет М-80 ",
        ],
    },
    "tm7": {
        "title": "Шаумаров Отабек",
        "markets": [
            "Маркет М-127 ",
            "Маркет М-134 ",
            "Маркет М-159 ",
            "Маркет М-166 ",
            "Маркет М-74 ",
            "Маркет М-76 ",
            "Маркет М-161 ",
            "Маркет М-197 ",
            "Маркет М-162 ",
            "Маркет М-143 ",
            "Маркет М-06 ",

        ],
    },
    "tm8": {
        "title": "Шодмонов Комил",
        "markets": [
           "Маркет М-04 ",
            "Маркет М-05 ",
            "Маркет М-111 ",
            "Маркет М-139 ",
            "Маркет М-147 ",
            "Маркет М-150 ",
            "Маркет М-158  ",
            "Маркет М-181  ",
            "Маркет М-21 ",
            "Маркет М-45 ",
            "Маркет М-49 ",
            "Маркет М-61 ",
            "Маркет М-79 ",
        ],
    },
    "tm9": {
        "title": "Эгамбердиев Алохон",
        "markets": [
            "Маркет D-30 ",
            "Маркет М-102 ",
            "Маркет М-103 ",
            "Маркет М-126 ",
            "Маркет М-170 ",
            "Маркет С-16Т ",
            "Маркет С-17 ",
            "Маркет С-19 ",
            "Маркет С-20 ",
            "Маркет С-28 ",
        ],
    },
    "tm10": {
        "title": "Эгамбердиев Санжар",
        "markets": [
            "Маркет М-107 ",
            "Маркет М-109 ",
            "Маркет М-137 ",
            "Маркет М-144 ",
            "Маркет М-151 ",
            "Маркет М-160 ",
            "Маркет М-165 ",
            "Маркет М-168 ",
            "Маркет М-193 ",
            "Маркет М-194 ",
            "Маркет М-202 ",
            "Маркет М-53 ",
            "Маркет М-64 ",
            "Маркет М-66 ",
            "Маркет М-72 ",
            "Маркет М-75 ",
        ],
    },
    "tm11": {
        "title": "Абдуллаев Нозимбек",
        "markets": [
           "Маркет N-01 ",
            "Маркет N-02 ",
            "Маркет N-03 ",
            "Маркет N-09 ",
        ],
    },
    "tm12": {
        "title": "Ахатов Ослонбек",
        "markets": [
          "Маркет Dz-01 ",
        "Маркет Dz-02 ",
        "Маркет Dz-03 ",
        "Маркет Dz-04 ",
        "Маркет Dz-05 ",
        "Маркет Dz-06 ",
        "Маркет Dz-07 ",
        "Маркет Dz-08 ",
        "Маркет Dz-10 ",
        "Маркет Dz-11 ",
        "Маркет Dz-12 ",

        ],
    },
    "tm13": {
        "title": "Бекмухамедов Ойбек",
        "markets": [
           "Маркет S-09 ",
            "Маркет S-13 ",
            "Маркет S-14 ",
            "Маркет S-17 ",
            "Маркет S-22 ",
            "Маркет S-27 ",

        ],
    },
    "tm14": {
        "title": " Давронов Садриддин",
        "markets": [
           "Маркет S-01 ",
            "Маркет S-03 ",
            "Маркет S-06 ",
            "Маркет S-08 ",
            "Маркет S-12 ",
            "Маркет S-16 ",
            "Маркет S-20 ",
        ],
    },
    "tm15": {
        "title": "Салимов Карим",
        "markets": [
           "Маркет S-02 ",
            "Маркет S-07 ",
            "Маркет S-10 ",
            "Маркет S-15 ",
            "Маркет S-18 ",
            "Маркет S-23 ",
            "Маркет S-29 ",
        ],
    },
    "tm16": {
        "title": "Абдималиков Шахзод",
        "markets": [
            "Маркет С-01 ",
            "Маркет С-03 ",
            "Маркет С-04 ",
            "Маркет С-05 ",
            "Маркет С-06 ",
            "Маркет С-10 ",
            "Маркет С-13 ",
            "Маркет С-14 ",
            "Маркет С-15 ",
            "Маркет С-21 ",
            "Маркет С-22 ",


        ],
    },
    "tm17": {
        "title": "Ахунов Муххамаджон",
        "markets": [
            "Маркет М-44 ",
            "Маркет М-112 ",
            "Маркет М-59 ",
            "Маркет М-125 ",
            "Маркет М-130 ",
            "Маркет М-190 ",
            "Маркет М-198 ",
            "Маркет М-20 ",
            "Маркет М-26 ",
            "Маркет М-27 ",
            "Маркет М-35 ",
        ],
    },
    "tm18": {
        "title": "Калашников Денис",
        "markets": [
           "Маркет М-110 ",
            "Маркет М-16 ",
            "Маркет М-164 ",
            "Маркет М-179 ",
            "Маркет М-23 ",
            "Маркет М-31 ",
            "Маркет М-41 ",
            "Маркет М-60 ",
            "Маркет М-92 ",
            "Маркет М-82 ",
            "Маркет М-115 ",
            "Маркет М-101 ",
            "Маркет М-43 ",
        ],
    },
    "tm19": {
        "title": "Абдуалимов Нурмухаммад",
        "markets": [
          "Маркет М-201 ",
        "Маркет М-131 ",
        "Маркет М-156 ",
        "Маркет М-30 ",
        "Маркет М-98 ",
        ],
    },
    "tm20": {
        "title": "Каримов Зиед",
        "markets": [
         "Маркет М-167 ",
        "Маркет М-93 ",
        "Маркет С-07 ",
        "Маркет С-08 ",
        "Маркет С-09 ",
        "Маркет С-11 ",
        "Маркет С-12 ",
        "Маркет С-26 ",
        "Маркет С-27 ",
        "Маркет С-29 ",
        "Маркет С-30 ",
        "Маркет С-31 ",
        ],
    },
    "tm21": {
        "title": "Кодыров Хумоюн",
        "markets": [
              "Маркет М-07 ",
            "Маркет М-113 ",
            "Маркет М-117 ",
            "Маркет М-187 ",
            "Маркет М-188 ",
            "Маркет М-78 ",
            "Маркет С-25 ",

        ],
    },
    "tm22": {
        "title": "Сейтмеметов Эскендер",
        "markets": [
         "Маркет М-02 ",
        "Маркет М-11 ",
        "Маркет М-119 ",
        "Маркет М-135 ",
        "Маркет М-153 ",
        "Маркет М-157 ",
        "Маркет М-178 ",
        "Маркет М-51 ",
        "Маркет М-62 ",
        "Маркет М-84 ",
        "Маркет М-90 ",
        "Маркет М-96 ",
        "Маркет С-18 ",

        ],
    },
    "tm23": {
        "title": "Серикбаев Айдос",
        "markets": [
         "Маркет K-01 ",
        "Маркет K-02 ",
        "Маркет K-03 ",
        "Маркет K-04 ",
        "Маркет K-05 ",
        "Маркет K-06 ",
        "Маркет K-07 ",
        "Маркет K-08 ",
        "Маркет K-09 ",
        "Маркет K-10 ",
        "Маркет K-11 ",
        "Маркет М-97 ",

        ],
    },
    "tm24": {
        "title": "Юлдашев Олим",
        "markets": [
         "Маркет М-108 ",
        "Маркет М-145 ",
        "Маркет М-163 ",
        "Маркет М-183 ",
        "Маркет М-184 ",
        "Маркет М-195 ",
        "Маркет М-33 ",
        "Маркет М-36 ",
        "Маркет М-68 ",
        "Маркет М-69 ",
        "Маркет М-83 ",
        ],
    },
    "tm25": {
        "title": "Маджидов Хумоюн",
        "markets": [
         "Маркет М-106 ",
        "Маркет М-121 ",
        "Маркет М-132 ",
        "Маркет М-133 ",
        "Маркет М-185 ",
        "Маркет М-67 ",
        "Маркет М-200 ",
        "Маркет М-173 ",
        "Маркет М-91 ",
        "Маркет М-122 ",
        "Маркет М-129 ",
        ],
    },
    "tm26": {
        "title": "Абдурахимов Гайрат",
        "markets": [
          "Маркет D-06 ",
            "Маркет D-10 ",
            "Маркет D-11 ",
            "Маркет D-12 ",
            "Маркет D-13 ",
            "Маркет D-14 ",
            "Маркет D-19 ",
            "Маркет D-22 ",
            "Маркет D-23 ",
            "Маркет D-24 ",
            "Маркет D-25 ",
            "Маркет D-28 ",

        ],
    },

    "tm27": {
        "title": "Акимова Диляра",
        "markets": [
          "Маркет А-01 ",
            "Маркет А-02 ",
            "Маркет А-03 ",
            "Маркет А-04 ",
            "Маркет А-05 ",
            "Маркет А-06 ",
            "Маркет А-09 ",
            "Маркет А-10 ",
            "Маркет А-12 ",
            "Маркет А-13 ",
            "Маркет А-14 ",
            "Маркет А-16 ",
            "Маркет А-17 ",
            "Маркет А-19 ",
            "Маркет А-21 ",
            "Маркет А-22 ",
            "Маркет А-41 ",
            "Маркет А-42 ",
        ],
    },

    "tm28": {
        "title": "Алламов Юнус",
        "markets": [
          "Маркет Nm-01 ",
            "Маркет Nm-02 ",
            "Маркет Nm-04 ",
        ],
    },

    "tm29": {
        "title": "Отбосаров Бахром",
        "markets": [
          "Маркет А-07 ",
        "Маркет А-18 ",
        "Маркет А-20 ",
        "Маркет А-23 ",
        "Маркет А-25 ",
        "Маркет А-27 ",
        "Маркет А-31 ",
        "Маркет А-35 ",
        "Маркет А-36 ",
        "Маркет А-37 ",
        "Маркет А-38 ",
        "Маркет А-46 ",
        ],
    },

    "tm30": {
        "title": "Рахмадов Искандар",
        "markets": [
         "Маркет D-01 ",
        "Маркет D-02 ",
        "Маркет D-03 ",
        "Маркет D-04 ",
        "Маркет D-05 ",
        "Маркет D-07 ",
        "Маркет D-08 ",
        "Маркет D-09 ",
        "Маркет D-15 ",
        "Маркет D-16 ",
        "Маркет D-17 ",
        "Маркет D-20 ",
        "Маркет D-21 ",
        "Маркет D-29 ",
        "Маркет D-31 ",
        "Маркет D-34 ",
        "Маркет D-37 ",
        ],
    },

    "tm31": {
        "title": "Хакимов Азизбек",
        "markets": [
        "Маркет B-01 ",
        "Маркет B-02 ",
        "Маркет B-03 ",
        "Маркет B-04 ",
        "Маркет B-05 ",
        "Маркет B-06 ",
        "Маркет B-07 ",
        "Маркет B-08 ",
        "Маркет B-09 ",
        "Маркет B-10 ",
        "Маркет B-11 ",
        "Маркет D-18 ",
        "Маркет D-26 ",
        ],
    },

       "tm32": {
        "title": "Эрниезов Шохзод",
        "markets": [
        "Маркет А-08 ",
        "Маркет А-11 ",
        "Маркет А-15 ",
        "Маркет А-24 ",
        "Маркет А-26 ",
        "Маркет А-28 ",
        "Маркет А-29 ",
        "Маркет А-30 ",
        "Маркет А-32 ",
        "Маркет А-34 ",
        "Маркет А-43 ",
        "Маркет А-44 ",
        "Маркет А-45 ",

        ],
    }, 
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

@dp.message_handler(commands=["not_sent"])
async def cmd_not_sent(message: types.Message):
    """
    /not_sent — показать только те маркеты, которые НЕ отправили отчёт за сегодня.
    Сначала по территориальным менеджерам (если TERRITORIAL_MANAGERS заполнен),
    затем — магазины без привязки к ТМ.
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    c = conn.cursor()
    # Берём все отчёты за сегодня и по каждому маркету оставляем последний (по id)
    c.execute(
        """
        SELECT market, id
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        ORDER BY id
        """
    )
    rows = c.fetchall()

    last_by_market = {}
    for market, _id in rows:
        last_by_market[market] = _id

    lines = []

    # --- 1) Группы по территориальным менеджерам ---
    markets_in_tm = set()
    for tm_key, info in TERRITORIAL_MANAGERS.items():
        title = info["title"]
        tm_markets = info["markets"]
        markets_in_tm.update(tm_markets)

        tm_not_sent = []
        for m in tm_markets:
            if m not in last_by_market:
                code = m.replace("Маркет", "").strip()
                tm_not_sent.append(f"❌ {code}")

        if tm_not_sent:
            block = f"{title}:\n" + "\n".join(tm_not_sent)
            lines.append(block)

    # --- 2) Магазины, которые не попали ни в одного ТМ, но есть в MARKETS ---
    other_not_sent = []
    for m in MARKETS:
        if m not in markets_in_tm and m not in last_by_market:
            code = m.replace("Маркет", "").strip()
            other_not_sent.append(f"❌ {code}")

    if other_not_sent:
        block = "Без ТМ:\n" + "\n".join(other_not_sent)
        lines.append(block)

    if not lines:
        await message.reply("Все маркеты отправили отчёт за сегодня (UTC+5) ✅")
        return

    text = "Маркеты без отчёта за сегодня (UTC+5):\n\n" + "\n\n".join(lines)
    await message.reply(text)

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
    
@dp.message_handler(commands=["tm_done"])
async def cmd_tm_done(message: types.Message):
    """
    /tm_done — показать по территориальным менеджерам только те маркеты,
    которые ОТПРАВИЛИ отчёт за сегодня (UTC+5).
    Отдельно показываем магазины без привязки к ТМ.
    """
    if not is_admin(message.from_user):
        await message.reply("У вас нет прав для этой команды.")
        return

    c = conn.cursor()
    # Берём все отчёты за сегодня, по каждому магазину оставляем последний (по id)
    c.execute(
        """
        SELECT market, username, full_name, datetime(created_at, '+5 hours') AS created_at_uz, id
        FROM reports
        WHERE date(datetime(created_at, '+5 hours')) = date('now', '+5 hours')
        ORDER BY id
        """
    )
    rows = c.fetchall()

    last_by_market = {}
    for market, username, full_name, created_at_uz, _id in rows:
        last_by_market[market] = (username, full_name, created_at_uz)

    if not last_by_market:
        await message.reply("Сегодня ещё никто не отправил отчёт.")
        return

    lines = []

    # --- 1) Маркеты по территориальным менеджерам ---
    markets_in_tm = set()
    for tm_key, info in TERRITORIAL_MANAGERS.items():
        title = info["title"]
        tm_markets = info["markets"]
        markets_in_tm.update(tm_markets)

        tm_done = []
        for m in tm_markets:
            if m in last_by_market:
                username, full_name, created_at_uz = last_by_market[m]
                code = m.replace("Маркет", "").strip()

                if username and full_name:
                    sender = f"@{username} ({full_name})"
                elif username:
                    sender = f"@{username}"
                elif full_name:
                    sender = full_name
                else:
                    sender = "неизвестно"

                tm_done.append(f"✅ {code} — {sender}")

        if tm_done:
            block = f"{title}:\n" + "\n".join(tm_done)
            lines.append(block)

    # --- 2) Маркеты без ТМ, но с отчётом ---
    other_done = []
    for m in MARKETS:
        if m not in markets_in_tm and m in last_by_market:
            username, full_name, created_at_uz = last_by_market[m]
            code = m.replace("Маркет", "").strip()

            if username and full_name:
                sender = f"@{username} ({full_name})"
            elif username:
                sender = f"@{username}"
            elif full_name:
                sender = full_name
            else:
                sender = "неизвестно"

            other_done.append(f"✅ {code} — {sender}")

    if other_done:
        block = "Без ТМ:\n" + "\n".join(other_done)
        lines.append(block)

    if not lines:
        await message.reply("По ТМ пока нет ни одного отправленного отчёта за сегодня.")
        return

    text = "Маркеты, отправившие отчёт за сегодня (UTC+5):\n\n" + "\n\n".join(lines)
    await send_long_message(message, text)


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

    await send_long_message(message, text)



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
        # админу в группе можем подсказать, что бот работает только в личке
        await message.reply(
            "Бот принимает отчёты только в личных сообщениях.\n"
            "Пожалуйста, отправьте фото боту в личку."
        )
        return

    user_id = message.from_user.id
    lang = get_lang(user_id)

    # ⏰ ОГРАНИЧЕНИЕ ВРЕМЕНИ ДЛЯ НЕ-АДМИНОВ: 12:00–13:00 UTC+5
    if not is_admin(message.from_user):
        # текущее время в UTC+5
        now_utc = datetime.utcnow()
        now_utc5 = now_utc + timedelta(hours=5)
        hour = now_utc5.hour

        # принимаем только с 12:00 до 12:59 (UTC+5)
        if not (12 <= hour < 14):
            if lang == "uz":
                txt = (
                    "Foto hisobot faqat soat 12:00 dan 13:00 gacha qabul qilinadi (UTC+5).\n"
                    "Iltimos, shu vaqt oralig'ida yuboring."
                )
            else:
                txt = (
                    "Фотоотчёты принимаются только с 12:00 до 13:00 (UTC+5).\n"
                    "Пожалуйста, отправьте фото в это время."
                )
            await message.reply(txt)
            return

    # если время подходит или это админ — продолжаем обычный сценарий
    photo = message.photo[-1]
    file_id = photo.file_id

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
        if lang == "уз":
            allowed = ["kam", "yetarli", "ko'p"]
        elif lang == "uz":
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

        # формируем строку с отправителем
        u = message.from_user
        uname = u.username
        fname = u.full_name

        if uname and fname:
            sender_line = f"Отправил: @{uname} ({fname})"
        elif uname:
            sender_line = f"Отправил: @{uname}"
        elif fname:
            sender_line = f"Отправил: {fname}"
        else:
            sender_line = "Отправил: (неизвестно)"

        raw_text = (
            f"#Магазин: {market_code}\n"
            f"{sender_line}\n"
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
        "Бот запускается (SQLite, RU/UZ, админы по user_id, роли админ/суперадмин, ТМ-отчёты)..."
    )
    executor.start_polling(dp, skip_updates=True)
