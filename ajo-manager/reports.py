"""Console reports and TXT exports."""
from datetime import datetime
from collections import defaultdict
import storage
import members
import contributions as con
from contributions import money

NOTE = "Records are manually entered by the group and are not independently verified."


def show_members():
    ms = members.load_members()
    if not ms:
        print("  No members yet.")
        return
    print(f"\n  {'ID':<6}{'NAME':<22}{'PHONE':<15}{'JOINED'}")
    print("  " + "-" * 56)
    for m in ms:
        print(f"  {m['id']:<6}{m['name']:<22}{m['phone']:<15}{m['joined']}")


def paid_unpaid(cycle):
    paid_ids = {r["member_id"]: r for r in con.for_cycle(cycle)}
    ms = members.load_members()
    print(f"\n  CYCLE {cycle} - PAID / NOT PAID")
    print("  " + "=" * 56)
    for m in ms:
        r = paid_ids.get(m["id"])
        status = f"PAID  {money(r['amount'])} on {r['date']}" if r else "NOT PAID"
        print(f"  {m['id']:<6}{m['name']:<20}{status}")
    print("  " + "-" * 56)
    print(f"  Paid: {len(paid_ids)}   Not paid: {len(ms) - len(paid_ids)}")
    print(f"  {NOTE}")


def total_summary():
    records = con.load_all()
    print("\n  CONTRIBUTION SUMMARY")
    print("  " + "=" * 40)
    by_cycle = defaultdict(float)
    for r in records:
        by_cycle[r["cycle"]] += r["amount"]
    for c in sorted(by_cycle):
        print(f"  Cycle {c:<4} {money(by_cycle[c]):>18}")
    print("  " + "-" * 40)
    print(f"  TOTAL RECORDED {money(con.total(records)):>14}  ({len(records)} entries)")
    print(f"  {NOTE}")


def history(member):
    recs = con.for_member(member["id"])
    print(f"\n  HISTORY - {member['name']} ({member['id']})")
    print("  " + "-" * 56)
    if not recs:
        print("  No contributions recorded.")
        return
    for r in recs:
        print(f"  Cycle {r['cycle']:<3} {r['date']}  {money(r['amount']):>14}  [{r['source']}]")
    print(f"  Total: {money(con.total(recs))}")


def late_report():
    current = con.get_settings()["current_cycle"]
    print(f"\n  LATE CONTRIBUTIONS (cycles before {current})")
    print("  " + "-" * 40)
    found = False
    for cycle in range(1, current):
        paid = {r["member_id"] for r in con.for_cycle(cycle)}
        for m in members.load_members():
            if m["id"] not in paid:
                found = True
                print(f"  Cycle {cycle}: {m['id']} {m['name']}")
    if not found:
        print("  Nothing outstanding.")


def monthly_summary():
    months = defaultdict(lambda: [0, 0.0])
    for r in con.load_all():
        months[r["date"][:7]][0] += 1
        months[r["date"][:7]][1] += r["amount"]
    print("\n  MONTHLY SUMMARY")
    print("  " + "-" * 40)
    if not months:
        print("  No contributions recorded.")
    for month in sorted(months):
        n, amt = months[month]
        print(f"  {month}  {n:>3} entries  {money(amt):>16}")


def _write(filename, lines):
    storage.REPORTS_DIR.mkdir(exist_ok=True)
    path = storage.REPORTS_DIR / filename
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_receipt(r):
    m = members.get_member(r["member_id"])
    return _write(f"receipt_{r['id']}.txt", [
        "=" * 44, "        AJO CONTRIBUTION RECEIPT", "=" * 44,
        f"Receipt ID : {r['id']}",
        f"Member     : {m['name']} ({m['id']})",
        f"Cycle      : {r['cycle']}",
        f"Date       : {r['date']}",
        f"Amount     : {money(r['amount'])}",
        f"Source     : {r['source']}",
        f"Reference  : {r.get('reference') or '-'}",
        "-" * 44, r["label"], NOTE,
        f"Generated  : {datetime.now():%Y-%m-%d %H:%M}",
    ])


def export_statement(member):
    recs = con.for_member(member["id"])
    lines = ["=" * 50, f"MEMBER STATEMENT - {member['name']} ({member['id']})", "=" * 50]
    lines += [f"Cycle {r['cycle']:<3} {r['date']}  {money(r['amount']):>14}  {r['source']}"
              for r in recs] or ["No contributions recorded."]
    lines += ["-" * 50, f"Total: {money(con.total(recs))}", NOTE,
              f"Generated: {datetime.now():%Y-%m-%d %H:%M}"]
    return _write(f"statement_{member['id']}.txt", lines)
