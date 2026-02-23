import random
import uuid
import json
import string
from datetime import datetime, timedelta, timezone

from database import init_db, get_connection, DB_PATH
from processors.payflow import payflow_instance
from processors.stripeconnect import stripeconnect_instance
from processors.latampay import latampay_instance

random.seed(42)

MERCHANTS = [
    ("merch_001", "CloudBites Inc"),
    ("merch_002", "TechPulse Labs"),
    ("merch_003", "FreshGrocer Co"),
    ("merch_004", "StreamVault Media"),
    ("merch_005", "PixelForge Studios"),
]

STATUSES = ["SUCCEEDED"] * 70 + ["PENDING"] * 10 + ["DECLINED"] * 8 + ["REFUNDED"] * 5 + ["ERROR"] * 3 + ["EXPIRED"] * 4

SUB_STATUSES = {
    "SUCCEEDED": ["APPROVED", "CAPTURED"],
    "PENDING": ["PENDING_PROVIDER_CONFIRMATION", "AUTHORIZED"],
    "DECLINED": ["APPROVED"],
    "REFUNDED": ["PARTIALLY_REFUNDED", "APPROVED"],
    "ERROR": ["APPROVED"],
    "EXPIRED": ["APPROVED"],
    "AUTHORIZED": ["AUTHORIZED"],
    "CANCELED": ["APPROVED"],
}

DESCRIPTIONS = [
    "Monthly subscription", "One-time purchase", "Premium upgrade",
    "Marketplace order", "In-app purchase", "Service fee",
    "Digital download", "API usage fee", "Storage upgrade",
    "Team license", "Enterprise plan", "Addon purchase",
]


def gen_hex(n):
    return "".join(random.choices("0123456789abcdef", k=n))


def gen_alphanum(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def gen_timestamp(days_ago_max=30):
    days = random.uniform(0, days_ago_max)
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()


def build_payflow_response(proc_id, amount, currency, status, merchant_name):
    result_code_map = {
        "SUCCEEDED": "Authorised",
        "DECLINED": "Refused",
        "PENDING": "Pending",
        "ERROR": "Error",
        "CANCELED": "Cancelled",
        "REFUNDED": "Refunded",
        "EXPIRED": "Error",
        "AUTHORIZED": "Authorised",
    }
    result_code = result_code_map.get(status, "Error")
    cents = int(amount * 100)
    resp = {
        "pspReference": proc_id,
        "merchantAccount": f"{merchant_name.replace(' ', '')}Merchant",
        "resultCode": result_code,
        "authCode": f"0{random.randint(10000, 99999)}",
        "refusalReason": "",
        "refusalReasonCode": "",
        "amount": {"currency": currency.upper(), "value": cents},
        "additionalData": {
            "paymentMethodVariant": random.choice(["visa", "mc", "amex"]),
            "acquirerCode": "TestAcquirer",
            "authorisedAmountValue": str(cents),
        },
        "eventDate": (datetime.now(timezone.utc) - timedelta(days=random.uniform(0, 30))).strftime(
            "%Y-%m-%dT%H:%M:%S+01:00"
        ),
    }
    if result_code == "Refused":
        resp["refusalReason"] = random.choice(["Not enough balance", "Card expired", "CVC Declined"])
        resp["refusalReasonCode"] = str(random.choice([2, 5, 24]))
    return resp


def build_stripe_response(proc_id, amount, currency, status):
    status_map = {
        "SUCCEEDED": "succeeded",
        "DECLINED": "failed",
        "PENDING": "pending",
        "ERROR": "failed",
        "CANCELED": "canceled",
        "REFUNDED": "refunded",
        "EXPIRED": "failed",
        "AUTHORIZED": "succeeded",
    }
    stripe_status = status_map.get(status, "failed")
    cents = int(amount * 100)
    paid = stripe_status == "succeeded"
    captured = paid
    refunded = stripe_status == "refunded"
    resp = {
        "id": proc_id,
        "object": "charge",
        "amount": cents,
        "amount_captured": cents if captured else 0,
        "amount_refunded": cents if refunded else 0,
        "currency": currency.lower(),
        "status": stripe_status,
        "paid": paid,
        "captured": captured,
        "refunded": refunded,
        "failure_code": None,
        "failure_message": None,
        "outcome": {
            "network_status": "approved_by_network" if paid else "declined_by_network",
            "reason": None if paid else "generic_decline",
            "type": "authorized" if paid else "issuer_declined",
        },
        "created": int((datetime.now(timezone.utc) - timedelta(days=random.uniform(0, 30))).timestamp()),
        "livemode": False,
    }
    if stripe_status == "failed":
        resp["failure_code"] = random.choice(["card_declined", "insufficient_funds", "expired_card"])
        resp["failure_message"] = random.choice(
            ["Your card was declined.", "Your card has insufficient funds.", "Your card has expired."]
        )
        resp["paid"] = False
    return resp


def build_latampay_response(proc_id, amount, currency, country, status):
    status_code_map = {
        "SUCCEEDED": ("PAID", "The payment was paid.", "200"),
        "DECLINED": ("REJECTED", "The payment was rejected by the bank.", "302"),
        "PENDING": ("PENDING", "The payment is pending.", "100"),
        "ERROR": ("REJECTED", "The payment encountered an error.", "301"),
        "CANCELED": ("CANCELLED", "The payment was cancelled.", "300"),
        "REFUNDED": ("REFUNDED", "The payment was refunded.", "400"),
        "EXPIRED": ("EXPIRED", "The payment has expired.", "500"),
        "AUTHORIZED": ("AUTHORIZED", "The payment was authorized.", "100"),
    }
    lp_status, detail, code = status_code_map.get(status, ("REJECTED", "Unknown.", "301"))
    created = datetime.now(timezone.utc) - timedelta(days=random.uniform(0, 30))
    resp = {
        "id": proc_id,
        "amount": amount,
        "currency": currency.upper(),
        "country": country.upper(),
        "payment_method_id": random.choice(["CARD", "PIX", "BANK_TRANSFER"]),
        "payment_method_type": "CARD",
        "payment_method_flow": "DIRECT",
        "status": lp_status,
        "status_detail": detail,
        "status_code": code,
        "order_id": f"ORD-2026-{random.randint(10000, 99999)}",
        "notification_url": "https://cloudbites.com/webhooks/latampay",
        "created_date": created.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "approved_date": (created + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if lp_status == "PAID"
        else None,
    }
    return resp


# Ghost transaction definitions: internal_status differs from processor status
GHOST_TXNS = [
    # 1-3: SUCCEEDED internally but DECLINED at processor (CRITICAL) — one per processor
    {"idx": 2, "internal": "SUCCEEDED", "proc_status_override": "Refused"},           # PayFlow (idx < 40)
    {"idx": 45, "internal": "SUCCEEDED", "proc_status_override": "failed"},            # StripeConnect (40 <= idx < 80)
    {"idx": 82, "internal": "SUCCEEDED", "proc_status_override": ("REJECTED", "302")}, # LatamPay (idx >= 80)
    # 4-5: More SUCCEEDED→Refused at PayFlow
    {"idx": 8, "internal": "SUCCEEDED", "proc_status_override": "Refused"},            # PayFlow
    {"idx": 14, "internal": "SUCCEEDED", "proc_status_override": "Refused"},           # PayFlow
    # 6: SUCCEEDED→failed at Stripe
    {"idx": 50, "internal": "SUCCEEDED", "proc_status_override": "failed"},            # StripeConnect
    # 7-9: PENDING internally but SUCCEEDED at processor (MISSED_WEBHOOK)
    {"idx": 20, "internal": "PENDING", "proc_status_override": "Authorised"},          # PayFlow
    {"idx": 55, "internal": "PENDING", "proc_status_override": "succeeded"},           # StripeConnect
    {"idx": 88, "internal": "PENDING", "proc_status_override": ("PAID", "200")},       # LatamPay
    # 10-11: More PENDING→succeeded
    {"idx": 25, "internal": "PENDING", "proc_status_override": "Authorised"},          # PayFlow
    {"idx": 60, "internal": "PENDING", "proc_status_override": "succeeded"},           # StripeConnect
    # 12-14: SUCCEEDED internally but REFUNDED at processor (UNTRACKED_REFUND)
    {"idx": 30, "internal": "SUCCEEDED", "proc_status_override": "Refunded"},          # PayFlow
    {"idx": 65, "internal": "SUCCEEDED", "proc_status_override": "refunded"},          # StripeConnect
    {"idx": 95, "internal": "SUCCEEDED", "proc_status_override": ("REFUNDED", "400")}, # LatamPay
    # 15-16: AUTHORIZED internally but CANCELED at processor (STATUS_MISMATCH)
    {"idx": 35, "internal": "AUTHORIZED", "proc_status_override": "Cancelled"},        # PayFlow
    {"idx": 70, "internal": "AUTHORIZED", "proc_status_override": "canceled"},         # StripeConnect
    # 17-18: SUCCEEDED internally but 404 at processor (MISSING_AT_PROCESSOR)
    {"idx": 10, "internal": "SUCCEEDED", "missing": True},                             # PayFlow
    {"idx": 75, "internal": "SUCCEEDED", "missing": True},                             # StripeConnect
]


def seed():
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    conn = get_connection()

    ghost_map = {g["idx"]: g for g in GHOST_TXNS}

    payments = []
    transactions = []

    for i in range(120):
        # Determine processor assignment
        if i < 40:
            proc_name = "PayFlow"
            currencies = ["USD", "EUR"]
            countries = ["US", "DE"]
            methods = ["CARD"]
        elif i < 80:
            proc_name = "StripeConnect"
            currencies = ["USD"]
            countries = ["US"]
            methods = ["CARD", "WALLET"]
        else:
            proc_name = "LatamPay"
            currencies = ["BRL", "MXN", "COP"]
            countries = ["BR", "MX", "CO"]
            methods = ["CARD", "PIX", "BANK_TRANSFER"]

        merchant_id, merchant_name = random.choice(MERCHANTS)
        currency = random.choice(currencies)
        country = random.choice(countries)
        method = random.choice(methods)
        amount = round(random.uniform(10.0, 500.0), 2)
        order_num = random.randint(10000, 99999)
        order_id = f"ORD-2026-{order_num}"
        description = random.choice(DESCRIPTIONS)

        # Status selection
        ghost = ghost_map.get(i)
        if ghost:
            internal_status = ghost["internal"]
        else:
            internal_status = random.choice(STATUSES)

        sub_status = random.choice(SUB_STATUSES.get(internal_status, ["APPROVED"]))

        # Generate IDs
        pay_id = f"pay_{gen_hex(8)}"
        txn_id = f"txn_{gen_hex(8)}"

        if proc_name == "PayFlow":
            proc_txn_id = f"PF-{gen_hex(8)}"
        elif proc_name == "StripeConnect":
            proc_txn_id = f"ch_{gen_alphanum(24)}"
        else:
            proc_txn_id = f"LP-PAY-{random.randint(1000000, 9999999)}"

        created_at = gen_timestamp()
        updated_at = created_at

        # Build processor response and store in mock processor
        if ghost and ghost.get("missing"):
            # Don't add to processor store (simulates 404)
            proc_raw_response = None
            proc_status = None
            proc_status_detail = None
            proc_response_code = None
        else:
            if proc_name == "PayFlow":
                if ghost:
                    override_status = ghost["proc_status_override"]
                    resp = build_payflow_response(proc_txn_id, amount, currency, internal_status, merchant_name)
                    resp["resultCode"] = override_status
                    if override_status == "Refused":
                        resp["refusalReason"] = "Not enough balance"
                        resp["refusalReasonCode"] = "2"
                    elif override_status == "Refunded":
                        pass
                else:
                    resp = build_payflow_response(proc_txn_id, amount, currency, internal_status, merchant_name)
                payflow_instance.add_to_store(proc_txn_id, resp)
                proc_status = resp["resultCode"]
                proc_status_detail = resp.get("refusalReason", "")
                proc_response_code = resp.get("refusalReasonCode", "")
                proc_raw_response = json.dumps(resp)

            elif proc_name == "StripeConnect":
                if ghost:
                    override_status = ghost["proc_status_override"]
                    resp = build_stripe_response(proc_txn_id, amount, currency, internal_status)
                    resp["status"] = override_status
                    if override_status == "failed":
                        resp["paid"] = False
                        resp["captured"] = False
                        resp["failure_code"] = "card_declined"
                        resp["failure_message"] = "Your card was declined."
                        resp["outcome"] = {
                            "network_status": "declined_by_network",
                            "reason": "generic_decline",
                            "type": "issuer_declined",
                        }
                    elif override_status == "refunded":
                        resp["refunded"] = True
                        resp["amount_refunded"] = resp["amount"]
                    elif override_status == "succeeded":
                        resp["paid"] = True
                        resp["captured"] = True
                    elif override_status == "canceled":
                        resp["paid"] = False
                        resp["captured"] = False
                else:
                    resp = build_stripe_response(proc_txn_id, amount, currency, internal_status)
                stripeconnect_instance.add_to_store(proc_txn_id, resp)
                proc_status = resp["status"]
                proc_status_detail = resp.get("failure_message", "")
                proc_response_code = resp.get("failure_code", "")
                proc_raw_response = json.dumps(resp)

            else:  # LatamPay
                if ghost:
                    override = ghost["proc_status_override"]
                    resp = build_latampay_response(proc_txn_id, amount, currency, country, internal_status)
                    resp["status"] = override[0]
                    resp["status_code"] = override[1]
                    resp["status_detail"] = f"The payment was {override[0].lower()}."
                else:
                    resp = build_latampay_response(proc_txn_id, amount, currency, country, internal_status)
                latampay_instance.add_to_store(proc_txn_id, resp)
                proc_status = resp["status"]
                proc_status_detail = resp.get("status_detail", "")
                proc_response_code = resp.get("status_code", "")
                proc_raw_response = json.dumps(resp)

        # Build response message
        response_msg = "Transaction processed successfully" if internal_status == "SUCCEEDED" else f"Transaction {internal_status.lower()}"

        payments.append((
            pay_id, merchant_id, merchant_name, order_id, description,
            amount, currency, country, method, internal_status, sub_status,
            proc_name, created_at, updated_at,
        ))
        transactions.append((
            txn_id, pay_id, "PURCHASE", internal_status, sub_status,
            response_msg, proc_name, proc_txn_id, proc_status,
            proc_status_detail, proc_response_code, proc_raw_response,
            amount, currency, created_at, updated_at,
        ))

    conn.executemany(
        """INSERT INTO payments
           (id, merchant_id, merchant_name, order_id, description, amount, currency,
            country, payment_method, internal_status, internal_sub_status, processor_name,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        payments,
    )
    conn.executemany(
        """INSERT INTO transactions
           (id, payment_id, type, internal_status, internal_sub_status, response_message,
            processor_name, processor_transaction_id, processor_status, processor_status_detail,
            processor_response_code, processor_raw_response, amount, currency, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        transactions,
    )
    conn.commit()

    print(f"Seeded {len(payments)} payments and {len(transactions)} transactions")
    print(f"Ghost transactions: {len(GHOST_TXNS)} (will show as mismatches during reconciliation)")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    seed()
    # Only close when run standalone (not when imported by main.py)
    get_connection().close()
