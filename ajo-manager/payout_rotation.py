"""Agreed payout order. Cycle N pays order[(N-1) % len(order)]."""
import storage
import members

FILE = "payout_order.json"


def get_order():
    return storage.load(FILE, [])


def add_to_order(member_id):
    order = get_order()
    if member_id not in order:
        order.append(member_id)
        storage.save(FILE, order)


def set_order(ids):
    ids = [i.strip().upper() for i in ids if i.strip()]
    known = {m["id"] for m in members.load_members()}
    if len(ids) != len(set(ids)):
        raise ValueError("Each member ID can appear only once.")
    if set(ids) - known:
        raise ValueError(f"Unknown ID(s): {', '.join(sorted(set(ids) - known))}")
    if known - set(ids):
        raise ValueError(f"Missing member(s): {', '.join(sorted(known - set(ids)))}")
    storage.save(FILE, ids)


def recipient_for_cycle(cycle):
    order = get_order()
    if not order:
        return None
    return members.get_member(order[(cycle - 1) % len(order)])


def schedule(from_cycle, count=3):
    return [(c, recipient_for_cycle(c)) for c in range(from_cycle, from_cycle + count)]
