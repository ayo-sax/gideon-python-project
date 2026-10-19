# Ajo Manager

A menu-driven Python tool for tracking an Ajo/Esusu group: members, contributions, paid/unpaid status and payout rotation.

**Record-keeping only.** It does not hold or move money, guarantee repayment, or replace the group's agreed rules. Contributions are labelled *"Manually recorded - not independently verified"*. Only Paystack payments confirmed through Paystack's verify API carry a different label.

## Run
```
python main.py
```
Python 3.8+. No packages needed except for the optional Paystack feature (`pip install -r requirements.txt`).

## Files
| File | Purpose |
|---|---|
| main.py | Menu and input handling |
| members.py | Add / list / search members (IDs M001, M002...) |
| contributions.py | Settings, validation, recording, duplicate prevention |
| payout_rotation.py | Payout order and next recipient |
| reports.py | Paid/unpaid, totals, history, late, monthly, TXT receipts/statements |
| paystack.py | Optional Paystack initialize + verify |
| storage.py | Safe JSON load/save |
| data/ | members.json, contributions.json, payout_order.json, settings.json |
| reports/ | Generated receipts and statements |

## How it works
- A **cycle** is one round of contributions; each cycle has one payout recipient.
- Cycle N pays `payout_order[(N-1) % members]`, so the order repeats.
- One contribution per member per cycle; duplicates are rejected.
- Amounts must be positive numbers; dates cannot be in the future; unknown member IDs are rejected.

## Paystack (optional)
Open the `.env` file and replace `sk_test_paste_your_key_here` with your Paystack **test** secret key (Paystack dashboard -> Settings -> API Keys & Webhooks). `.env` is listed in `.gitignore` so it is not pushed to GitHub. Never put the key inside a .py file.

Menu option 15 creates a payment link, waits for you to pay, verifies the reference with Paystack, and records the contribution only if Paystack confirms success and the amount matches.

## Test checklist
Add members, set amount, record contributions, view paid/unpaid, view total, check next payout, restart and confirm data persists, then try an invalid amount, an unknown ID and a duplicate entry. Save screenshots in `screenshots/`.
