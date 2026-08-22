#!/usr/bin/env bash
# ⚠️ SUPERSEDED — DOES NOT RUN AS WRITTEN.
#
# This script targets the removed `macos-data safari <noun> <verb> --stdin`
# surface. Two independent things broke it:
#
#   1. Rename + contract change. `macos-data-cli` became `mpia-cli` and 0.9.3
#      replaced adapter/subcommands with `mpia METHOD "/path"`. There is no
#      `--stdin`: `--params` / `--body` accept inline JSON only. Porting the
#      pipes to `--body "$payload"` would put bookmark titles and URLs into
#      process arguments and shell history, which this skill's privacy boundary
#      does not allow. A replacement must solve that first, not paper over it.
#   2. Store schema. mpia 0.9.3 cannot parse Safari 27's Bookmarks.plist
#      (`SAFARI_SCHEMA_UNSUPPORTED`), so no live CLI bookmark path exists on
#      this Mac regardless of syntax.
#
# The folder ids and operation counts below are frozen from one completed 2026
# run; they are not reusable inputs. Kept as a record of the safety chain
# (dry-run -> expectedSourceSHA256 -> apply -> read-back), which the mpia routes
# preserve. Route mapping lives in references/browser-workflow-cli.md.
#
# Delete or rewrite deliberately — do not run.
# sort-safari-bookmarks.sh — 按重要性排序 4 个文件夹的书签（macos-data CLI）
#
# 前置：Safari 完全退出。每项 move：dry-run → apply(expectedSourceSHA256) → read-back。
# 计划：/tmp/safari-sort-plan.json（23 次 move，index 降序=从后往前）
# 输出：每项 [OK] 或 [FAIL]，结尾汇总；任一项失败即停（不继续用旧哈希）。

set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"

if ! pgrep -x Safari >/dev/null 2>&1; then
  echo "✅ Safari 已退出，可执行排序写操作。"
else
  echo "❌ Safari 正在运行。CLI 写操作要求 Safari 完全退出。" >&2
  exit 1
fi

PLAN="/tmp/safari-sort-plan.json"
[[ -f "$PLAN" ]] || { echo "❌ 找不到排序计划 $PLAN"; exit 1; }

pass=0; fail=0
count=$(python3 -c "import json; print(len(json.load(open('$PLAN'))))")
for i in $(seq 0 $((count-1))); do
  # 取第 i 项（保持文件顺序=index 降序）
  item=$(python3 -c "
import json
plan = json.load(open('$PLAN'))
it = plan[$i]
print(f'{it[\"id\"]}|{it[\"parentID\"]}|{it[\"index\"]}|{it[\"title\"]}')")
  IFS='|' read -r bid parent idx title <<< "$item"

  # dry-run
  dry=$(printf '%s' "{\"id\":\"$bid\",\"parentID\":\"$parent\",\"index\":$idx}" \
    | macos-data safari bookmarks move --stdin --format json)
  hash_before=$(printf '%s' "$dry" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["sourceSHA256Before"])' 2>/dev/null || echo "")

  # apply（带哈希）
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
