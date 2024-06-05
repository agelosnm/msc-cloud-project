def main(event):
    event_payload = event.get("event", {})
    return event_payload
    # name = event_payload.get("name", "World")
    # greeting = f"Hello, {name}!"
    # return {"greeting": greeting}
