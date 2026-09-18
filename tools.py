LEAVE_BALANCES = {
    "alice": 8,
    "bob": 3,
    "chen": 12,
}

BILL_STATUSES = {
    "B001": "approved",
    "B002": "pending",
    "B003": "rejected",
}


def get_leave_balance(name: str) -> dict:
    key = name.strip().lower()
    if key not in LEAVE_BALANCES:
        return {
            "found": False,
            "name": name,
            "days": None,
            "error": "unknown employee",
        }
    return {
        "found": True,
        "name": key,
        "days": LEAVE_BALANCES[key],
        "error": None,
    }


def get_bill_status(bill_id: str) -> dict:
    key = bill_id.strip().upper()
    if key not in BILL_STATUSES:
        return {
            "found": False,
            "id": bill_id,
            "status": None,
            "error": "unknown bill",
        }
    return {
        "found": True,
        "id": key,
        "status": BILL_STATUSES[key],
        "error": None,
    }