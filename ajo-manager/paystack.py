"""Optional Paystack integration (test mode recommended).

Put your key in the .env file:  PAYSTACK_SECRET_KEY=sk_test_xxxxx
Never hard-code the key in a .py file or commit .env to GitHub.
"""
import os
from pathlib import Path

API = "https://api.paystack.co"


def _load_env():
    """Read KEY=value lines from the .env file next to this script."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


class PaystackError(Exception):
    pass


def _headers():
    key = os.environ.get("PAYSTACK_SECRET_KEY")
    if not key:
        raise PaystackError("PAYSTACK_SECRET_KEY not found. Add it to the .env file.")
    return {"Authorization": f"Bearer {key}"}


def _call(method, path, **kwargs):
    try:
        import requests
    except ImportError:
        raise PaystackError("Run: pip install requests")
    try:
        r = requests.request(method, API + path, headers=_headers(), timeout=15, **kwargs)
        body = r.json()
    except requests.exceptions.RequestException as e:
        raise PaystackError(f"Network error: {e}")
    except ValueError:
        raise PaystackError("Paystack returned an unreadable response.")
    if not body.get("status"):
        raise PaystackError(body.get("message", "Paystack request failed."))
    return body["data"]


def initialize(email, amount_naira, reference, metadata=None):
    """Returns data containing authorization_url."""
    return _call("POST", "/transaction/initialize", json={
        "email": email,
        "amount": int(round(amount_naira * 100)),  # Paystack uses kobo
        "currency": "NGN",
        "reference": reference,
        "metadata": metadata or {},
    })


def verify(reference, expected_naira):
    """True only if Paystack says success AND the amount/currency match."""
    data = _call("GET", f"/transaction/verify/{reference}")
    return (data.get("status") == "success"
            and data.get("currency") == "NGN"
            and data.get("amount", 0) >= int(round(expected_naira * 100)))
