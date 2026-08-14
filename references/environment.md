# Android SDK and emulator environment

Android command-line tooling is a Core developer environment, not just a GUI
app. Homebrew supplies Java and the command-line tools. Command-line tools 22
and newer introduce `android sdk` as the preferred package-management surface
and mark `sdkmanager` deprecated; the latter remains the compatibility path for
the established license and deterministic install workflow below.

The first `android` invocation downloads and unpacks its embedded CLI and shows
the Android SDK terms and metrics notice. Treat this as a network-visible
bootstrap step on a new Mac. Do not automate acceptance of changed terms; keep
metrics disabled when the installed CLI supports a non-interactive opt-out.

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
command -v java android sdkmanager adb emulator avdmanager
java -version
android --sdk="$ANDROID_SDK_ROOT" sdk list '*'
sdkmanager --list | sed -n '1,20p'
emulator -list-avds
adb version
```

`android sdk list '*'` is the preferred read-only inventory and also reports
available updates. Keep the `sdkmanager` check while legacy license/install
automation remains in use. Migrate mutation commands only after testing their
prompt, terms, metrics, package-name, and unattended-execution behavior on a
clean machine.

Start only when an Android workflow is in scope:

```sh
emulator -avd kirara-api-35 -no-snapshot-load
```

## AVD storage cleanup

Treat an AVD and its Quick Boot snapshots as different actions. Inspect first:

```sh
emulator -list-avds
du -sh "$ANDROID_AVD_HOME"/*.avd 2>/dev/null
find "$ANDROID_AVD_HOME" -type d -name snapshots -prune -print
```

When the virtual device is still needed but snapshots are not, fully stop the
emulator and remove only that AVD's `snapshots/` directory after an exact path
preview. The next launch is a cold boot; installed apps and writable device
data remain. Verify with `-no-snapshot-load` and a fresh size measurement.

Deleting an entire AVD removes its virtual device definition, writable system
image, installed apps, settings, and snapshots. Require the user to name the
AVD and confirm that broader loss, then use the supported owner:

```sh
avdmanager delete avd --name NAME
```

After either action, run `emulator -list-avds`, verify the exact AVD path, and
record measured bytes only in machine-local state. Never infer permission to
delete SDK system images shared by other AVDs.

Record package versions, measured download/install bytes, selected ABI, AVD
name, and verification timestamps under machine-local state. Never commit SDK
licenses, emulator snapshots, device data, or credentials.
