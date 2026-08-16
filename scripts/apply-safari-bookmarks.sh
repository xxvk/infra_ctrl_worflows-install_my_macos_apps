#!/usr/bin/env bash
# apply-safari-bookmarks.sh — 执行 17 条新增 + 1 条删除（macos-data CLI CRUD）
#
# 前置（硬性）：
#   1. Safari 必须完全退出（pgrep Safari 为空），否则 CLI fail closed。
#   2. 本脚本只做 local_only 编辑；iCloud 同步由用户重开 Safari 触发。
#
# 安全链（每条操作）：
#   dry-run（取 sourceSHA256Before）→ apply（带 expectedSourceSHA256 + 精确确认）
#   → read-back（list/query 验证存在）
#
# 用法：
#   ./apply-safari-bookmarks.sh          # 执行（含每项 read-back）
#   ./apply-safari-bookmarks.sh --dry    # 只跑全部 dry-run，不写
#
# 失败模式：任一项 apply 失败即停止（不继续用旧哈希强写）。

set -euo pipefail

export PATH="/opt/homebrew/bin:$PATH"
MACOS_DATA="${MACOS_DATA:-macos-data}"

FOLDER31="safarifolder_b1c3aa866fca385cdac25c4a0e64c365d7dde78bf794d3cc93c1080e24d28d5d"
FOLDER13="safarifolder_51562b45c4c634eccef27691dc05626cacaad41b37e0bc1c0285e761238c7b0d"
FOLDER52="safarifolder_1fa884d3982a35aba9de4c56eb7f320f64eca82d9e0a9f4d5ba793a2340cee45"
FOLDER42="safarifolder_b66d56468eddc3392f5b3d06287ad05c9001a251e476a227b6fb0780fcc866fc"
FIXTURE_ID="safaribookmark_aaa540bf490bb820a82da5fb61d5fc12b627ec2433b62fc7eb7b4ef2621d345e"
FIXTURE_URL="https://example.com/macos-data-safari-feasibility/67d369a5-dd33-4035-a6ff-184ab9738228"

MODE="${1:-apply}"
[[ "$MODE" == "--dry" ]] && echo "DRY-RUN 模式：只验证，不写盘" || true

# ── 前置检查 ─────────────────────────────────────────────────────────────
if pgrep -x Safari >/dev/null 2>&1; then
  if [[ "$MODE" == "--dry" ]]; then
    echo "⚠️ Safari 正在运行（dry-run 只读不受影响）；--apply 前必须退出 Safari。"
  else
    echo "❌ Safari 正在运行。CLI 写操作要求 Safari 完全退出（local bookmark writes require Safari fully quit）。" >&2
    exit 1
  fi
else
  echo "✅ Safari 已退出，可执行写操作。"
fi

# ── 新增书签：文件夹ID|标题|URL ──────────────────────────────────────────
CREATE_LIST=(
  "$FOLDER31|arXiv AI|https://arxiv.org/list/cs.AI/recent"
  "$FOLDER31|Hugging Face Blog|https://huggingface.co/blog"
  "$FOLDER31|Hugging Face Papers|https://huggingface.co/papers"
  "$FOLDER31|Google DeepMind Blog|https://deepmind.google/"
  "$FOLDER31|SemiAnalysis|https://www.semianalysis.com/"
  "$FOLDER13|GitHub|https://github.com/"
  "$FOLDER13|MDN Web Docs|https://developer.mozilla.org/"
  "$FOLDER13|Homebrew|https://brew.sh/"
  "$FOLDER13|Node.js|https://nodejs.org/en"
  "$FOLDER52|JLPT 官网|https://www.jlpt.jp/"
  "$FOLDER52|AnkiWeb|https://ankiweb.net/"
  "$FOLDER42|Finviz|https://finviz.com/"
  "$FOLDER42|TradingView|https://www.tradingview.com/"
  "$FOLDER42|Macrotrends|https://www.macrotrends.net/"
  "$FOLDER42|StockAnalysis|https://stockanalysis.com/"
  "$FOLDER42|TradingEconomics|https://tradingeconomics.com/"
)

pass=0; fail=0
for entry in "${CREATE_LIST[@]}"; do
  IFS='|' read -r folder title url <<< "$entry"

  # 1) dry-run：拿 sourceSHA256Before
  payload="{\"parentID\":\"$folder\",\"index\":0,\"title\":\"$title\",\"url\":\"$url\"}"
  dry_json="$(printf '%s' "$payload" | "$MACOS_DATA" safari bookmarks create --stdin --format json)"
  hash_before="$(printf '%s' "$dry_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["sourceSHA256Before"])')"

  if [[ "$MODE" == "--dry" ]]; then
    echo "[dry] $title -> dry-run OK (hash=${hash_before:0:12}...)"
    continue
  fi

  # 2) apply：带 expectedSourceSHA256（无需确认短语，create 非破坏性）
  apply_payload="{\"parentID\":\"$folder\",\"index\":0,\"title\":\"$title\",\"url\":\"$url\",\"expectedSourceSHA256\":\"$hash_before\"}"
  apply_json="$(printf '%s' "$apply_payload" | "$MACOS_DATA" safari bookmarks create --stdin --apply --format json)"
  apply_ok="$(printf '%s' "$apply_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); ok=d.get("ok") is True and d["data"].get("dryRun") is False and d["data"].get("verification")=="readback_confirmed"; print("yes" if ok else "no")' 2>/dev/null || echo no)"
  if [[ "$apply_ok" != "yes" ]]; then
    echo "❌ apply 未确认: $title"; echo "$apply_json" | head -8; fail=$((fail+1)); break
  fi
  new_id="$(printf '%s' "$apply_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"].get("targetID",""))' 2>/dev/null || true)"

  # 3) read-back：get 新 ID 验证存在
  if [[ -n "$new_id" ]] && "$MACOS_DATA" safari bookmarks get --id "$new_id" --format json 2>/dev/null | grep -q '"ok"' ; then
    echo "✅ 新增: $title (read-back OK, id=${new_id:0:12}...)"
    pass=$((pass+1))
  else
    echo "⚠️ apply 成功但 read-back 未确认: $title"; fail=$((fail+1))
  fi
done

# ── 删除测试残留（需精确确认短语）────────────────────────────────────────
if [[ "$MODE" != "--dry" ]]; then
  echo ""
  echo "--- 删除测试残留 fixture ---"
  del_payload="{\"id\":\"$FIXTURE_ID\"}"
  del_dry="$(printf '%s' "$del_payload" | "$MACOS_DATA" safari bookmarks delete --stdin --format json)"
  del_hash="$(printf '%s' "$del_dry" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["sourceSHA256Before"])')"
  del_payload2="{\"id\":\"$FIXTURE_ID\",\"expectedSourceSHA256\":\"$del_hash\"}"
  del_json="$(printf '%s' "$del_payload2" | "$MACOS_DATA" safari bookmarks delete --stdin --apply --confirm "DELETE SAFARI BOOKMARK" --format json)"
  if printf '%s' "$del_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); ok=d.get("ok") is True and d["data"].get("dryRun") is False and d["data"].get("verification")=="readback_confirmed"; print("yes" if ok else "no")' 2>/dev/null | grep -q yes; then
    echo "✅ 删除测试残留 (read-back confirmed)"
    pass=$((pass+1))
  else
    echo "❌ 删除失败:"; echo "$del_json" | head -8; fail=$((fail+1))
  fi
fi

echo ""
echo "=== 结果: 成功 $pass / 失败 $fail ==="
[[ "$fail" -eq 0 ]] || exit 1
echo "⚠️ 记住：这些是 local_only 编辑。重开 Safari 触发 iCloud 同步。"
