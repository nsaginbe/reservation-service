import re
from datetime import date
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import urlencode

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from common import conf

PROPERTY_ID = "e6b334f6-caac-4dd8-8e6f-b8bfa578a484"
BASE_URL = f"https://reservationsteps.ru/rooms/index/{PROPERTY_ID}"


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def build_search_url(dfrom: date, dto: date, adults: int, children: str) -> str:
    params = {
        "dfrom": dfrom.strftime("%d-%m-%Y"),
        "dto": dto.strftime("%d-%m-%Y"),
        "adults": adults,
        "children": children,
    }
    return f"{BASE_URL}?{urlencode(params)}"


async def fetch_rooms(
    dfrom: date,
    dto: date,
    adults: int,
    children: str,
    timeout_ms: int = 10000,
) -> Dict[str, Any]:
    url = build_search_url(dfrom=dfrom, dto=dto, adults=adults, children=children)
    rooms_payload: List[Dict[str, Any]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=conf.HEADLESS,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(timeout_ms)
        page.set_default_navigation_timeout(timeout_ms)

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(".room.room-shown", timeout=timeout_ms)
            await page.wait_for_timeout(1000)
        except PlaywrightTimeoutError:
            await browser.close()
            raise RuntimeError("Timeout while loading reservation page")

        room_cards = page.locator(".room.room-shown")
        room_count = await room_cards.count()

        for idx in range(room_count):
            card = room_cards.nth(idx)

            # Cards with this section represent unavailable or invalid options.
            if await card.locator(".category-action .tariff__nodates").count():
                continue

            title_locator = card.locator(".room__titleText").first
            title = (
                _normalize_text(await title_locator.inner_text())
                if await title_locator.count()
                else ""
            )
            if not title:
                continue

            plans = card.locator(".tariff.plan_row[data-available-for-guests='1']")
            if await plans.count() == 0:
                plans = card.locator(".tariff.plan_row")

            offers: List[Dict[str, Any]] = []
            seen_offers: Set[Tuple[str, int]] = set()

            for pidx in range(await plans.count()):
                plan = plans.nth(pidx)

                price_locator = plan.locator("span.tariff__price-value[data-tariff-price]").first
                if await price_locator.count() == 0:
                    continue

                price_raw = await price_locator.get_attribute("data-tariff-price")
                try:
                    price_value = int(price_raw) if price_raw else None
                except ValueError:
                    price_value = None
                if price_value is None:
                    continue

                meal_locator = plan.locator(
                    ".tariff__descriptionFood span:not(.tariff__modal-icon)"
                ).first
                meal = (
                    _normalize_text(await meal_locator.inner_text())
                    if await meal_locator.count()
                    else None
                )

                dedupe_key = (meal or "", price_value)
                if dedupe_key in seen_offers:
                    continue
                seen_offers.add(dedupe_key)

                offers.append(
                    {
                        "meal": meal,
                        "price": price_value,
                    }
                )

            if offers:
                rooms_payload.append({"name": title, "offers": offers})

        await browser.close()

    return {
        "dfrom": dfrom.strftime("%d-%m-%Y"),
        "dto": dto.strftime("%d-%m-%Y"),
        "adults": adults,
        "children": children,
        "rooms": rooms_payload,
    }
