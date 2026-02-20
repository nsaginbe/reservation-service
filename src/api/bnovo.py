import contextlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DATE_FORMAT = "%d.%m.%Y"


@dataclass
class BookingSummary:
    booking_number: Optional[str]
    guest_name: Optional[str]
    balance: Optional[str]
    status: Optional[str]
    grid_column_start: Optional[int]
    grid_column_end: Optional[int]
    check_in: Optional[str] = None
    check_out: Optional[str] = None


@dataclass
class RoomData:
    room_name: str
    bookings: List[BookingSummary]


@dataclass
class ReferencePoint:
    date: Optional[datetime] = None
    column: Optional[int] = None


def parse_grid_column(style: str) -> Tuple[Optional[int], Optional[int]]:
    if not style:
        return None, None
    match = re.search(r"grid-column:\s*(\d+)\s*/\s*(\d+)", style)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


@contextlib.contextmanager
def launch_page(headless: bool, timeout_ms: int) -> Iterator[Page]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    context = browser.new_context()
    context.set_default_timeout(timeout_ms)
    context.set_default_navigation_timeout(timeout_ms)
    page = context.new_page()

    try:
        yield page
    finally:
        browser.close()
        playwright.stop()


def goto_login(page: Page) -> None:
    page.goto("https://online.bnovo.ru/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector('input[placeholder="Введите электронную почту"]', timeout=10000)


def login(page: Page, email: str, password: str) -> None:
    page.get_by_placeholder("Введите электронную почту").fill(email)
    page.get_by_placeholder("Введите пароль").fill(password)
    page.get_by_role("button", name="Войти").click()

    page.wait_for_selector(".planning-panel-content.js-planning-panel", timeout=60000)


def close_marketing_modal(page: Page) -> None:
    try:
        page.wait_for_selector(".marketing-modal__close", timeout=1000)
        page.locator(".marketing-modal__close").click()
    except Exception:
        return


def close_planning_modal(page: Page) -> None:
    try:
        page.wait_for_selector("button.v-dialog__close", timeout=1500)
        page.locator("button.v-dialog__close").first.click()
    except Exception:
        return


def goto_planning(page: Page, date_from: str, timeout_ms: int, max_attempts: int = 2) -> None:
    url = f"https://online.bnovo.ru/planning?dfrom={date_from}&daily=0"
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            return
        except PlaywrightTimeoutError as exc:
            last_exc = exc
            if attempt == max_attempts:
                raise
            page.wait_for_timeout(1000)

    if last_exc:
        raise last_exc


def wait_planning_grid(page: Page) -> None:
    page.wait_for_selector(".planning-panel-content.js-planning-panel")


def get_rows(page: Page):
    return page.locator("div.planning-panel-content.js-planning-panel")


def get_rows_for_house(page: Page, house_category: str):
    panels = page.locator("div.planning-panel")
    panels_count = panels.count()

    for i in range(panels_count):
        panel = panels.nth(i)
        name_loc = panel.locator(".planning-roomtype-name__text")
        try:
            name = (name_loc.inner_text(timeout=2000) or "").strip()
        except Exception:
            continue

        if name == house_category:
            return panel.locator("div.planning-panel-content.js-planning-panel")

    raise ValueError(f"House category '{house_category}' not found")


def get_room_name(row) -> str:
    loc = row.locator(".planning-room-name__text")
    return (loc.inner_text(timeout=5000) or "").strip()


def parse_booking_dialog(page: Page) -> Dict[str, Any]:
    stay_block = page.locator(".set.set_cols-labeled").filter(has_text="Дата заезда-выезда").first

    stay_dates_text = stay_block.locator("div.d-flex > span").nth(0).inner_text().strip()
    nights_text = (
        stay_block.locator(".bnovo-quick-actions-stay-dates-nights-count").inner_text().strip()
    )

    footer_rows = page.locator(".bnovo-quick-actions-footer__row")
    footer_count = footer_rows.count()

    amounts: Dict[str, Any] = {}
    for i in range(footer_count):
        row = footer_rows.nth(i)
        label = row.locator(".bnovo-quick-actions-footer__label").inner_text().strip()
        value = row.locator("div").last.inner_text().strip()
        amounts[label] = value

    return {
        "stay_dates": stay_dates_text,
        "nights": nights_text,
        "amounts": amounts,
    }


def get_date_by_column(column_index: int, reference: ReferencePoint) -> Optional[str]:
    if reference.date is None or reference.column is None:
        return None

    days_diff = column_index - reference.column
    target_date = reference.date + timedelta(days=days_diff)
    return target_date.strftime(DATE_FORMAT)


def get_date_from_booking(booking, page: Page) -> Tuple[datetime, int]:
    style = booking.get_attribute("style") or ""
    column_start, _ = parse_grid_column(style)

    booking.click()
    page.wait_for_selector(".bnovo-quick-actions-footer")
    details = parse_booking_dialog(page)

    date_str = details["stay_dates"].split("-")[0].strip().split(" ")[0]
    parsed_date = datetime.strptime(date_str, DATE_FORMAT)

    if column_start is None:
        raise ValueError("Cannot determine grid column for booking reference date.")

    return parsed_date, column_start


def parse_booking(booking, page: Page, reference: ReferencePoint) -> BookingSummary:
    booking_number = booking.get_attribute("data-booking-number")
    name_loc = booking.locator(".planning-booking__name")
    guest_name = name_loc.first.inner_text().strip() if name_loc.count() else None

    balance_el = booking.locator(".planning-booking__balance")
    balance = balance_el.first.inner_text().strip() if balance_el.count() else None

    style = booking.get_attribute("style") or ""
    col_start, col_end = parse_grid_column(style)

    if col_start and reference.date is None:
        reference.date, reference.column = get_date_from_booking(booking, page)

    check_in = get_date_by_column(col_start, reference) if col_start else None
    check_out = get_date_by_column(col_end, reference) if col_end else None

    return BookingSummary(
        booking_number=booking_number,
        guest_name=guest_name,
        balance=balance,
        status=None,
        grid_column_start=col_start,
        grid_column_end=col_end,
        check_in=check_in,
        check_out=check_out,
    )


def print_bookings(bookings: List[BookingSummary]) -> None:
    for booking in bookings:
        print(f"Booking Number: {booking.booking_number}")
        print(f"Guest Name: {booking.guest_name}")
        print(f"Balance: {booking.balance}")
        print(f"Status: {booking.status}")
        print(f"Grid Column Start: {booking.grid_column_start}")
        print(f"Grid Column End: {booking.grid_column_end}")
        print(f"Check-in Date: {booking.check_in}")
        print(f"Check-out Date: {booking.check_out}")
        print("-" * 40)


def parse_room_row(row, page: Page, reference: ReferencePoint) -> RoomData:
    room_name = get_room_name(row)

    bookings_locator = row.locator("div.planning-booking.js-planning-booking")
    bookings_count = bookings_locator.count()

    bookings: List[BookingSummary] = []
    for j in range(bookings_count):
        booking = bookings_locator.nth(j)
        bookings.append(parse_booking(booking, page, reference))

    print_bookings(bookings)

    return RoomData(room_name=room_name, bookings=bookings)


def parse_rooms(
    page: Page,
    reference: ReferencePoint,
    house_category: str,
    seen_bookings: Set[str],
) -> List[RoomData]:
    rows = get_rows_for_house(page, house_category)
    rows_count = rows.count()

    results: List[RoomData] = []
    for i in range(rows_count):
        row = rows.nth(i)

        try:
            room_data = parse_room_row(row, page, reference)
        except Exception:
            continue

        if seen_bookings:
            filtered_bookings: List[BookingSummary] = []
            for booking in room_data.bookings:
                if booking.booking_number and booking.booking_number in seen_bookings:
                    continue
                if booking.booking_number:
                    seen_bookings.add(booking.booking_number)
                filtered_bookings.append(booking)
            room_data = RoomData(room_name=room_data.room_name, bookings=filtered_bookings)

        results.append(room_data)

    return results


def format_date(dt: datetime) -> str:
    return dt.strftime(DATE_FORMAT)


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


def latest_check_in(rooms: List[RoomData]) -> Optional[datetime]:
    check_ins: List[datetime] = []
    for room in rooms:
        for booking in room.bookings:
            if booking.check_in:
                try:
                    check_ins.append(parse_date(booking.check_in))
                except ValueError:
                    continue
    if not check_ins:
        return None
    return max(check_ins)


def fetch_rooms_data(
    email: str,
    password: str,
    headless: bool,
    house_category: str,
    timeout_ms: int,
    date_from: str,
) -> List[RoomData]:
    seen_bookings: Set[str] = set()
    all_rooms: Dict[str, RoomData] = {}

    with launch_page(headless, timeout_ms) as page:
        goto_login(page)
        login(page, email, password)
        goto_planning(page, date_from.replace(".", "-"), timeout_ms)
        close_planning_modal(page)
        wait_planning_grid(page)

        first_reference = ReferencePoint()
        first_rooms = parse_rooms(
            page,
            first_reference,
            house_category,
            seen_bookings,
        )

        for room in first_rooms:
            all_rooms.setdefault(
                room.room_name, RoomData(room_name=room.room_name, bookings=[])
            ).bookings.extend(room.bookings)

        last_check_in = latest_check_in(first_rooms)
        if last_check_in is not None:
            goto_planning(page, last_check_in.strftime("%d-%m-%Y"), timeout_ms)
            close_planning_modal(page)
            wait_planning_grid(page)

            second_reference = ReferencePoint()
            next_rooms = parse_rooms(
                page,
                second_reference,
                house_category,
                seen_bookings,
            )

            for room in next_rooms:
                all_rooms.setdefault(
                    room.room_name, RoomData(room_name=room.room_name, bookings=[])
                ).bookings.extend(room.bookings)

    return list(all_rooms.values())


def serialize_rooms(rooms: List[RoomData]) -> List[Dict[str, Any]]:
    return [
        {
            "room": room.room_name,
            "bookings": [
                {
                    "booking_number": booking.booking_number,
                    "guest_name": booking.guest_name,
                    "balance": booking.balance,
                    "status": booking.status,
                    "grid_column_start": booking.grid_column_start,
                    "grid_column_end": booking.grid_column_end,
                    "check_in": booking.check_in,
                    "check_out": booking.check_out,
                }
                for booking in room.bookings
            ],
        }
        for room in rooms
    ]


def compute_free_spaces(
    bookings: List[BookingSummary],
    date_from: datetime,
    date_to: datetime,
) -> List[Dict[str, Any]]:
    search_start = date_from
    search_end = date_to + timedelta(days=1)
    cursor = search_start

    free_intervals: List[Tuple[datetime, datetime]] = []

    sortable_bookings = [booking for booking in bookings if booking.check_in and booking.check_out]
    sortable_bookings.sort(key=lambda booking: parse_date(booking.check_in))  # type: ignore[arg-type]

    for booking in sortable_bookings:
        start = parse_date(booking.check_in)  # type: ignore[arg-type]
        end = parse_date(booking.check_out)  # type: ignore[arg-type]

        if end <= search_start:
            continue
        if start >= search_end:
            break

        window_start = max(start, search_start)
        window_end = min(end, search_end)

        if window_start > cursor:
            free_intervals.append((cursor, window_start))

        cursor = max(cursor, window_end)

    if cursor < search_end:
        free_intervals.append((cursor, search_end))

    return [
        {
            "date_from": format_date(start),
            "date_to": format_date(end),
            "nights": (end - start).days,
        }
        for start, end in free_intervals
        if (end - start).days > 0
    ]
