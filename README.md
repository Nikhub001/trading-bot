# Trading Bot — Telegram Signals → Gate.io Futures

Читает сигналы из Telegram каналов и автоматически открывает сделки на Gate.io Futures.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

**Первый запуск:** Telethon попросит номер телефона и код из Telegram.
Сессия сохраняется в `trading_bot.session` — повторная авторизация не нужна.

## Конфигурация (.env)

| Параметр | Описание |
|---|---|
| TELEGRAM_API_ID | ID приложения с my.telegram.org |
| TELEGRAM_API_HASH | Hash приложения |
| TELEGRAM_CHANNELS | Каналы через запятую (ссылки или @username) |
| GATE_API_KEY | API ключ Gate.io |
| GATE_API_SECRET | API секрет Gate.io |
| GEMINI_API_KEY | Ключ Google Gemini |
| RISK_PERCENT | % депозита на сделку (default: 15) |
| LEVERAGE | Плечо (default: 10) |
| DEFAULT_STOP_PERCENT | Стоп если нет в сигнале, % (default: 2) |
| DEFAULT_TP_PERCENT | Тейк если нет в сигнале, % (default: 4) |

## Логи

Логи пишутся в `logs/bot.log` и в консоль.

---

## Support the Author

If you find this project useful, support with crypto:

**Network: Polygon (MATIC)**
**Address:** `0xd2903900eb4755fEFa55E07767AC21A49a125813`

> ⚠️ Send only on **Polygon network** — other networks will result in lost funds!

[![Donate on Polygon](https://img.shields.io/badge/Donate-Polygon%20Network-8247E5?style=for-the-badge&logo=ethereum)](https://polygonscan.com/address/0xd2903900eb4755fEFa55E07767AC21A49a125813)