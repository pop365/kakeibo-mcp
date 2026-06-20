# 家計簿MCP

複式簿記の家計簿をClaude（チャット）から操作するMCPサーバー。

## セットアップ

```bash
pip install mcp
```

## Claude Desktop への登録

`claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "家計簿": {
      "command": "python",
      "args": ["C:/path/to/kakeibo_mcp/server.py"]
    }
  }
}
```

設定ファイルの場所:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

## 使い方

Claude に話しかけるだけ:

```
「今日スーパーで3000円使った」
「先月の収支を見せて」
「6月の残高試算表」
「交際費という科目を追加して」
```

## 使えるツール

| ツール | 説明 |
|--------|------|
| 科目一覧 | 登録科目を表示 |
| 仕訳記録 | 仕訳を1件追加 |
| 仕訳一覧 | 仕訳を月別に表示 |
| 仕訳削除 | 仕訳を削除 |
| 残高試算表 | 残高試算表を表示 |
| 月次収支 | 月の収支サマリー |
| 科目追加 | 新しい科目を追加 |

## データ保存先

`data/kakeibo.json`（サーバーと同じフォルダ）
