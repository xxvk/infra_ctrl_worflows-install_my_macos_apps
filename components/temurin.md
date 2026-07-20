---
component_id: "temurin"
name: "Temurin Java"
category: "Developer runtime"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "temurin"
brew_formula: null
official_url: "https://adoptium.net/temurin/"
check_command: "java -version"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 200000000
download_estimate_method: "homebrew_cask_metadata"
---
# Temurin Java

Core Java runtime for Android command-line tools, Gradle/Maven builds, and
other developer workflows. Install from Homebrew:

```sh
brew install --cask temurin
```

Verify in a fresh login shell with `java -version`. Do not change the default
Java runtime or `JAVA_HOME` automatically when multiple JDKs are installed;
make that a separate reviewed configuration step.
