---
component_id: "perplexity"
name: "Perplexity"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "official_web"
allowed_sources: ["official_web"]
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://www.perplexity.ai/personal-computer"
bundle_identifiers: ["ai.perplexity.macv3"]
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

## 来源说明

Perplexity 的 Mac app 必须从官网获取。Mac App Store 版本属于旧版：其 Bundle ID
和能力集合不同，不接受为最终安装来源。发现 App Store receipt 时，先退出并删除
旧 App Store bundle，再下载和安装官网版本；不要保留旧包或把它作为回滚版本。
官网版本安装后仍需验证版本、Bundle ID、启动和所需权限。只删除旧 App bundle，
不要删除 Perplexity 用户数据或登录信息。

来源检查命令：

```sh
test ! -f "/Applications/Perplexity.app/Contents/_MASReceipt/receipt"
```
