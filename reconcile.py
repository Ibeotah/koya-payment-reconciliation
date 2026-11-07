# #!/usr/bin/env python3
# """Payment reconciliation.

# Reads payments.jsonl and works out how much money we actually collected.
# Run:  python3 reconcile.py
# """
# import json

# total = 0.0
# count = 0

# with open("payments.jsonl") as f:
#     for line in f:
#         event = json.loads(line)
#         if event["status"] == "success":
#             total += float(event["amount"])
#             count += 1

# with open("expected.txt") as f:
#     expected = int(f.read().strip())

# if count != expected:
#     print(f"Check failed: counted {count} successful payments, expected {expected}.")
#     print("Something in the data isn't being handled the way the README describes.")
# else:
#     print(f"Check passed: {count} successful payments.")
#     print(f"Your code: KOYA-{round(total)}")


#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def read_amount(value):
    """Turn an amount such as '55,707.77' or 3533.05 into a number.
    Returns None if the amount cannot be read."""
    text = str(value).replace(",", "").replace("NGN", "").strip()
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    return number


def read_time(value):
    """Turn a time such as '2026-09-21T15:30:26Z' into a time we can compare.
    If the time cannot be read, return the oldest possible time."""
    text = str(value).strip().replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def main():
    # For each txn_id, we keep only its latest attempt.
    latest = {}

    with open("payments.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # blank line, skip it

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # line cannot be read, skip it

            if not isinstance(event, dict):
                continue  # line is not an event, skip it

            txn_id = event.get("txn_id")
            if not txn_id:
                continue  # no txn_id, skip it

            when = read_time(event.get("ts", ""))
            status = str(event.get("status", "")).strip().lower()
            amount = read_amount(event.get("amount", ""))

            previous = latest.get(txn_id)
            if previous is None or when >= previous["when"]:
                latest[txn_id] = {"when": when, "status": status, "amount": amount}

    total = Decimal(0)
    count = 0
    for attempt in latest.values():
        if attempt["status"] == "success":
            count += 1
            if attempt["amount"] is not None:
                total += attempt["amount"]

    with open("expected.txt") as f:
        expected = int(f.read().strip())

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    main()
