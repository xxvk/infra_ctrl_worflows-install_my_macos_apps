# Android SDK and emulator environment

Android command-line tooling is a Core developer environment, not just a GUI
app. Homebrew supplies Java and the command-line tools; `sdkmanager` supplies
the Emulator, ADB, Android platforms, and system images.

For a complete Emulator workflow, `sdkmanager` is the single owner of
`platform-tools`/ADB. Do not install the standalone Homebrew
`android-platform-tools` cask alongside it. On a Mac migrated from the older
cask, verify the SDK-managed `adb` first, then remove only the duplicate cask:

```sh
brew uninstall --cask android-platform-tools
```

This does not remove the SDK Manager copy under `ANDROID_SDK_ROOT`.

## Homebrew prerequisites

```sh
brew install --cask temurin
brew install --cask android-commandlinetools
```

The SDK root must be derived from Homebrew rather than hard-coded:

```sh
export ANDROID_SDK_ROOT="$(brew --prefix)/share/android-commandlinetools"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_AVD_HOME="$HOME/.android/avd"
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$PATH"
```

Add one idempotent block to the active user's login shell (`~/.zprofile` for
zsh, `~/.bash_profile` for bash), preserving unrelated content. Do not write
credentials or machine-specific absolute Homebrew paths.

## SDK packages by architecture

Apple Silicon uses `arm64-v8a`; Intel uses `x86_64`. QEMU is provided by the
Android Emulator package and must not be installed separately for this
workflow.

```sh
sdkmanager --sdk_root="$ANDROID_SDK_ROOT" --licenses
sdkmanager --sdk_root="$ANDROID_SDK_ROOT" \
  platform-tools emulator platforms\;android-35 \
  "system-images;android-35;google_apis;${ANDROID_ABI}"
```

Set `ANDROID_ABI=arm64-v8a` on Apple Silicon and `ANDROID_ABI=x86_64` on Intel.
Create one AVD only after the package installation succeeds:

```sh
echo no | avdmanager create avd \
  --name kirara-api-35 \
  --package "system-images;android-35;google_apis;${ANDROID_ABI}" \
  --device pixel_6
```

Verify the environment in a fresh login shell:

```sh
command -v java sdkmanager adb emulator avdmanager
java -version
sdkmanager --list | sed -n '1,20p'
emulator -list-avds
adb version
```

Start only when an Android workflow is in scope:

```sh
emulator -avd kirara-api-35 -no-snapshot-load
```

Record package versions, measured download/install bytes, selected ABI, AVD
name, and verification timestamps under machine-local state. Never commit SDK
licenses, emulator snapshots, device data, or credentials.
