"""Member registration and lookup."""
from datetime import date
import storage

FILE = "members.json"


def load_members():
    return storage.load(FILE, [])


def get_member(member_id):
    member_id = member_id.strip().upper()
    return next((m for m in load_members() if m["id"] == member_id), None)


def add_member(name, phone="", email=""):
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    members = load_members()
    if any(m["name"].lower() == name.lower() for m in members):
        raise ValueError(f"A member named '{name}' already exists.")
    next_num = max((int(m["id"][1:]) for m in members), default=0) + 1
    member = {
        "id": f"M{next_num:03d}",
        "name": name,
        "phone": phone.strip(),
        "email": email.strip(),
        "joined": date.today().isoformat(),
    }
    members.append(member)
    storage.save(FILE, members)
    return member


def search(term):
    term = term.strip().lower()
    return [m for m in load_members()
            if term in m["id"].lower() or term in m["name"].lower()]
