"""
家計簿コアロジック - 複式簿記エンジン
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).parent / "data" / "kakeibo.json"

# 科目種別と残高の正方向（借方増加 or 貸方増加）
ACCOUNT_NORMAL_BALANCE = {
    "資産": "debit",
    "負債": "credit",
    "資本": "credit",
    "収益": "credit",
    "費用": "debit",
}

DEFAULT_ACCOUNTS = [
    # 資産
    {"id": "1001", "name": "現金",               "type": "資産"},
    {"id": "1002", "name": "普通預金",            "type": "資産"},
    {"id": "1003", "name": "定期預金",            "type": "資産"},
    {"id": "1004", "name": "電子マネー",          "type": "資産"},
    # 負債
    {"id": "2001", "name": "クレジットカード",    "type": "負債"},
    {"id": "2002", "name": "住宅ローン",          "type": "負債"},
    {"id": "2003", "name": "カードローン",        "type": "負債"},
    # 資本
    {"id": "3001", "name": "元入金",              "type": "資本"},
    # 収益
    {"id": "4001", "name": "給与収入",            "type": "収益"},
    {"id": "4002", "name": "副収入",              "type": "収益"},
    {"id": "4003", "name": "利息収入",            "type": "収益"},
    {"id": "4004", "name": "その他収入",          "type": "収益"},
    # 費用
    {"id": "5001", "name": "食費",               "type": "費用"},
    {"id": "5002", "name": "外食費",             "type": "費用"},
    {"id": "5003", "name": "交通費",             "type": "費用"},
    {"id": "5004", "name": "光熱費",             "type": "費用"},
    {"id": "5005", "name": "通信費",             "type": "費用"},
    {"id": "5006", "name": "医療費",             "type": "費用"},
    {"id": "5007", "name": "娯楽費",             "type": "費用"},
    {"id": "5008", "name": "衣服費",             "type": "費用"},
    {"id": "5009", "name": "日用品費",           "type": "費用"},
    {"id": "5010", "name": "住居費",             "type": "費用"},
    {"id": "5011", "name": "保険料",             "type": "費用"},
    {"id": "5012", "name": "教育費",             "type": "費用"},
    {"id": "5013", "name": "交際費",             "type": "費用"},
    {"id": "5014", "name": "その他支出",         "type": "費用"},
]


def _load() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        data = {"accounts": DEFAULT_ACCOUNTS, "journals": []}
        _save(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 科目 ──────────────────────────────────────────────

def get_accounts() -> list[dict]:
    return _load()["accounts"]


def get_account_by_name(name: str) -> Optional[dict]:
    for acc in get_accounts():
        if acc["name"] == name:
            return acc
    return None


def add_account(name: str, account_type: str) -> dict:
    if account_type not in ACCOUNT_NORMAL_BALANCE:
        raise ValueError(f"種別が不正: {account_type}。使用可能: {list(ACCOUNT_NORMAL_BALANCE.keys())}")
    data = _load()
    for acc in data["accounts"]:
        if acc["name"] == name:
            raise ValueError(f"科目「{name}」は既に存在します")
    max_id = max((int(a["id"]) for a in data["accounts"]), default=1000)
    new_acc = {"id": str(max_id + 1), "name": name, "type": account_type}
    data["accounts"].append(new_acc)
    _save(data)
    return new_acc


# ── 仕訳 ──────────────────────────────────────────────

def add_journal_entry(
    date_str: str,
    debit_account: str,
    credit_account: str,
    amount: int,
    memo: str = "",
) -> dict:
    if not get_account_by_name(debit_account):
        raise ValueError(f"借方科目「{debit_account}」が見つかりません")
    if not get_account_by_name(credit_account):
        raise ValueError(f"貸方科目「{credit_account}」が見つかりません")
    if amount <= 0:
        raise ValueError("金額は1円以上を指定してください")

    data = _load()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": date_str,
        "debit_account": debit_account,
        "credit_account": credit_account,
        "amount": amount,
        "memo": memo,
        "created_at": datetime.now().isoformat(),
    }
    data["journals"].append(entry)
    _save(data)
    return entry


def get_journal_entries(year_month: Optional[str] = None) -> list[dict]:
    journals = _load()["journals"]
    if year_month:
        journals = [j for j in journals if j["date"].startswith(year_month)]
    return sorted(journals, key=lambda x: x["date"])


def delete_journal_entry(entry_id: str) -> bool:
    data = _load()
    before = len(data["journals"])
    data["journals"] = [j for j in data["journals"] if j["id"] != entry_id]
    if len(data["journals"]) == before:
        return False
    _save(data)
    return True


# ── 集計 ──────────────────────────────────────────────

def get_trial_balance(year_month: Optional[str] = None) -> dict:
    """残高試算表"""
    data = _load()
    accounts = {a["name"]: a for a in data["accounts"]}
    journals = data["journals"]
    if year_month:
        journals = [j for j in journals if j["date"].startswith(year_month)]

    balances: dict[str, dict] = {
        name: {"type": acc["type"], "debit": 0, "credit": 0, "balance": 0}
        for name, acc in accounts.items()
    }

    for e in journals:
        if e["debit_account"] in balances:
            balances[e["debit_account"]]["debit"] += e["amount"]
        if e["credit_account"] in balances:
            balances[e["credit_account"]]["credit"] += e["amount"]

    for name, bal in balances.items():
        acc_type = bal["type"]
        if ACCOUNT_NORMAL_BALANCE[acc_type] == "debit":
            bal["balance"] = bal["debit"] - bal["credit"]
        else:
            bal["balance"] = bal["credit"] - bal["debit"]

    # 動きのある科目だけ返す
    return {k: v for k, v in balances.items() if v["debit"] or v["credit"]}


def get_monthly_summary(year_month: str) -> dict:
    """月次収支サマリー"""
    tb = get_trial_balance(year_month)
    income = sum(v["balance"] for v in tb.values() if v["type"] == "収益")
    expense = sum(v["balance"] for v in tb.values() if v["type"] == "費用")
    return {
        "year_month": year_month,
        "income": income,
        "expense": expense,
        "net": income - expense,
        "details": {k: v for k, v in tb.items() if v["type"] in ("収益", "費用")},
    }
