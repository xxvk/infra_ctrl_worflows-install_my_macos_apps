# 灾难恢复 Runbook：Mac 丢失/损坏/换新机

本文档把仓库里分散的脚本串成一条从「拿到一台全新/裸机 Mac」到「恢复到已知基线」的完整顺序。每一步都引用已存在的脚本或文档，不新增功能；本文件本身是只读操作指引，不持有任何机器状态或密钥。

适用场景：现有 Mac 丢失、被盗、主板损坏需要更换，或购入一台新 Mac 作为主力机。**不适用**于日常的偏好漂移修复——那种情况见 [`scripts/bootstrap_verify.py`](../scripts/bootstrap_verify.py) 的 drift 报告，无需走完整流程。

## 前提条件

- 你需要能访问：Apple Account（App Store 购买记录）、GitHub 账号（本仓库和其他私有仓库）、密码管理器（当前为 macOS/iCloud 系统 Keychain，见 [`settings/manual-actions.yaml`](../settings/manual-actions.yaml)）。
- 本仓库（XVK_PM，含本 skill 作为子模块）本身通过 iCloud Drive 同步 + Git 追踪；确保它已经能在新 Mac 上通过 iCloud 或 `git clone` 取回。
- 如果旧机器仍可访问，先按下方「第 0 步」在旧机器上做最后一次基线快照，再开始新机器的恢复。

## 第 0 步（旧机器仍在时，事故发生前）：留下最后一份基线

在旧机器上运行一次完整只读基线，作为对比基准。这一步本身也是[「Time Machine / 备份前置检查」待办](../TODO.md)想要在破坏性操作前强制的同一类检查：

```sh
python3 scripts/bootstrap_macos.py --profile auto
```

确认 `state/bootstrap-*.json` 生成成功，并将该文件手动复制到仓库之外的安全位置（例如导出到密码管理器的安全笔记，或另一台设备）——`state/` 本身被 git 忽略，机器丢失后这份记录也会一并丢失，必须手动带出。

## 第 1 步：取回仓库

在新 Mac 上恢复 iCloud Drive 同步，或直接克隆：

```sh
git clone --recurse-submodules <XVK_PM 仓库地址>
```

确认 `workflows/infra_ctrl_worflows/install_my_macos_apps/` 子模块内容完整（`git submodule status` 无 `-` 前缀）。

## 第 2 步：联网

按 [`settings/manual-actions.yaml`](../settings/manual-actions.yaml) 里的 `wifi-network-connectivity` 检查点（这是全文件里 phase 最前置的一条）——没有网络，第 3 步及之后的所有操作都无法进行。这一步没有脚本，纯手动：加入 Wi-Fi 或接入以太网，确认能访问 App Store 和 GitHub。

## 第 3 步：只读现状扫描

```sh
python3 scripts/bootstrap_macos.py --profile auto
```

这一步跑 App 扫描、容量感知安装计划、权限清单、偏好基线/对比，全部只读，不安装、不改权限、不改偏好。产出 `state/bootstrap-*.json`，把它和第 0 步留下的旧基线并排比较，确认新机器的起点状态被完整记录。

## 第 4 步：账号与密码管理器优先建立

在安装任何需要登录的 App 之前，先确认密码管理器可用（当前是系统/iCloud Keychain，跟随 Apple Account 自动同步）。见 [`settings/manual-actions.yaml`](../settings/manual-actions.yaml) 里的账号检查点列表。**不要**在这一步让 skill 代为输入任何密码/两步验证码；全部由用户在可见界面里手动完成。

## 第 5 步：安装 App

按 [SKILL.md 的 Workflow 章节](../SKILL.md#workflow) 和 [App Store workflow](../SKILL.md#app-store-workflow) 执行：

```sh
python3 scripts/macos_apps.py plan --profile auto
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply
```

一次最多两个 `--only`；Homebrew CLI 类批量最多 5 个；GUI/App Store/需要账号许可证的一次一个。参见 SKILL.md 中列出的所有例外流程（Claude VM 清理、YouTube PlayCover、Bionic 重命名等），不要在这份 runbook 里重复展开。

## 第 6 步：权限与偏好还原

```sh
python3 scripts/macos_permissions.py
python3 scripts/macos_preferences.py
python3 scripts/macos_preferences.py --check
python3 scripts/macos_preferences.py --apply   # 仅在 --check 显示漂移且用户确认后
python3 scripts/macos_preferences.py --check   # 复核 apply 结果
```

如果这次运行的宿主是 Claude 桌面客户端的本地 agent 会话（而非 Terminal.app），先确认 Full Disk Access 授予的是 `/Applications/Claude.app`；见 [`settings/privacy.yaml`](../settings/privacy.yaml) 中记录的这条真实教训。

## 第 7 步：Dock、键盘、Chrome Profile 等设备/机器相关配置

```sh
python3 scripts/macos_dock.py --save-config    # 对比 settings/dock-order.json
python3 scripts/chrome_profiles.py --expected config/chrome-profiles.json --output state/chrome-profiles-inventory.json
```

键盘 K240 profile 按 [SKILL.md 的 Keyboard settings workflow](../SKILL.md#keyboard-settings-workflow) 单独走，包含前台验证 F1/F2/F3/F5/F12 和 Input Monitoring 授权。

## 第 8 步：最终验证

```sh
python3 scripts/bootstrap_verify.py
```

记录缺失的 Core App、来源不匹配、权限漂移、偏好 `--check` 结果，以及可安全重跑的恢复命令。只有这一步全部通过（或已知差异都已被用户接受），才认为这台新机器达到了「一次同步、开箱即用」的基线。

## 恢复不完整时怎么办

- 任何一步失败，先记录失败步骤和原始报错，不要用 `sudo`/`--force` 之类的方式强行绕过。
- 权限类失败几乎总是 TCC/Full Disk Access 没授予正确的宿主进程（见第 6 步）。
- App 缺失但来源标记为 `store_unavailable`，参考 SKILL.md 中「App Store workflow」第 5 条的处理方式，不要用官网下载静默替代。
- 全部记录只进 `state/`；恢复完成后，把哪些配置值得提升为 tracked `settings/` 留给用户人工审阅（这也是仓库既有的 [「审阅并只提交可复用策略」原则](../TODO.md)）。
