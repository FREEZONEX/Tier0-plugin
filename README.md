# Tier0 Plugin

在 Codex 中连接 Tier0，通过自然语言操作已有平台能力。插件负责操作指导和鉴权引导，[Tier0 CLI](https://github.com/FREEZONEX/Tier0-cli) 负责执行平台请求。

## 安装

在已安装 Codex CLI 的终端执行：

```sh
codex plugin marketplace add FREEZONEX/Tier0-plugin
codex plugin add tier0@tier0
```

安装完成后新建 Codex 任务，输入：

> 连接 Tier0

插件先检查 CLI 和现有登录；未登录时提供 Tier0 浏览器授权链接。用户登录、选择工作区并授权后，插件核对身份与权限，再继续原任务。已有有效授权会复用。

首次使用需要 Python 3；缺少 Tier0 CLI 时会引导安装，npm 安装器需要 Node.js >=16。插件安装不等于平台授权，也不会在安装时自动发起登录。

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
.agents/plugins/marketplace.json  # Codex 插件市场入口
plugins/tier0/
  .codex-plugin/plugin.json      # 插件清单
  skills/platform/               # 操作入口、CLI 参考、鉴权辅助脚本
  tests/                         # 离线模拟测试
  SOURCES.json                   # 上游版本与来源记录
  THIRD_PARTY_LICENSE.txt        # 复用资料的 MIT 许可
```

当前发布包装面向 Codex；不宣称已完成其他宿主兼容验证。业务参考复用 Tier0-skill，不要求用户再单独安装该仓库。

## 验证与限制

```sh
python3 -m unittest discover -s plugins/tier0/tests -v
```

本版通过 16 项模拟鉴权测试、插件/技能格式校验和 CLI 0.7.0 的 5 项离线请求预览。尚未完成真实账号浏览器授权和平台业务联调；离线预览不是平台执行成功的证据。

更多说明见 [插件 README](plugins/tier0/README.md)，上游来源见 [SOURCES.json](plugins/tier0/SOURCES.json)。
