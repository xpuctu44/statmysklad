# Telegram Bot с интеграцией МойСклад

Бот для Telegram с интеграцией API МойСклад для получения отчетов по товарам и прибыльности.

## Возможности

- **/start** — приветствие
- **/help** — список команд
- **/ms_products <поиск>** — поиск товаров в МойСклад
- **/ms_profit YYYY-MM-DD YYYY-MM-DD [папка]** — отчёт прибыльности за период

## Быстрый запуск на GitHub Actions

### 1. Настройка Secrets

В репозитории GitHub перейдите в **Settings → Secrets and variables → Actions** и добавьте:

- `BOT_TOKEN` — токен вашего Telegram бота (от @BotFather)
- `MOYSKLAD_LOGIN` — логин для МойСклад
- `MOYSKLAD_PASSWORD` — пароль для МойСклад

### 2. Запуск бота

После настройки secrets:
1. Перейдите в **Actions** в вашем репозитории
2. Выберите workflow "Telegram Bot"
3. Нажмите **Run workflow**

### 3. Локальный запуск

```bash
# Клонируйте репозиторий
git clone https://github.com/xpuctu44/statmysklad.git
cd statmysklad

# Создайте .env файл
cp env.sample .env
# Отредактируйте .env с вашими данными

# Установите зависимости
pip install -r requirements.txt

# Запустите бота
python bot.py
```

## Переменные окружения

Файл `.env`:
```
BOT_TOKEN=ваш_токен_бота
MOYSKLAD_LOGIN=ваш_логин@example.com
MOYSKLAD_PASSWORD=ваш_пароль
```

## Примеры использования

```
/ms_products айфон
/ms_profit 2024-08-01 2024-08-31 Электроника
```

## Технологии

- Python 3.11+
- python-telegram-bot 21.6
- httpx для API МойСклад
- GitHub Actions для автоматизации



