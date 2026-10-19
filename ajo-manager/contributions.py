"""Settings, validation and recording of contributions.

Every record is labelled with its source. Manual entries are NOT independently
verified; only Paystack entries (checked against Paystack's verify endpoint)
carry a verified label.
"""
import math
from datetime import date, datetime
import storage
import members

FILE = "contributions.json"
SETTINGS_FILE = "settings.json"
FREQUENCIES = ("weekly", "fortnightly", "monthly")
MANUAL_LABEL = "Manually recorded - not independently verified"
PAYSTACK_LABEL = "Paid via Paystack - confirmed by Paystack verify API"


def money(x):
    return f"N{x:,.2f}"


def label_for(record):
    return PAYSTACK_LABEL if record.get("source") == "paystack" else MANUAL_LABEL


# ---------- settings ----------
def get_settings():
    s = storage.load(SETTINGS_FILE, {})
    return {"amount": s.get("amount"),
            "frequency": s.get("frequency", "monthly"),
            "current_cycle": s.get("current_cycle", 1)}


def set_settings(amount, frequency):
    if frequency not in FREQUENCIES:
        raise ValueError(f"Frequency must be one of: {', '.join(FREQUENCIES)}")
    s = get_settings()
    s.update(amount=amount, frequency=frequency)
    storage.save(SETTINGS_FILE, s)


def advance_cycle():
    s = get_settings()
    s["current_cycle"] += 1
    storage.save(SETTINGS_FILE, s)
    return s["current_cycle"]


# ---------- validation ----------
def parse_amount(text):
    cleaned = text.replace(",", "").replace("₦", "").strip().lstrip("Nn").strip()
    try:
        value = float(cleaned)
    except ValueError:
        raise ValueError("Amount must be a number, e.g. 5000.")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(value, 2)


def parse_date(text):
    text = text.strip()
    if not text:
        return date.today().isoformat()
    try:
        d = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must look like 2026-10-12.")
    if d > date.today():
        raise ValueError("Date cannot be in the future.")
    return d.isoformat()


# ---------- records ----------
def load_all():
    return storage.load(FILE, [])


def has_paid(member_id, cycle):
    return any(r["member_id"] == member_id and r["cycle"] == cycle for r in load_all())


def record(member_id, amount, cycle, date_str, source="manual", reference=None):
    member_id = member_id.strip().upper()
    if members.get_member(member_id) is None:
        raise ValueError(f"Unknown member ID: {member_id or '(blank)'}")
    current = get_settings()["current_cycle"]
    if not 1 <= cycle <= current:
        raise ValueError(f"Cycle must be between 1 and {current}.")
    if has_paid(member_id, cycle):
        raise ValueError(f"{member_id} already has a contribution for cycle {cycle}.")
    records = load_all()
    if reference and any(r.get("reference") == reference for r in records):
        raise ValueError("This payment reference has already been recorded.")
    entry = {
        "id": f"C{len(records) + 1:04d}",
        "member_id": member_id,
        "cycle": cycle,
        "amount": amount,
        "date": date_str,
        "source": source,
        "reference": reference,
        "label": PAYSTACK_LABEL if source == "paystack" else MANUAL_LABEL,
    }
    records.append(entry)
    storage.save(FILE, records)
    return entry


def for_cycle(cycle):
    return [r for r in load_all() if r["cycle"] == cycle]


def for_member(member_id):
    member_id = member_id.strip().upper()
    return sorted((r for r in load_all() if r["member_id"] == member_id),
                  key=lambda r: r["cycle"])


def total(records=None):
    return sum(r["amount"] for r in (load_all() if records is None else records))
