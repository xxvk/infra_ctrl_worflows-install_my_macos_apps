---
component_id: "trae-work"
name: "TRAE Work"
category: "AI development"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://www.trae.ai/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# TRAE Work

TRAE Work contains application data plus an AI-agent runtime. Under its support
tree, VM/runtime tools and sparse disk images are not generic caches. A large
logical image can have small allocated bytes; compare both before proposing
storage work. Never remove `ModularData/ai-agent/vm/tools`, a runtime image, or
workspace/session data merely because Mole reports a large logical size.

Only logs and explicitly named vendor caches may enter review after TRAE Work
and its agent processes are fully quit. Verify the app launches, the agent
runtime starts, and an existing workspace remains available after any approved
cleanup. Productizing VM cleanup belongs to the 0.6 App Adapter layer and must
define rebuild, account, rollback, and sparse-image behavior first.

## Storage recovery boundary

Measure `ModularData/ai-agent/vm/tools` and `ModularData/ai-agent/vm/vms`
separately with allocated-byte-aware tools. A `data.img` may advertise tens of
gigabytes of logical capacity while occupying only a few MiB locally; never
rank its logical capacity as reclaimable space or combine it with the tools
directory.

TRAE's support community documents `vm/tools` as a downloadable SOLO work
environment cache. It may be removed only as a manual, high-impact recovery
when all of the following are explicit:

- the user accepts that prior SOLO local environments may require
  reconfiguration;
- TRAE Work and every related agent/helper process are fully quit;
- the exact allocated size is measured immediately before the action;
- no workspace, session database, or sibling `ModularData` content is included;
- the next launch is expected to download the required tools again.

Reference: [TRAE community guidance for a large `vm/tools`
directory](https://forum.trae.cn/t/topic/17711). Until a TRAE Adapter owns a
transaction and verification contract, this remains a visible manual handoff,
not a public `safe_cache` allowlist rule. Verify the rebuilt environment and
measure the volume again after the next launch.

## Update source boundary

TRAE Work and TRAE IDE are separate products. Homebrew casks `trae` and
`trae-cn` install `Trae.app` or `Trae CN.app`, described as the Adaptive AI
IDE. They do not update the `TRAE SOLO.app` bundle used by TRAE Work. No
`trae-work` or `trae-solo` Homebrew cask is currently available, so never
install the IDE cask as an update substitute.

For an existing TRAE Work installation, use **TRAE Work → Check for Updates…**
and read back the result. If no update is available, leave the bundle and
runtime untouched. If an update is offered, allow the signed in-app updater to
finish, relaunch the app, then verify the bundle version, Work/Code surfaces,
existing workspace access, and allocated size. Use the official TRAE Work
download page only when the in-app updater cannot complete.

Measure the app bundle and support tree separately and under the same process
state. Agent logs, temporary files, and sparse VM allocation can fluctuate when
TRAE Work launches or checks for updates; a small support-tree decrease is not
evidence that an update occurred or that a durable cleanup succeeded. Require
a changed bundle version or signed updater result for update evidence, then
run a fresh allocated-size comparison after the app is quit.
