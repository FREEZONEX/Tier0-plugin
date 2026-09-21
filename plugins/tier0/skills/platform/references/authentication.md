# 连接、登录与授权

## 安装与版本

依赖 Python 3（包装脚本只用标准库）、Tier0 CLI。缺 CLI 时使用现有 npm 安装器（需要 Node.js >=16）：

```sh
npx -y @tier0/cli@0.7.0 install
```

这是本插件核对源码的版本基线，并非宣称最新版本。安装器下载对应平台二进制到 `~/.tier0/bin/`，安装内嵌 Skills 并同步到检测到的 Agent。这些是上游安装器的实际副作用。插件内的参考随插件版本更新；独立 `tier0 skills update` 不会更新本插件缓存。无需为使用本插件再次运行 skills sync。

安装后检查 PATH；必要时用 `~/.tier0/bin/tier0`，再让该目录进入当前进程 PATH。Windows 使用相应用户目录与 tier0.exe。已有 CLI 不自动降级，先检查本版所需 login / auth whoami / --json / --dry-run flags；缺能力再升级。安装失败说明实际原因，不执行任意替代下载脚本。

## 连接步骤

以下 `TIER0_SKILL_DIR` 表示本 SKILL.md 所在目录，由 Agent 从当前技能实际路径确定。

```sh
python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" status
```

默认 SaaS 是 `https://tier0.dev`。已配置的实例应继续复用；不要为了登录覆盖用户的私有部署地址。用户未指定且无已有配置才使用默认地址。`tier0 config --json` 只输出脱敏配置，可以读取 baseURL；不要 cat ~/.tier0/config.json。

未登录时，以确认的实例开始：

```sh
python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" begin --base-url https://tier0.dev
```

返回 `authorization_required`、`verification_url`、临时 `setup_code`、600 秒有效期。这是授权请求，不是已登录。将原始 verification_url 作为可点击链接展示，说明“请在 Tier0 页面登录，选择要连接的工作区并授权”；不改写 URL，不索要密钥。临时 setup_code 仅用于本次授权，不写进项目、文档、版本记录。

开始有界轮询（下方 CODE 替换成刚才返回的值）：

```sh
python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" finish --base-url https://tier0.dev --setup-code CODE
```

begin 和 finish 必须使用同一 base-url。CLI 向 `/api/core/cli-auth/status` 轮询，由 CLI 把凭证保存至 `~/.tier0/config.json`；包装脚本丢弃包含完整 API Key 的原始 stdout，随后执行 whoami，返回白名单身份字段。不得直接运行 `tier0 login --setup-code ... --json`，也不要把原始输出 tee 到日志。

finish 每次最多 45 秒，等待超时不会保留子进程。先执行 status 检查是否已经保存登录；仍未登录且请求未过期时才继续使用同一码轮询。每轮等待期间提供简短进度；用户取消后不重启轮询。授权拒绝时停止；过期需重新生成链接，不能持续使用旧码。

授权成功后说清实际用户、Workspace 和权限，继续用户原请求。身份有效但目标 Workspace 不符时，让用户确认目标并重新授权，不默认在旧 Workspace 执行。

## 配置边界

当前源码在不同命令家族中应用 `TIER0_BASE_URL` / `TIER0_API_KEY` 的方式不一致。helper 检测到这两个环境覆盖时返回配置错误，避免身份检查与业务命令访问不同实例。不要打印变量值；改用同一 CLI profile，或由用户在其终端调整环境后重试。不能仅凭 README 的优先级表推定所有命令一致。

个人 Key 绑定用户和工作区，不等同任意平台权限。最低授权由用户目标决定；不要为了绕过 403 要求 full_access。可按任务检查 whoami 的 permissions，真实请求仍由服务端裁决。

## 失败处理

| 结果 | 处理 |
| --- | --- |
| cli_not_installed | 安装现有 CLI，然后重试状态检查 |
| login_required / authentication | 引导登录；保留用户控制的浏览器授权步骤 |
| different_instance_login_required | 使用用户目标实例重新授权；不要拿旧 Key 调另一个实例 |
| authorization / 403 | 检查实际用户、工作区、权限；说明所需权限，不反复登录 |
| network / 等待超时 | 核对连通性、状态与有效期；不要宣称授权成功 |
| config / 404 | 检查 CLI 配置及该部署是否实现 CLI 授权接口 |
| internal / unexpected output | 可能版本不兼容；检查版本，保留原始输出不回显，不盲目重试写入 |

本版 CLI 未提供 logout 或远端 revoke 命令。不要编造这些命令，也不要将删除本地配置称为撤销远端权限。需要断开时，引导用户在目标平台实际 API Key 管理入口撤销对应 Key；入口和撤销结果须核实。卸载插件也不会自动撤销平台 Key。
