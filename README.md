# Tier0 Plugin

为 AI 助手提供 Tier0 平台连接与操作能力，通过自然语言使用已有平台功能。插件负责操作指导和鉴权引导，[Tier0 CLI](https://github.com/FREEZONEX/Tier0-cli) 负责执行平台请求。

## 使用

复制下面这句话到支持终端操作的 AI 助手中：

```text
请帮我安装 https://github.com/FREEZONEX/Tier0-plugin 中的 Tier0 插件，按照仓库说明选择当前工具支持的安装方式，检查并安装必要的 CLI 依赖，然后引导我完成 Tier0 登录授权。
```

安装与连接流程：

1. 获取本仓库中的 `plugins/tier0`，按所用 AI 工具支持的方式加载插件或其中的 `skills/platform` 技能。
2. 在对话中输入“连接 Tier0”。
3. 根据提示在浏览器登录 Tier0，选择工作区并授权。
4. 授权完成后，直接提出平台操作需求，例如“查看 UNS 目录”或“列出我的 Flow”。

插件会检查 CLI 和现有登录。缺少 CLI 时引导安装；已有有效授权会复用。安装插件不等于平台授权，也不会在安装时自动发起登录。

运行环境需要终端命令执行能力、Python 3 和 Tier0 CLI；npm 安装器需要 Node.js >=16。手动安装 CLI：

```sh
npx -y @tier0/cli@0.7.0 install
```

不同 AI 工具的插件格式和加载入口不同。本仓库提供通用的 Skill、CLI 操作参考与辅助脚本，并保留已有宿主适配配置；具体工具的安装兼容性需分别验证。

## 支持范围

| 能力 | 操作 |
| --- | --- |
| 连接与诊断 | 浏览器授权、用户/工作区/权限查询、服务信息 |
| UNS | 浏览、搜索、读写、历史数据、节点管理 |
| Flow | SourceFlow/EventFlow 管理、Node-RED 画布导出和部署 |
| MQTT | 凭证管理、消息发布、有界订阅 |
| 文件 | 上传、下载、访问地址、删除 |
| 成员查询 | 仅在目标部署已确认支持时使用 |

暂不支持应用生成、Scaffold 初始化、App 源码上传、建版或发布。Flow 部署指 Node-RED 画布部署，不是 App 发布。

登录和 MQTT 凭证创建通过包装脚本过滤原始输出；凭证仍由 CLI 保存到用户目录，不进入插件仓库。卸载插件不会撤销远端 Key。

## 仓库结构

```text
.agents/plugins/marketplace.json  # 已有宿主的插件市场适配
plugins/tier0/
  …                             # 宿主适配清单
  skills/platform/               # 操作入口、CLI 参考、鉴权辅助脚本
  tests/                         # 离线模拟测试
  SOURCES.json                   # 上游版本与来源记录
  THIRD_PARTY_LICENSE.txt        # 复用资料的 MIT 许可
```

业务参考复用 Tier0-skill，不要求用户再单独安装该仓库。平台请求由独立的 Tier0 CLI 执行，核心工作流不依赖特定模型。

## 验证与限制

```sh
python3 -m unittest discover -s plugins/tier0/tests -v
```

本版通过 16 项模拟鉴权测试、插件/技能格式校验和 CLI 0.7.0 的 5 项离线请求预览。尚未完成真实账号浏览器授权和平台业务联调；离线预览不是平台执行成功的证据。

更多说明见 [插件 README](plugins/tier0/README.md)，上游来源见 [SOURCES.json](plugins/tier0/SOURCES.json)。
