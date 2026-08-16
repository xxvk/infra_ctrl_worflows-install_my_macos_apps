# Safari organization and one-level projection

## Boundary

`browser-organization-v1` is the Private source of truth for one reviewed
Safari export. It binds the export SHA-256, fixed two-level taxonomy, folder
rules, item-level exceptions, duplicate resolutions, Reading List status, and
conservative title suggestions. It never authorizes execution or modifies
Safari.

Tracked source contains only the Schema, compiler, policy documentation, and
fictional fixtures. The real instance is
`Private/browser/organization.json`; it is Git-ignored, synchronized by the
surrounding iCloud folder, and created with mode `0600`. Exact export paths and
frozen transaction plans remain machine-local.

## Taxonomy contract

The Private organization keeps the domain/subdomain taxonomy for governance,
quota, review, and archive decisions. Safari projects only the 15 active
subdomains as direct children of its system `Favorites` collection. The
`01`–`05` domains and `99` archive domain are conceptual groupings and must not
be emitted as additional clickable Safari folders.

The conceptual taxonomy remains:

- `01｜事业与项目 🏗️`: `11｜AIM与机器人 🤖`,
  `12｜科技创业与商业项目 🚀`, `13｜产品与开发 🧑‍💻`;
- `02｜内容与创作 🎬`: `21｜视频平台与频道 📺`,
  `22｜虚拟人与互动内容 🧑‍🎤`, `23｜制作、发行与增长 📣`;
- `03｜专业研究 🔬`: `31｜AI、Agent与数据 🧠`,
  `32｜检索、论文与知识产权 🔎`, `33｜学位、证书与职业学习 🎓`;
- `04｜财务与交易 📈`: `41｜金融学习与宏观 🌐`,
  `42｜全球股票研究 📊`, `43｜数字资产与商业交易 ₿`;
- `05｜生活与迁移 🌏`: `51｜移民、签证与旅行 🛂`,
  `52｜语言、社交与个人生活 🗣️`, `53｜消费数码、购物与返点 🎁`;
- `99｜归档 📦`: `91` through `95`, corresponding to the five domains.

Obsidian owns project-specific context. Reading List is a temporary inbox and
does not enter the topic hierarchy.

The import projection is therefore `Favorites -> 11–53`, with one clickable
folder level. Archive folders `91`–`95` remain Private ledger state and are not
included in the active import package.

Directory assignment does not imply display order. Freeze a separate
convergence-bound Private order only after reviewing pinned, core, monitor,
trial, and low-frequency placement for every source. The HTML generator must
reject alphabetical fallback when no complete frozen order is supplied.

## Compile and review

The compiler requires every bookmark to receive exactly one base assignment,
every discovered duplicate group to receive one complete resolution, and every
exported item to appear exactly once. Reviewed counts are assertions, not
inferred acceptance.

```sh
./bin/macomrade review browser-organization \
  ~/Downloads/Safari-Bookmarks.zip \
  --spec /private/tmp/browser-organization-spec.json \
  --output Private/browser/organization.json
```

Preview emits aggregate counts only and writes nothing. Applied persistence
requires the adjacent exact confirmation:

```sh
./bin/macomrade review browser-organization \
  ~/Downloads/Safari-Bookmarks.zip \
  --spec /private/tmp/browser-organization-spec.json \
  --output Private/browser/organization.json \
  --apply --confirm "SYNC PRIVATE BROWSER ORGANIZATION"
```

The write is atomic, refuses a different existing destination, validates the
read-back, enforces mode `0600`, keeps stdout redacted, and performs no Safari
write.

## Frozen plan handoff

`plan browser --organization` converts only bookmark decisions into move,
archive, and delete operations. Reading List `delete_later` and `defer` rows
are excluded. Original titles, URLs, and title suggestions are not copied into
transaction operations.

```sh
./bin/macomrade plan browser ~/Downloads/Safari-Bookmarks.zip \
  --organization Private/browser/organization.json
```

The export hash and every item fingerprint are rechecked. The plan remains
non-executable; `apply browser` continues to return `blocked` until a supported
Safari interface can provide exact mutation and rollback.

## Title suggestions

Original titles are immutable evidence. Suggestions may only normalize
repeated whitespace or remove a trailing site label that exactly matches the
URL host/domain token. They never translate, summarize, or enter a transaction
operation. Link-health scanning, import HTML, GUI automation, and live Safari
mutation are later phases.

## Source evidence retention

The organization JSON stores the source SHA-256 but is not a replacement for
the source export. Preserve the original ZIP byte-for-byte as Private evidence
before deleting it from Downloads. The intended synchronized location is:

```text
Private/browser/evidence/safari-export-YYYY-MM-DD-<sha256-prefix>.zip
```

Evidence is Git-ignored, mode `0600`, and immutable after import. Do not unpack,
rewrite, recompress, or rename it without preserving the hash binding. The
public repository records only this naming and retention policy, never the
private ZIP, URL, title, folder, item ID, or full source hash.

Import is preview-only by default:

```sh
./bin/macomrade review browser-evidence ~/Downloads/Safari-Bookmarks.zip \
  --exported-on YYYY-MM-DD
```

After the redacted counts are reviewed, persistence requires:

```sh
./bin/macomrade review browser-evidence ~/Downloads/Safari-Bookmarks.zip \
  --exported-on YYYY-MM-DD \
  --apply --confirm "IMPORT PRIVATE BROWSER EVIDENCE"
```

The destination name is derived from the reviewed date and first 12 source-hash
characters; callers cannot choose an arbitrary path. The importer validates the
source before and after copying, preserves its exact bytes, writes atomically,
enforces mode `0600`, confirms Git ignore, reparses the destination, refuses
different existing bytes, and emits no path or hash. An identical import is
unchanged. This action does not modify Safari or authorize organization rebase.

## Export drift and reconciliation

An export hash mismatch is expected after Safari content changes. It is a
reconciliation trigger, never permission to overwrite the canonical Private
organization.

The required future flow is:

1. preserve and hash the new source export;
2. compare old and new items inside the same browser/profile/account boundary;
3. inherit unchanged path rules by exact source path;
4. reuse an item-level decision only when its semantic fingerprint remains an
   unambiguous match;
5. return added, removed, changed, ambiguous, and duplicate-membership changes
   to review;
6. recompute title suggestions without changing original titles;
7. validate complete counts and generate a separate versioned candidate;
8. require a fresh exact confirmation before changing the canonical pointer;
9. preserve the previous organization and source evidence for audit/rollback.

The current reconciler implements steps 1 through 7 without changing the
canonical organization:

```sh
./bin/macomrade review browser-reconciliation \
  Private/browser/organization.json \
  ~/Downloads/Safari-Bookmarks-new.zip \
  --reconciled-on YYYY-MM-DD
```

It matches equal-multiplicity semantic fingerprints, reapplies exact source-path
rules, transfers item overrides only for unchanged unambiguous items, and
requires duplicate groups to retain the same fingerprint multiset. New or
changed unresolved items, removed old items, multiplicity ambiguity, and
duplicate membership drift block candidate generation and return redacted
review counts.

When every item reconciles, a separate versioned candidate may be persisted:

```sh
./bin/macomrade review browser-reconciliation \
  Private/browser/organization.json \
  ~/Downloads/Safari-Bookmarks-new.zip \
  --reconciled-on YYYY-MM-DD \
  --apply --confirm "WRITE PRIVATE BROWSER RECONCILIATION CANDIDATE"
```

The candidate is written below `Private/browser/versions/`, validated as a
complete `browser-organization-v1` document, and never overwrites or switches
`Private/browser/organization.json`. Canonical promotion and rollback
acceptance remain unimplemented and require a separate future transaction.
