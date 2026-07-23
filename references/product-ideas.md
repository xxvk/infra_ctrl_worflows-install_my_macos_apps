# Product idea pool

## Purpose

This document holds product-shaping ideas that are intentionally outside the
committed release roadmap. An idea remains a **candidate** until the user
explicitly assigns it to a version in `release-roadmap.md`.

The product opportunity is larger than an application installer or disk
cleaner. The long-term direction is a local-first **Personal Mac Control
Plane**: a system that understands the user's intended machine state, remembers
decisions, explains consequences, and changes the Mac safely.

Evaluate candidates using five questions:

1. Does the user understand the value within thirty seconds?
2. Does it combine capabilities accumulated in 0.1.0–0.7.0?
3. Does it create durable data, workflow, or trust advantages?
4. Can every consequential action be previewed, approved, measured, and
   reversed where technically possible?
5. Does it strengthen the eventual native macOS product rather than merely add
   another maintenance command?

## Twenty candidates

| # | Idea | Product promise | Strategic advantage | Principal boundary |
| ---: | --- | --- | --- | --- |
| 1 | **Mac Digital Twin** | Visualize applications, data, accounts, permissions, startup items, cloud copies, and dependencies as one living model of the Mac. | Unifies all earlier capabilities behind one defensible data model. | Identity resolution and freshness must be trustworthy. |
| 2 | **Intent OS** | Say “make this a development, travel, presentation, or recovery Mac” and receive a convergent, verified action plan. | Moves the product from command execution to desired-state management. | Intent must never silently broaden authorization. |
| 3 | **Context Capsules** | Package the complete context of a project—tools, environment, bookmarks, notes, SSH metadata, and file relationships—for continuation on another Mac. | Creates a portable unit of work rather than a loose collection of synced files. | Capsules must exclude secrets and licensed/private data by default. |
| 4 | **Multi-Mac Fleet Brain** | Give each Mac a role and compare, coordinate, or repair configuration drift across the personal fleet. | Expands the product from one machine into a personal infrastructure layer. | Raw private machine state must not be copied indiscriminately. |
| 5 | **Reversible Computing** | Show the impact and recovery path of every cleanup or configuration action and provide Undo when technically possible. | Builds the trust needed for a system-management product. | Some cloud deletions, account changes, and secure erasures are not reversible. |
| 6 | **Data Temperature Engine** | Classify data as Hot, Warm, Cold, or Frozen and place it locally, on demand, or in an archive accordingly. | Replaces crude “large file” cleanup with lifecycle intelligence. | Access timestamps and cloud metadata can be incomplete or misleading. |
| 7 | **Recoverability Economy** | Compare local space saved with redownload time, regeneration cost, API cost, bandwidth, and recovery risk. | Treats a gigabyte of cache, model weights, source data, and personal media differently. | Cost estimates require visible assumptions and confidence. |
| 8 | **Why Is This Here?** | Explain who created any folder, why it exists, when it mattered, and what will break if it disappears. | Makes opaque `Library` and application data understandable to normal users. | Ownership inference must remain evidence-based. |
| 9 | **Application X-Ray** | Display an application's bundle, databases, caches, helpers, permissions, network extensions, cloud state, and data relationships. | Creates a compelling native visual surface and foundation for safe cleanup. | Shared containers and cross-app data can make ownership ambiguous. |
| 10 | **App Adapter Marketplace** | Install reviewed storage and lifecycle adapters for WeChat, Claude, Xcode, Adobe, Docker, and other complex applications. | Builds an extensible ecosystem instead of hard-coding every application. | Adapters need signing, schema compatibility, review, and rollback contracts. |
| 11 | **Universal Offload Fabric** | Manage iCloud, Google Drive, Dropbox, NAS, external disks, and local storage through one placement policy. | Solves storage location rather than only deletion. | Providers expose different synchronization and placeholder guarantees. |
| 12 | **Personal Mac SRE** | Continuously identify abnormal growth, broken services, permission drift, background-task changes, and recovery risks. | Turns one-time setup into ongoing reliability operations. | Monitoring must remain quiet, explainable, and resource-efficient. |
| 13 | **Decision Memory Graph** | Remember not only what the user decided, but why, for how long, and which other decisions depend on it. | Reduces repeated work and creates a personalized operational moat. | Private filenames and reasoning need strict local/synced boundaries. |
| 14 | **Cleanroom Work Sessions** | Start an ephemeral workspace and retain only promoted outputs when the task ends. | Prevents storage debt at creation time instead of cleaning it later. | Must not remove an unpromoted artifact the user still needs. |
| 15 | **AI Workload Scheduler** | Choose local Mac, another Mac, or cloud execution based on memory, model size, privacy, speed, energy, and cost. | Uses Apple Silicon and multi-Mac resources as one intelligent compute fabric. | Provider credentials, billing, and private inputs require isolation. |
| 16 | **Personal Knowledge Fabric** | Connect bookmarks, reading lists, notes, documents, screenshots, photos, and projects into a traceable knowledge layer. | Integrates 0.3, 0.4, and 0.7 into one higher-value system. | Canonical-source ownership and privacy rules must be explicit. |
| 17 | **Privacy Firewall** | Explain every new permission, helper, login item, or network extension and recommend allow, time-limit, or revoke. | Makes zero-trust personal computing understandable and actionable. | macOS does not expose supported automation for every permission. |
| 18 | **Disaster Recovery Simulator** | Simulate losing the Mac today and show what is recoverable, what is unverified, and what would be permanently lost. | Converts “ready to restore” from documentation into measurable evidence. | A simulation must never claim recovery without a real restore test. |
| 19 | **Personal Compute Balance Sheet** | Show storage cost, cloud cost, subscription overlap, recovery exposure, background consumption, and maintenance debt. | Gives the user a CEO/CIO view of personal computing assets. | Financial and usage estimates must show source and confidence. |
| 20 | **Explainable Autopilot** | Propose a complete optimization plan, simulate effects, obtain approval, execute, verify, and remember the outcome. | Provides the strongest unified interaction for the eventual native product. | Autonomy must remain bounded by explicit authority and reversible plans. |

## Candidate portfolios

These portfolios are combinations, not roadmap commitments.

### Portfolio A — product-defining

- **Mac Digital Twin**
- **Intent OS**

Digital Twin supplies the unified model; Intent OS lets the user move that
model toward a desired state. This is the current CEO/CTO recommendation
because it creates both a data-model moat and an interaction moat.

### Portfolio B — cross-device continuity

- **Context Capsules**
- **Multi-Mac Fleet Brain**

The product promise becomes: change Macs without losing the working context,
and give every device a deliberate role.

### Portfolio C — storage platform

- **Universal Offload Fabric**
- **Reversible Computing**

The product becomes a trusted placement and lifecycle system spanning local,
cloud, NAS, and external storage.

### Portfolio D — memory-native AI

- **Decision Memory Graph**
- **Explainable Autopilot**

The product learns why the user makes decisions, reduces repeated review, and
offers increasingly useful but still bounded automation.

## Selection record

When the user selects an idea:

1. assign it explicitly to `0.8.0` or `0.9.0` in `release-roadmap.md`;
2. change its roadmap status from `undecided` to `committed`;
3. define user promise, non-goals, architecture, safety boundaries, migration,
   and measurable acceptance gates;
4. keep all unselected ideas in this pool as `candidate`;
5. do not update `VERSION` until the selected release is actually complete.
