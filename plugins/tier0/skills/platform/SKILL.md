---
name: platform
description: 连接并使用 Tier0 平台。用户要求安装或运行 Tier0 插件、登录授权、查看工作区身份权限，或操作 UNS、Node-RED Flow、MQTT、文件时使用。先检查 CLI 和鉴权，缺少登录时引导浏览器授权；暂不支持应用生成、App 源码上传、建版或发布。
---

# Tier0 平台

通过现有 Tier0 CLI 执行平台操作。用户说“运行 Tier0 插件”“连接 Tier0”时，立即进入下列连接流程，不要求用户提供应用源码或 Scaffold。插件安装本身不会触发登录脚本；首次调用本技能时才检查与引导授权。

## 首次使用与登录

先读取 [连接与鉴权](references/authentication.md)。确定本技能所在目录，将其绝对路径记为 `TIER0_SKILL_DIR`；示例中的变量必须替换为本次安装位置，不能指向开发者机器或旧缓存。

1. 找到 `tier0` 可执行文件（PATH 或 `~/.tier0/bin/tier0`；Windows 为 tier0.exe），检查 `version` 和 `--help`。缺少 CLI 时使用文档中的现有安装器，不另造登录协议。安装插件或连接平台的请求包含安装必要 CLI 的意图；宿主权限审批仍按实际执行要求处理。
2. 用 `python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" status` 检查真实身份。成功则复用登录；展示用户、Workspace 和权限摘要，不重复索要授权。用户指定其他实例时带 `--base-url` 核对。
3. 未配置凭证或凭证失效时运行 helper 的 `begin`；显示返回的原始授权链接，说明需用户在浏览器登录、选择 Workspace 并授权。不要索要密码、验证码或 API Key，不代替用户批准授权。
4. 用同一实例和 setup_code 执行 helper 的 `finish`，每次最多等待 45 秒。等待中及时更新状态；用户取消则停止，过期后按需重新开始。不要把等待超时当成授权成功。
5. `finish` 会回查 whoami；确认 Workspace 符合用户意图后继续原任务。权限不足、网络故障、接口未部署应分别处理，不一律重新登录。

首次仅要求连接时，完成身份验证后说明下方可用能力，不自行创建资源。已有登录后每个会话首次操作及更换实例/工作区时复核；不在每个普通查询前重复登录。

## 当前能力

任务执行前读取对应参考。`references/cli/` 来自已有 Tier0-skill，不是需要另外安装的插件。该目录中 `uns/...`、`flow/...` 等跨模块引用以 `references/cli/` 为根；模块内 `references/...` 以相应模块目录为根。

| 用户任务 | 已有 CLI 入口 | 读取 |
| --- | --- | --- |
| 连接、身份、工作区和权限 | login、auth whoami、config、doctor | [鉴权](references/authentication.md) |
| 服务信息与连通性 | api /openapi/v1/info | [服务信息](references/cli/info/info.md) |
| UNS 浏览、搜索、当前值、历史、建节点、改字段、写值、删除/恢复 | uns | [UNS](references/cli/uns/guide.md) |
| Node-RED Flow 列表、节点、画布导出、创建、修改、部署、删除 | flow | [Flow](references/cli/flow/guide.md) |
| MQTT 凭证、发布与有界订阅 | mqtt | [MQTT](references/cli/mqtt/guide.md) |
| 文件上传、下载、访问地址、删除 | assets | [文件](references/cli/files/guide.md) |
| 项目/平台成员查询 | 仅在目标部署确认支持后使用相应 api | [能力边界](references/capabilities.md) |

不要凭 CLI 源码存在或登录成功，声称所有部署和所有角色都能使用全部能力。`flow deploy` 是 Node-RED 画布部署，不是 App 发布。

## 调用与结果

- 从现有命令与参考选择操作，先看目标命令 `--help`，不猜命令或 flags。优先专用命令；`api` 只用于已有且目标部署支持的接口。
- 写入前对支持的命令使用 `--dry-run --json` 核对目标、请求和影响。预览不是执行成功。明确的用户写入指令即相应授权；高风险变更先展示具体影响，缺少相应授权时再确认。
- Flow 部署前先导出画布备份并保留 Tier0 mqtt-broker 配置节点。不要把副作用不明的用户自定义 HTTP endpoint 当只读查询。
- 退出码 10 / confirmation_required 不能静默绕过。仅在用户已确认对应目标与影响后使用 `--yes`。
- Tier0 普通 OpenAPI 响应通常为 `code: 200` 或 `0`，dry-run/helper 为 `ok`，login 起始为 `status`，完成为 `event`；不要套用飞书的单一输出判断。读取 stdout 与 stderr，检查业务 code、批次 success 与逐项 results。见 [CLI 输出和边界](references/capabilities.md)。
- 凭证生成必须经过 helper：登录完成和 MQTT create 的原始 JSON 包含密钥。不要直接运行这些原始 JSON 命令，不开 `--debug`，不读取或展示配置文件全文；参考中的手动操作示例不覆盖这一要求。
- MQTT create 用 helper 的 `mqtt-create --name ... --save ...`，输出仅包含远端凭证 ID 与本地 profile。其他 MQTT 操作用 profile，订阅设 count/timeout；长时间监控需要独立运行机制，不留下无界后台订阅。
- 写操作失败或超时先回读，不盲目重复创建、发布或删除。完成后报告真实结果和资源标识；私密文件地址只在用户请求时返回。

## 明确不支持

本版不生成应用、不下载 Scaffold、不上传 App 源码、不创建 App 版本、不构建或发布 App。收到这些请求时说明当前范围，保留用户目标供后续能力升级，不自动退回通用代码生成，也不借 `api` 绕过此范围。

本插件不注册 MCP 服务，也不自创 OAuth 或 API Key 权限。平台操作始终受用户实际 Workspace、权限、套餐和目标部署支持限制。
