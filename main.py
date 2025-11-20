
# -*- coding: utf-8 -*-
import logging
from aiogram import Bot, Dispatcher, types
from datetime import datetime

# 🔐 ТВОЙ ТОКЕН БОТА
API_TOKEN = "8502500500:AAHw3Nvkefvbff27oeuwjdPrF-lXRxboiKQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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
