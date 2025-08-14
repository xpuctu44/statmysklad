import base64
from typing import Any, Dict, Optional, List, Tuple

import httpx


API_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"


class MoySkladClient:
	"""Простой async-клиент для МойСклад JSON API.

	Поддерживает аутентификацию:
	- через токен (MOYSKLAD_TOKEN) — заголовок Bearer
	- через логин/пароль (MOYSKLAD_LOGIN/MOYSKLAD_PASSWORD) — Basic Auth
	"""

	def __init__(
		self,
		token: Optional[str] = None,
		login: Optional[str] = None,
		password: Optional[str] = None,
		timeout_seconds: float = 20.0,
	):
		self._token = token
		self._login = login
		self._password = password
		self._timeout = httpx.Timeout(timeout_seconds)
		self._client: Optional[httpx.AsyncClient] = None

	async def __aenter__(self) -> "MoySkladClient":
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"User-Agent": "tgbot-moysklad/1.0",
			"Accept-Encoding": "gzip",
		}

		if self._token:
			headers["Authorization"] = f"Bearer {self._token}"
			self._client = httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=self._timeout)
		else:
			# Basic Auth через заголовок Authorization, чтобы не хранить auth-объект
			if not (self._login and self._password):
				raise ValueError("Нужен либо MOYSKLAD_TOKEN, либо пара MOYSKLAD_LOGIN/MOYSKLAD_PASSWORD")
			encoded = base64.b64encode(f"{self._login}:{self._password}".encode()).decode()
			headers["Authorization"] = f"Basic {encoded}"
			self._client = httpx.AsyncClient(base_url=API_BASE_URL, headers=headers, timeout=self._timeout)

		return self

	async def __aexit__(self, exc_type, exc, tb) -> None:
		if self._client:
			await self._client.aclose()
			self._client = None

	async def list_products(self, search: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
		"""Возвращает список товаров. Использует параметр `search` для полнотекстового поиска."""
		if not self._client:
			raise RuntimeError("Клиент не инициализирован. Используйте 'async with MoySkladClient(...)'.")
		params: Dict[str, Any] = {"limit": limit}
		if search:
			params["search"] = search
		resp = await self._client.get("/entity/product", params=params)
		resp.raise_for_status()
		return resp.json()

	async def find_product_folder(self, name: str) -> Optional[Dict[str, Any]]:
		"""Ищет папку номенклатуры по точному имени."""
		if not self._client:
			raise RuntimeError("Клиент не инициализирован. Используйте 'async with MoySkladClient(...)'.")
		params = {"filter": f"name={name}", "limit": 1}
		resp = await self._client.get("/entity/productfolder", params=params)
		resp.raise_for_status()
		data = resp.json()
		rows: List[Dict[str, Any]] = data.get("rows", []) if isinstance(data, dict) else []
		return rows[0] if rows else None

	async def report_profit_by_assortment(
		self,
		moment_from: str,
		moment_to: str,
		product_folder_id: Optional[str] = None,
		limit: int = 100,
	) -> Dict[str, Any]:
		"""Отчёт по прибыльности, группировка по номенклатуре.

		Параметры дат — строки в формате ISO, например: "2024-08-01 00:00:00".
		Если задан `product_folder_id`, добавляется фильтр по папке номенклатуры.
		"""
		if not self._client:
			raise RuntimeError("Клиент не инициализирован. Используйте 'async with MoySkladClient(...)'.")

		params: List[Tuple[str, str]] = [
			("momentFrom", moment_from),
			("momentTo", moment_to),
			("limit", str(limit)),
		]
		if product_folder_id:
			folder_href = f"{API_BASE_URL}/entity/productfolder/{product_folder_id}"
			params.append(("filter", f"productFolder={folder_href}"))

		resp = await self._client.get("/report/profit/byassortment", params=params)
		resp.raise_for_status()
		return resp.json()


