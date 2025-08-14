import os
import asyncio
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from moysklad_client import MoySkladClient


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MOYSKLAD_TOKEN = os.getenv("MOYSKLAD_TOKEN")
MOYSKLAD_LOGIN = os.getenv("MOYSKLAD_LOGIN")
MOYSKLAD_PASSWORD = os.getenv("MOYSKLAD_PASSWORD")


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user_first_name = update.effective_user.first_name if update.effective_user else "друг"
	await update.message.reply_text(f"Привет, {user_first_name}! Я готов.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text("Доступные команды:\n/start — приветствие\n/help — помощь\n/ms_products <поиск> — поиск товаров в МойСклад\n/ms_profit YYYY-MM-DD YYYY-MM-DD [папка] — отчёт прибыльности")


async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.message.text:
		await update.message.reply_text(update.message.text)


async def ms_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	query = " ".join(context.args) if context.args else None
	try:
		async with MoySkladClient(
			token=MOYSKLAD_TOKEN,
			login=MOYSKLAD_LOGIN,
			password=MOYSKLAD_PASSWORD,
		) as client:
			data = await client.list_products(search=query, limit=5)
			rows = data.get("rows") or data.get("items") or []
			if not rows:
				await update.message.reply_text("Ничего не найдено в МойСклад.")
				return
			lines = []
			for idx, item in enumerate(rows, start=1):
				name = item.get("name") or "(без названия)"
				code = item.get("code") or item.get("article") or ""
				line = f"{idx}. {name}"
				if code:
					line += f" (код: {code})"
				lines.append(line)
			text = "\n".join(lines)
			await update.message.reply_text(text)
	except Exception as exc:
		await update.message.reply_text(f"Ошибка при обращении к МойСклад: {exc}")


async def ms_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Прибыльность по товарам за период. Пример:
	/ms_profit 2024-08-01 2024-08-31 Электроника
	Если название папки не указано, будет без фильтра по папке."""
	args = context.args
	if len(args) < 2:
		await update.message.reply_text(
			"Использование: /ms_profit YYYY-MM-DD YYYY-MM-DD [ПапкаНоменклатуры]"
		)
		return

	moment_from = f"{args[0]} 00:00:00"
	moment_to = f"{args[1]} 23:59:59"
	folder_name = " ".join(args[2:]) if len(args) > 2 else None

	try:
		async with MoySkladClient(
			token=MOYSKLAD_TOKEN,
			login=MOYSKLAD_LOGIN,
			password=MOYSKLAD_PASSWORD,
		) as client:
			folder_id = None
			if folder_name:
				folder = await client.find_product_folder(folder_name)
				folder_id = folder.get("id") if folder else None

			data = await client.report_profit_by_assortment(
				moment_from=moment_from,
				moment_to=moment_to,
				product_folder_id=folder_id,
				limit=20,
			)
			rows = data.get("rows") or []
			if not rows:
				await update.message.reply_text("Данных по прибыльности не найдено.")
				return

			lines = []
			for idx, item in enumerate(rows, start=1):
				assort = item.get("assortment", {})
				name = assort.get("name") or "(без названия)"
				profit = item.get("profit") or 0
				revenue = item.get("sales") or 0
				cost = item.get("cost") or 0
				lines.append(f"{idx}. {name} — прибыль: {profit:.2f}, выручка: {revenue:.2f}, себестоимость: {cost:.2f}")

			text = "\n".join(lines[:10])
			await update.message.reply_text(text)
	except Exception as exc:
		await update.message.reply_text(f"Ошибка отчёта прибыльности: {exc}")


async def main() -> None:
	if not BOT_TOKEN:
		logger.error(
			"Не найден BOT_TOKEN. Создайте файл .env с BOT_TOKEN=... или задайте переменную окружения."
		)
		return

	# Проверяем наличие данных для МойСклад
	if not (MOYSKLAD_TOKEN or (MOYSKLAD_LOGIN and MOYSKLAD_PASSWORD)):
		logger.warning(
			"Не найдены данные для МойСклад. Команды /ms_products и /ms_profit будут недоступны."
		)

	application = ApplicationBuilder().token(BOT_TOKEN).build()

	application.add_handler(CommandHandler("start", start))
	application.add_handler(CommandHandler("help", help_command))
	application.add_handler(CommandHandler("ms_products", ms_products))
	application.add_handler(CommandHandler("ms_profit", ms_profit))
	application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_text))

	logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
	await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except (KeyboardInterrupt, SystemExit):
		logger.info("Бот остановлен.")


