import requests
import json
from datetime import datetime, timedelta
import threading
import time

# VTN_URL = "http://192.168.122.226:8080/openadr3/3.0.1" on HA
VTN_URL = "http://localhost:8080/openadr3/3.0.1"

HEADERS = {"Content-type": "application/json", "Authorization": "Bearer bl_token"}


def get_current_event_prices():
    """Get the current pricing event from the VTN and extract price data"""
    response = requests.get(
        f"{VTN_URL}/events",
        headers=HEADERS,
    )
    events = response.json()
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


def _create_program() -> bool:
    """currently hardcoding the program details"""
    data = {"programName": "minimalProgram"}
    response = requests.post(f"{VTN_URL}/programs", headers=HEADERS, json=data)
    if response.status_code == 201:
        print("Created program")
        return True
    # The program was already on the VTN
    if response.status_code == 409:
        print("Program already exists")
        return True

    print("Failed to create program")
    print("Create program, status code:", response.status_code)
    print("Create program, response body:", response.json())
    return False


def _delete_event(event_id=0) -> bool:
    response = requests.delete(
        f"{VTN_URL}/events/{event_id}",
        headers=HEADERS,
    )
    if response.status_code == 200:
        print("Okay")
        return True
    # The program was already on the VTN
    if response.status_code == 400:
        print("bad request")
        return True

    print("Failed to delete event")
    print("status code:", response.status_code)
    print("response body:", response.json())
    return False


# This event publishes pricing information to VENs
def _create_pricing_event(data, interval_start=0):
    """post example price, optionally adjusting order of intervals
    data is the pricing event"""

    # Extract pricing data from the event
    intervals = data["intervals"]
    updated_intervals = intervals[interval_start:] + intervals[:interval_start]
    data["intervals"] = updated_intervals

    response = requests.post(f"{VTN_URL}/events", headers=HEADERS, json=data)
    if response.status_code == 201:
        print("Created pricing event")
        return True
    print("Failed to create pricing event")
    print("Create event, status code:", response.status_code)
    print("Create event, response body:", response.json())


def _delete_all_events():
    response = requests.get(
        f"{VTN_URL}/events",
        headers=HEADERS,
    )
    events = response.json()
    if events == []:
        print("No events to delete")
        return
    for event in events:
        print(f"Deleting event {event['id']}")
        _delete_event(event["id"])

    last_id = events[-1]["id"]

    return last_id


# def _post_prices_with_threading():
#     while True:
#         for i in range(0, 24):
#             _create_pricing_event(i)
#             time.sleep(5)
#             _delete_all_events()


# if __name__ == "__main__":
#     _create_program()
#     _delete_all_events()
# Start the worker in a separate thread
# thread = threading.Thread(target=_post_prices_with_threading, daemon=True)
# thread.start()
# app.run(port=8081, debug=True)
