#!/usr/bin/env bash
# sort-from-plan.sh — 从 /tmp/<plan>.json 执行书签排序（macos-data CLI move）
#
# 用法: ./scripts/sort-from-plan.sh <plan.json>
# 前置: Safari 完全退出。每项 move: dry-run → apply(expectedSourceSHA256) → read-back。
# 计划格式: [{"id","parentID","index","title"}, ...]（index 降序=从后往前执行）

set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"

if ! pgrep -x Safari >/dev/null 2>&1; then
  echo "✅ Safari 已退出，可执行排序写操作。"
else
  echo "❌ Safari 正在运行。CLI 写操作要求 Safari 完全退出。" >&2
  exit 1
fi

PLAN="${1:-}"
[[ -n "$PLAN" && -f "$PLAN" ]] || { echo "❌ 用法: $0 <plan.json>"; exit 1; }

pass=0; fail=0
count=$(python3 -c "import json; print(len(json.load(open('$PLAN'))))")
for i in $(seq 0 $((count-1))); do
  item=$(python3 -c "
import json
plan = json.load(open('$PLAN'))
it = plan[$i]
print(f'{it[\"id\"]}|{it[\"parentID\"]}|{it[\"index\"]}|{it[\"title\"]}')")
  IFS='|' read -r bid parent idx title <<< "$item"

  dry=$(printf '%s' "{\"id\":\"$bid\",\"parentID\":\"$parent\",\"index\":$idx}" \
    | macos-data safari bookmarks move --stdin --format json)
  hash_before=$(printf '%s' "$dry" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["sourceSHA256Before"])' 2>/dev/null || echo "")

  res=$(printf '%s' "{\"id\":\"$bid\",\"parentID\":\"$parent\",\"index\":$idx,\"expectedSourceSHA256\":\"$hash_before\"}" \
    | macos-data safari bookmarks move --stdin --apply --format json)
  ok=$(printf '%s' "$res" | python3 -c 'import json,sys; d=json.load(sys.stdin); ok=d.get("ok") is True and d["data"].get("dryRun") is False and d["data"].get("verification")=="readback_confirmed"; print("yes" if ok else "no")' 2>/dev/null || echo no)

  if [[ "$ok" == "yes" ]]; then
    echo "  [OK] move #$((i+1))/$count → index=$idx  $title"
    pass=$((pass+1))
  else
    echo "  [FAIL] move #$((i+1))/$count → $title"
    printf '%s' "$res" | head -6
    fail=$((fail+1))
    break
  fi
done

echo ""
echo "=== 排序结果: 成功 $pass / 失败 $fail ==="
[[ "$fail" -eq 0 ]] || exit 1
echo "⚠️ local_only 编辑；重开 Safari 触发 iCloud 同步。"
