from tools import get_leave_balance, get_bill_status


def test_leave_balance_found_and_missing():
    hit = get_leave_balance("Alice")
    assert hit["found"] is True
    assert hit["days"] == 8
    assert hit["error"] is None

    miss = get_leave_balance("nobody")
    assert miss["found"] is False
    assert miss["days"] is None
    assert miss["error"] == "unknown employee"


def test_bill_status_found_and_missing():
    hit = get_bill_status("b001")
    assert hit["found"] is True
    assert hit["status"] == "approved"
    assert hit["error"] is None

    miss = get_bill_status("B999")
    assert miss["found"] is False
    assert miss["status"] is None
    assert miss["error"] == "unknown bill"