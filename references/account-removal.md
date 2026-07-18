# macOS 本地账户删除

仅在用户明确确认账户名和不可逆删除后执行。该流程删除本地账户记录及其主文件夹；它不会删除对应的 Apple Account、云端数据或远程服务账户。

## 删除前检查

1. 列出目标账户和当前登录会话：

   ```sh
   who
   ls -ld /Users/*
   ```

2. 绝不删除当前登录账户，也不要删除唯一管理员。确认至少保留一个可用管理员账户。
3. 检查目标账户是否承载 LaunchAgents、自动化任务、SSH/GPG 密钥、Git 项目、浏览器配置、Obsidian vault、AI 模型、Docker/OrbStack 数据或云盘同步内容。
4. 如果用户要求直接删除，明确说明主文件夹和其中数据会被永久删除；如用户尚未确认，先停止。

## 执行

优先使用 macOS 的 `sysadminctl`，而不是直接编辑目录服务：

```sh
sudo sysadminctl -deleteUser <username>
```

一次只处理已确认的账户列表。需要管理员认证时，在可见 Terminal 中执行，让用户自行输入密码；不得把密码传入命令、日志、Markdown 或 `state/`。

`sysadminctl` 通常会终止目标账户进程、删除账户记录、删除主文件夹和 Public share point。不要在此之前运行宽泛的 `rm -rf /Users/*`。

## 删除后验证

```sh
ls -1 /Users
for u in <deleted_users>; do
  test ! -e "/Users/$u" && echo "ABSENT /Users/$u"
done
who
id <remaining_admin>
```

确认目标账户不再登录、主文件夹不存在、保留管理员仍具备管理员组权限。只有在用户明确要求时，才清理账户之外的共享缓存或外部项目目录；不要按用户名模糊匹配删除共享数据。

## 记录

写入被忽略的 `state/remove-macos-accounts-YYYYMMDD.json`：删除的用户名、主文件夹路径、执行时间、验证结果和保留的管理员账户。不要把本机当前账户列表、路径或大小写入组件 Markdown 或 catalog。
