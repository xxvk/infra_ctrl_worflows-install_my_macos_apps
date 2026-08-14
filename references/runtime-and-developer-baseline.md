# Runtime and developer baseline

Load this reference only when the current task uses this domain. Its rules were moved verbatim from the original skill entry point during RC-05.

## Contents

- Version and product roadmap
- Mission: one-sync, ready-to-use Mac
- Shared Python Core policy
- JavaScript and TypeScript runtime ownership
- Android developer environment
- Whisper model selection
- Optional audio model catalog

## Version and product roadmap

Read `VERSION` as the repository version source of truth. Read
[`release-roadmap.md`](release-roadmap.md) when planning
new capabilities, assigning work to a release, or evaluating whether a change
is a patch, minor release, or 1.0 product requirement. A
`release_candidate` may be described as an implemented baseline only when its
referenced scripts, settings, and verification paths exist, but it must not be
described as released. Only a `shipped` item may be described as released, and
its release gates and evidence must be complete.

Read
[`release-acceptance-matrix.json`](release-acceptance-matrix.json)
as the cumulative contract bound to the current `VERSION`. Do not describe an
`interface_limited`, `deferred`, or `excluded` capability as supported. Before
making release-status claims, run `python3 scripts/validate_release_contract.py`;
every supported row must retain existing repository evidence.

Read [`product-ideas.md`](product-ideas.md) when evaluating future unassigned
capabilities. Version 0.8.0 is committed to WeChat group lifecycle management,
and 0.9.0 is committed to iPhone intelligence and Home Screen lifecycle through
iPhone Mirroring. Ideas and portfolios in the idea pool remain candidates, not
commitments; assign one to the roadmap only after the user explicitly selects
it.

Version changes, Git tags, releases, and App Store submissions are separate
actions. Update `VERSION` only when the release scope and acceptance gates are
met; never create a tag, commit, release, or submission without explicit user
authorization.

## Mission: one-sync, ready-to-use Mac

The purpose of this repository is reproducible Mac bootstrap: after one
successful sync, a new Mac should reach the user's intended working state
through a bounded sequence of scan, install, authorize, configure, and verify
steps. This is more than an app list; it is the durable definition of the
machine's reusable operating baseline.

Keep the baseline in four layers:

- Tracked policy and desired configuration: `components/`, `references/`,
  `settings/`, `scripts/`, and this skill.
- iCloud-synced, Git-ignored Private configuration: user-approved personal identifiers,
  account/profile mappings, names, and preferences under `Private/`. Follow
  [`configuration-layers.md`](configuration-layers.md)
  for deterministic merge and migration rules. Preserve all existing tracked
  configuration until its consumer has a tested backward-compatible migration;
  do not delete or silently relocate it.
- Machine-local observations: the directory resolved by
  `scripts/state_paths.py`, including detected versions, paths, current
  permission observations, install logs, and cleanup measurements. The tracked
  `state/` directory is only a compatibility locator and contains no runtime
  observations.
- User-controlled secrets and grants: never export passwords, tokens, raw TCC
  databases, private keys, session material, or private document contents.
  Record the required permission, reason, user action, and verification result
  instead; the user approves the actual grant on each Mac.

Portable expected operational state belongs in
[`../settings/bootstrap-operational-baseline.yaml`](../settings/bootstrap-operational-baseline.yaml).
This includes permission requirements, desired Login Item/LaunchAgent intent,
DNS/SmartDNS/VPN topology, and service verification contracts. It does not
make a current TCC grant portable, copy a startup database, or copy network
credentials. Each new Mac must apply or authorize the intent locally and then
write its own machine-local observation for drift comparison.

The bootstrap order is staged: establish the machine baseline; inventory
required permissions; export and review allowlisted user preferences; install
Core components; request sign-ins, licenses, and device pairing; apply
approved policies; then run a final drift audit. Do not turn a broad `defaults`
dump or the TCC database into configuration. Every new preference or
permission needs a named purpose, read/check method, apply method, and
verification method.

### JavaScript and TypeScript runtime ownership

Node 24 LTS managed by fnm is the Core interactive runtime. A fresh login shell
must resolve `node`, `npm`, and the npm global prefix from fnm's Node 24
installation. Automation installs Core npm-global packages only through
`fnm exec --using=24 npm`; a bare `npm install --global` is prohibited because
its destination depends on the caller's PATH.

Homebrew's unversioned `node` formula is a separate dependency runtime. Keep it
while `brew uses --installed node` lists formulas such as Mermaid CLI,
TypeScript, or Gemini CLI. Their launchers may intentionally bind to
`/opt/homebrew/opt/node/bin/node`; do not relink keg-only `node@24` over that
path merely to make both runtimes report the same major.

The resulting ownership boundary is:

```text
fnm Node 24 -> interactive development, npm, Core npm-global tools
Homebrew node -> Homebrew formula dependencies with formula-owned launchers
```

Before migrating an existing npm-global package, record its current owner,
version, executable link, global prefix, and size. Install the exact catalog
version under fnm Node 24, verify the command and account-dependent workflow,
then request separate approval before deleting the prior prefix copy.

### Shared Python Core policy

Python packages are managed as one tracked package set, not as individual
macOS catalog applications. The current shared environment is:

```text
~/.local/share/python/core/.venv
```

Its source of truth is:

```text
references/python-core/pyproject.toml
references/python-core/uv.lock
```

The runtime is Python 3.14 and the package manager is Homebrew `uv`. Keep the
default Core small and use uv dependency groups for `audio`, `data`, `llm`,
`agent`, and `dev`. The shared environment saves duplicate wheels across
repos, but it is not permission to install every ML framework into one
environment.

Install or refresh only from the reviewed manifest:

```sh
cd references/python-core
UV_PROJECT_ENVIRONMENT="$HOME/.local/share/python/core/.venv" \
  uv sync --locked --all-groups
```

Use `--group <name>` when a workflow needs only part of the package set. Do
not use `pip install --system` or `--break-system-packages` for this baseline.
Do not add large optional frameworks such as `whisperx`, `pyannote.audio`,
`ray`, `mlflow`, `llama-cpp-python`, vector databases, or multiple Agent
frameworks to the shared environment without a separate compatibility and
storage review. They may downgrade or replace MLX/data dependencies and should
normally receive their own uv environment.

The shared `.venv` and model caches are machine-local state, not tracked
policy. Record package versions, download/install measurements, and timestamps
under machine-local state; never record tokens, credentials, personal audio, or
model contents. Mole or other cleanup tools must not receive
`~/.local/share/python` as a purge path.

### Android developer environment

Android command-line tools, platform-tools/ADB, Java, and the Emulator are
Core developer dependencies. Follow [`environment.md`](environment.md)
for architecture-specific SDK packages and AVD setup. Derive all SDK paths
from `$(brew --prefix)`; Apple Silicon uses `arm64-v8a`, Intel uses `x86_64`.
QEMU arrives with the Android Emulator package and is not a separate Core
Homebrew install. `sdkmanager` is the sole owner of platform-tools/ADB for
this workflow; if a legacy `android-platform-tools` cask is present, verify
the SDK-managed binaries before removing only that duplicate cask. Treat
Java/cmdline-tools cask receipts as prerequisites only:
the environment is incomplete until `sdkmanager`, `adb`, `emulator`, and
`avdmanager` resolve in a fresh login shell and the selected AVD is listed.

Treat an SDK system image as a separately removable asset, not as the Android
toolchain itself. Before reclaiming one, list registered AVDs and installed SDK
packages, then prove that no retained AVD references the exact image package.
Use the SDK owner's exact package operation rather than deleting its directory:

```sh
SDK_ROOT="$(brew --prefix)/share/android-commandlinetools"
"$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" \
  --sdk_root="$SDK_ROOT" --uninstall \
  'system-images;android-35;google_apis;arm64-v8a'
```

The package identifier above is an example and must come from the current
inspection. After removal, require the exact image to be absent while
`platform-tools`, the intended `platforms;android-*`, Emulator, `adb`, and
`scrcpy` remain available. A warning from an independent Emulator launch or
version probe is a separate compatibility finding; record it without
attributing it to image removal unless a before/after test proves causation.

### Whisper model selection

The `audio` group provides `mlx-whisper`; model weights are downloaded
separately into the user Hugging Face cache and must not be placed in the
repository or the shared venv. Choose models by the target Mac's available
resources:

| Profile | Model | Approximate cache size | Use |
| --- | --- | ---: | --- |
| Resource-constrained | `mlx-community/whisper-large-v3-turbo` | 1.61 GB | Fast everyday transcription |
| Large-RAM Mac | `mlx-community/whisper-large-v3-mlx` | 3.08 GB | Highest transcription accuracy and translation workflows |
| Ample disk/RAM | Download both models | 4.69 GB | Keep Turbo for speed and large-v3 for quality/translation |

Turbo is the default when memory is limited; large-v3 is preferred when RAM
is ample. The two models can coexist without changing Python dependencies.
Record model IDs, cache paths, measured sizes, and download timestamps in
machine-local state. Do not download model weights automatically when only the
Python package is requested; model download is a separate, size-visible step.
Treat `~/.cache/huggingface/hub` as a model-asset directory, not disposable
application cache. Mole and other automatic cleanup workflows must not delete
or purge it. Scans should report its total size and model subdirectories, but
deletion requires an explicit model-removal action. If a cleanup tool supports
a whitelist, protect `~/.cache/huggingface` there as defense in depth.

For an explicitly approved model removal, bind the action to one inspected
model ID and its exact `models--<owner>--<model>` cache root. Recheck its size,
fingerprint, and open-file/process evidence immediately before deletion. Never
remove the Hugging Face hub root, sibling model directories, shared Python
environment, or Mole whitelist as part of that action. Verify the target model
is absent and every named retained model is still present, then measure the
volume's free bytes rather than reporting the directory's prior size as saved
space. The rollback is a later model redownload; there is no content-level
local rollback after deletion.

For Mole, this protection is part of the cross-device baseline. After Mole is
installed or detected, preserve existing entries and ensure this line exists:

```sh
mkdir -p "$HOME/.config/mole"
touch "$HOME/.config/mole/whitelist"
grep -qxF '~/.cache/huggingface' "$HOME/.config/mole/whitelist" || \
  printf '%s\n' '~/.cache/huggingface' >> "$HOME/.config/mole/whitelist"
```

Verify the resulting file before cleanup. This is local per-device
configuration and should be recreated during deployment rather than stored in
tracked policy.

### Optional audio model catalog

The tracked [`audio-model-catalog.yaml`](audio-model-catalog.yaml)
contains optional ASR weights. These are not macOS `.app` bundles and must not
be mixed into the App Store/Homebrew application catalog. Every such entry has
the `audio` tag, an explicit model ID, source URL, precision, approximate
download size, RAM envelope, and a verification command. Download at most one
large audio model at a time on a 16 GB Mac, and keep the existing Whisper
models as the comparison baseline until a user-owned Japanese meeting sample
has been evaluated.

For the current 16 GB M4 profile:

- Prefer **8-bit** for `Qwen3-ASR-1.7B` as the quality-first default. Its MLX
  conversion is about 2.46 GB and is the safest balance for long Japanese
  meetings. Use the MLX 4-bit conversion (about 1.5 GB) only as a fallback when
  memory pressure or swap is observed; do not silently replace the 8-bit model.
- `Kotoba-Whisper-v2.2` remains the latest Kotoba v2.x release found in the
  catalog. It is F32 and the official model is kept unquantized by default
  because its main value is Japanese transcription plus punctuation and
  diarization. Quantized community conversions may be used only after checking
  their provenance and measuring Japanese accuracy; diarization dependencies
  add a separate RAM and license review.
- Granite 4.0 1B Speech MLX 8-bit, Cohere Transcribe 03-2026 MLX 8-bit, and
  ReazonSpeech-k2-v2 INT8 are optional `audio` models. They are not Core app
  installations and are never downloaded as part of a normal app bootstrap.
