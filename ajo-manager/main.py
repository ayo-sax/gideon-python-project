"""Ajo Manager - contribution and payout rotation tracker (record-keeping only)."""
import uuid
import members
import contributions as con
import payout_rotation as payout
import reports
from contributions import money


def ask(prompt):
    return input(prompt).strip()


def pick_member(prompt="Member ID: "):
    mid = ask(prompt).upper()
    m = members.get_member(mid)
    if not m:
        print(f"  ! Unknown member ID: {mid or '(blank)'}")
    return m


def ask_cycle():
    current = con.get_settings()["current_cycle"]
    raw = ask(f"Cycle number [{current}]: ")
    if not raw:
        return current
    try:
        return int(raw)
    except ValueError:
        raise ValueError("Cycle must be a whole number.")


def add_member():
    m = members.add_member(ask("Full name: "), ask("Phone: "), ask("Email (needed for Paystack): "))
    payout.add_to_order(m["id"])
    print(f"  Added {m['name']} with ID {m['id']} (placed last in payout order).")


def set_contribution():
    s = con.get_settings()
    print(f"  Current: amount={s['amount']}, frequency={s['frequency']}, cycle={s['current_cycle']}")
    amount = con.parse_amount(ask("Contribution amount per member: "))
    freq = ask(f"Cycle frequency ({'/'.join(con.FREQUENCIES)}): ").lower()
    con.set_settings(amount, freq)
    print(f"  Saved: {money(amount)} {freq}.")


def record_contribution():
    m = pick_member()
    if not m:
        return
    cycle = ask_cycle()
    default = con.get_settings()["amount"]
    raw = ask(f"Amount [{default}]: " if default else "Amount: ")
    amount = con.parse_amount(raw or str(default))
    if default and amount != default:
        if ask(f"  Differs from agreed {money(default)}. Record anyway? (y/n): ").lower() != "y":
            print("  Cancelled.")
            return
    entry = con.record(m["id"], amount, cycle, con.parse_date(ask("Date YYYY-MM-DD [today]: ")))
    print(f"  Saved {entry['id']}: {m['name']} {money(amount)} for cycle {cycle}.")
    print(f"  Label: {entry['label']}")
    if ask("  Generate TXT receipt? (y/n): ").lower() == "y":
        print(f"  Receipt: {reports.write_receipt(entry)}")


def paystack_payment():
    import paystack
    m = pick_member()
    if not m:
        return
    if not m["email"]:
        print("  ! This member has no email on file (Paystack requires one).")
        return
    cycle = ask_cycle()
    if con.has_paid(m["id"], cycle):
        print(f"  ! {m['id']} already has a contribution for cycle {cycle}.")
        return
    default = con.get_settings()["amount"]
    raw = ask(f"Amount [{default}]: " if default else "Amount: ")
    amount = con.parse_amount(raw or str(default))
    ref = f"AJO-{m['id']}-C{cycle}-{uuid.uuid4().hex[:8]}"
    try:
        data = paystack.initialize(m["email"], amount, ref, {"member_id": m["id"], "cycle": cycle})
        print(f"\n  Open this link and pay:\n  {data['authorization_url']}")
        ask("\n  Press Enter after completing payment... ")
        if paystack.verify(ref, amount):
            entry = con.record(m["id"], amount, cycle, con.parse_date(""),
                               source="paystack", reference=ref)
            print(f"  Payment confirmed. Saved {entry['id']}.")
            print(f"  Label: {entry['label']}")
        else:
            print("  Payment not confirmed by Paystack. Nothing was recorded.")
    except paystack.PaystackError as e:
        print(f"  ! Paystack: {e}")


def payout_order():
    order = payout.get_order()
    print("\n  PAYOUT ORDER")
    for i, mid in enumerate(order, 1):
        m = members.get_member(mid)
        print(f"  {i}. {mid}  {m['name'] if m else '(missing)'}")
    if order and ask("  Change order? (y/n): ").lower() == "y":
        payout.set_order(ask("  New order, IDs separated by commas: ").split(","))
        print("  Payout order updated.")


def next_payout():
    cycle = con.get_settings()["current_cycle"]
    if payout.recipient_for_cycle(cycle) is None:
        print("  No payout order yet. Add members first.")
        return
    print(f"\n  NEXT PAYOUT (cycle {cycle}):")
    for c, m in payout.schedule(cycle):
        marker = "-> " if c == cycle else "   "
        print(f"  {marker}Cycle {c}: {m['name']} ({m['id']})")


def start_next_cycle():
    cur = con.get_settings()["current_cycle"]
    r = payout.recipient_for_cycle(cur)
    msg = f"  Close cycle {cur}"
    if r:
        msg += f" (recipient: {r['name']})"
    if ask(msg + " and start the next one? (y/n): ").lower() == "y":
        print(f"  Now on cycle {con.advance_cycle()}.")


def member_history():
    m = pick_member()
    if m:
        reports.history(m)


def export_statement():
    m = pick_member()
    if m:
        print(f"  Saved: {reports.export_statement(m)}")


def search_member():
    found = members.search(ask("Search by ID or name: "))
    for m in found:
        print(f"  {m['id']}  {m['name']}  {m['phone']}  {m['email']}")
    if not found:
        print("  No match.")


def paid_report():
    reports.paid_unpaid(ask_cycle())


MENU = [
    ("Add member", add_member),
    ("Display all members", lambda: reports.show_members()),
    ("Set contribution amount & cycle frequency", set_contribution),
    ("Record a contribution (manual)", record_contribution),
    ("Paid / not paid for a cycle", paid_report),
    ("Total contributions recorded", lambda: reports.total_summary()),
    ("Member contribution history", member_history),
    ("View / change payout order", payout_order),
    ("Next payout recipient", next_payout),
    ("Start next cycle", start_next_cycle),
    ("Late-contribution report", lambda: reports.late_report()),
    ("Monthly summary", lambda: reports.monthly_summary()),
    ("Export member statement (TXT)", export_statement),
    ("Search member", search_member),
    ("Pay with Paystack (optional)", paystack_payment),
]


def main():
    print("=" * 50)
    print("  AJO MANAGER - record-keeping only")
    print("  Does not hold or move money. Entries are manual")
    print("  unless marked as confirmed by Paystack.")
    print("=" * 50)
    while True:
        s = con.get_settings()
        print(f"\n  [Cycle {s['current_cycle']} | {s['frequency']} | "
              f"{money(s['amount']) if s['amount'] else 'amount not set'}]")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i:>2}. {label}")
        print("   0. Exit")
        choice = ask("Choose: ")
        if choice == "0":
            print("Goodbye. All data is saved in the data/ folder.")
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print("  ! Invalid option.")
            continue
        try:
            MENU[int(choice) - 1][1]()
        except ValueError as e:
            print(f"  ! {e}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nExited. Data already saved.")
