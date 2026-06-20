"""
家計簿MCP サーバー

使い方:
  pip install mcp
  python server.py

Claude Desktop の設定 (claude_desktop_config.json):
  {
    "mcpServers": {
      "家計簿": {
        "command": "python",
        "args": ["/path/to/kakeibo_mcp/server.py"]
      }
    }
  }
"""

import sys
from pathlib import Path

# server.py と同じディレクトリの kakeibo.py を読み込む
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from kakeibo import (
    get_accounts,
    add_account,
    add_journal_entry,
    get_journal_entries,
    delete_journal_entry,
    get_trial_balance,
    get_monthly_summary,
    ACCOUNT_NORMAL_BALANCE,
)

mcp = FastMCP("家計簿MCP")


@mcp.tool()
def list_accounts() -> str:
    """
    登録されている勘定科目の一覧を返します。
    仕訳を記録する前に必ずこのツールで科目名を確認してください。
    """
    accounts = get_accounts()
    grouped: dict[str, list[str]] = {}
    for acc in accounts:
        grouped.setdefault(acc["type"], []).append(acc["name"])

    lines = ["【勘定科目一覧】"]
    for acc_type in ["資産", "負債", "資本", "収益", "費用"]:
        names = grouped.get(acc_type, [])
        if names:
            lines.append(f"\n■ {acc_type}")
            for name in names:
                lines.append(f"  ・{name}")
    return "\n".join(lines)


@mcp.tool()
def record_journal(
    date: str,
    debit_account: str,
    credit_account: str,
    amount: int,
    memo: str = "",
) -> str:
    """
    仕訳を1件記録します。

    引数:
      date           : 日付。YYYY-MM-DD 形式（例: 2026-06-20）
      debit_account  : 借方の科目名（科目一覧で確認すること）
      credit_account : 貸方の科目名（科目一覧で確認すること）
      amount         : 金額。円単位の整数（例: 3000）
      memo           : 摘要。取引の説明（省略可）

    よくある仕訳パターン:
      スーパーで現金払い → debit_account:食費 / credit_account:現金
      給与入金          → debit_account:普通預金 / credit_account:給与収入
      カード払い        → debit_account:食費 / credit_account:クレジットカード
      カード引落し      → debit_account:クレジットカード / credit_account:普通預金
    """
    try:
        entry = add_journal_entry(date, debit_account, credit_account, amount, memo)
        return (
            f"✅ 仕訳を記録しました\n"
            f"  ID  : {entry['id']}\n"
            f"  日付: {entry['date']}\n"
            f"  借方: {entry['debit_account']}\n"
            f"  貸方: {entry['credit_account']}\n"
            f"  金額: {entry['amount']:,}円\n"
            f"  摘要: {entry['memo']}"
        )
    except ValueError as e:
        return f"❌ エラー: {e}"


@mcp.tool()
def list_journals(year_month: str = "") -> str:
    """
    仕訳の一覧を表示します。

    引数:
      year_month: 年月。YYYY-MM 形式で絞り込み（例: 2026-06）。省略すると全件表示。
    """
    entries = get_journal_entries(year_month or None)
    if not entries:
        label = f"「{year_month}」" if year_month else "全期間"
        return f"{label} の仕訳データはありません"

    label = year_month or "全期間"
    lines = [f"【仕訳一覧】{label}", ""]
    for e in entries:
        lines.append(
            f"{e['date']} [{e['id']}]  "
            f"{e['debit_account']} / {e['credit_account']}  "
            f"{e['amount']:>10,}円  {e['memo']}"
        )
    lines.append(f"\n合計金額: {sum(e['amount'] for e in entries):,}円 ({len(entries)}件)")
    return "\n".join(lines)


@mcp.tool()
def delete_journal(journal_id: str) -> str:
    """
    指定したIDの仕訳を削除します。
    仕訳IDは「仕訳一覧」ツールで確認できます。

    引数:
      journal_id: 削除する仕訳のID（例: J-0001）
    """
    if delete_journal_entry(journal_id):
        return f"✅ 仕訳 [{journal_id}] を削除しました"
    return f"❌ 仕訳 [{journal_id}] が見つかりません"


@mcp.tool()
def trial_balance(year_month: str = "") -> str:
    """
    残高試算表を表示します。各科目の借方・貸方合計と残高を確認できます。

    引数:
      year_month: 年月。YYYY-MM 形式で絞り込み（例: 2026-06）。省略すると全期間。
    """
    balances = get_trial_balance(year_month or None)
    if not balances:
        return "データがありません"

    label = year_month or "全期間"
    lines = [f"【残高試算表】{label}", ""]

    type_order = ["資産", "負債", "資本", "収益", "費用"]
    for acc_type in type_order:
        items = {k: v for k, v in balances.items() if v["type"] == acc_type}
        if not items:
            continue
        lines.append(f"■ {acc_type}")
        lines.append(f"  {'科目':<12}  {'借方':>12}  {'貸方':>12}  {'残高':>12}")
        lines.append("  " + "-" * 52)
        type_total = 0
        for name, bal in items.items():
            lines.append(
                f"  {name:<12}  {bal['debit']:>12,}  {bal['credit']:>12,}  {bal['balance']:>12,}"
            )
            type_total += bal["balance"]
        lines.append(f"  {'【合計】':<12}  {'':>12}  {'':>12}  {type_total:>12,}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def monthly_summary(year_month: str) -> str:
    """
    指定月の収支サマリーを表示します。

    引数:
      year_month: 年月。YYYY-MM 形式（例: 2026-06）
    """
    summary = get_monthly_summary(year_month)
    income = summary["income"]
    expense = summary["expense"]
    net = summary["net"]

    lines = [
        f"【{year_month} 月次収支】",
        "",
        f"  収入合計: {income:>12,}円",
        f"  支出合計: {expense:>12,}円",
        f"  ──────────────────",
        f"  収支差額: {net:>12,}円  {'（黒字）' if net >= 0 else '（赤字）'}",
        "",
        "■ 収益内訳",
    ]
    for name, bal in summary["details"].items():
        if bal["type"] == "収益":
            lines.append(f"  {name:<12}  {bal['balance']:>10,}円")

    lines += ["", "■ 費用内訳"]
    for name, bal in sorted(
        [(k, v) for k, v in summary["details"].items() if v["type"] == "費用"],
        key=lambda x: -x[1]["balance"],
    ):
        lines.append(f"  {name:<12}  {bal['balance']:>10,}円")

    return "\n".join(lines)


@mcp.tool()
def add_account(account_name: str, account_type: str) -> str:
    """
    新しい勘定科目を追加します。

    引数:
      account_name: 科目名。追加する科目の名前
      account_type: 種別。「資産」「負債」「資本」「収益」「費用」のいずれか
    """
    try:
        acc = add_account(account_name, account_type)
        return f"✅ 科目「{acc['name']}」（{acc['type']}）を追加しました（ID: {acc['id']}）"
    except ValueError as e:
        return f"❌ エラー: {e}"


if __name__ == "__main__":
    mcp.run()
