import aiohttp
import asyncio

from datetime import datetime, timedelta

from .const import VTN_URL

HEADERS = {"Content-type": "application/json", "Authorization": "Bearer bl_token"}


async def get_current_event_prices():
    """Get the current pricing event from the VTN and extract price data"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VTN_URL}/events",
            headers=HEADERS,
        ) as response:
            events = await response.json()
    if not events:
        return [0] * 24  # Return default prices if no events

    # Get the last event (assuming it's a pricing event, and that new events are appended to end of list)
    event = events[-1]
    event_prices = []
    for interval in event.get("intervals", []):
        for payload in interval.get("payloads", []):
            if payload.get("type") == "PRICE" and payload.get("values"):
                event_prices.append(payload["values"][0])

    return event_prices


async def _create_program() -> bool:
    """currently hardcoding the program details"""
    data = {"programName": "minimalProgram"}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{VTN_URL}/programs", headers=HEADERS, json=data
        ) as response:
            status = response.status
            try:
                resp_json = await response.json()
            except aiohttp.ContentTypeError:
                resp_json = await response.text()
    if status == 201:
        print("Created program")
        return True
    if status == 409:
        print("Program already exists")
        return True

    print("Failed to create program")
    print("Create program, status code:", status)
    print("Create program, response body:", resp_json)
    return False


async def _delete_event(event_id=0) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            f"{VTN_URL}/events/{event_id}",
            headers=HEADERS,
        ) as response:
            status = response.status
            try:
                resp_json = await response.json()
            except aiohttp.ContentTypeError:
                resp_json = await response.text()
    if status == 200:
        print("Okay")
        return True
    if status == 400:
        print("bad request")
        return True

    print("Failed to delete event")
    print("status code:", status)
    print("response body:", resp_json)
    return False


async def _create_pricing_event(data, interval_start=0):
    """post example price, optionally adjusting order of intervals
    data is the pricing event"""

    # Extract pricing data from the event
    intervals = data["intervals"]
    updated_intervals = intervals[interval_start:] + intervals[:interval_start]
    data["intervals"] = updated_intervals

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{VTN_URL}/events", headers=HEADERS, json=data
        ) as response:
            status = response.status
            try:
                resp_json = await response.json()
            except aiohttp.ContentTypeError:
                resp_json = await response.text()
    if status == 201:
        print("Created pricing event")
        return True
    print("Failed to create pricing event")
    print("Create event, status code:", status)
    print("Create event, response body:", resp_json)
    return False


async def _delete_all_events():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VTN_URL}/events",
            headers=HEADERS,
        ) as response:
            events = await response.json()
    if events == []:
        print("No events to delete")
        return
    for event in events:
        print(f"Deleting event {event['id']}")
        await _delete_event(event["id"])

    last_id = events[-1]["id"]

    return last_id
