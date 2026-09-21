# 已有 CLI 能力与输出

本版复用 Tier0-cli commit `cb4190247e956fd797f80dcadacf3da8ed77016e`（npm 源码版本 0.7.0）和 Tier0-skill commit `b95c845a4437c9fd9f2c0f5caffa64ae7e224b7e`，2026-09-21 核对。它们是源码能力证据，不代表每个客户部署已经上线或已完成真实账号联调。

| 类别 | 命令 | 范围 |
| --- | --- | --- |
| 基础 | version、config、doctor、login、auth whoami | 当前实例、登录和诊断；没有 logout 命令 |
| UNS | browse、search、read、history、write、create、update、delete、restore | 按目标命令 help 与匹配参考执行 |
| Flow | list、get、nodes、data、create、update、delete、deploy | SourceFlow / EventFlow、Node-RED 画布；不含 App 部署 |
| MQTT | auth create/delete、publish、subscribe | 凭证及实时消息；创建凭证必须经安全 helper |
| 文件 | assets upload/download/url/delete | 上传默认 workspace 归属；不要推定有 assets list |
| 通用 API | api | 使用已知接口；不代表所有内部 API 都可对外使用 |
| 本地维护 | skills install/update/status/sync、upgrade、uninstall | 维护 CLI 及独立 Skills；不等于平台操作或认证 |

服务信息使用 `tier0 api /openapi/v1/info --body '{}' --json`。该版本没有独立 `tier0 info` 命令，README 里的旧示例不能直接照用。

成员查询是条件能力，参考 [项目成员](cli/launchpad/members.md) 与 [平台成员](cli/platform/members.md)。上游文档记录公共 SaaS 接口曾返回 404，这不是本次实时测试结论。默认不宣传为已可用；目标部署有明确支持证据后才使用，不因登录成功自动探测所有成员接口。

## 输出契约

- 普通 API 成功：常见 `{"code":200,"data":...}`（CLI 也接受 code 0）。HTTP 200 不足以证明业务成功。
- UNS 批次：另外检查 `data.success` 和每个 `data.results[i].success/error`。
- dry-run：`{"ok":true,"dry_run":true,"data":{"api":[...]}}`，或 MQTT publish 的 `data.mqtt`；不需要 Key，也不访问平台。
- 原生 login 起始：`status: authorization_required`；完成：`event: authorization_complete` 并含 api_key，所以必须通过 helper 丢弃凭证。
- helper：统一 `ok`，状态成功有 `status: authenticated` 和身份白名单；不输出原生 stderr 的 message/hint。
- 错误：原生 `--json` 错误在 stderr 的 `error.type/subtype/param`，不能只看 stdout。
- MQTT 订阅：NDJSON，持续输出多条消息；必须设置 `--count` 或 `--timeout`。

退出码：validation=2，authentication/authorization/config=3，network=4，internal=5，confirmation=10，API 错误通常为 1。相同退出码可包含不同错误类别。

## MQTT 凭证安全

原生 `mqtt auth create --json` 即使指定 --save 仍输出服务端返回的密码。插件统一使用：

```sh
python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" mqtt-create --name agent --save agent --dry-run
python3 "$TIER0_SKILL_DIR/scripts/tier0_auth.py" mqtt-create --name agent --save agent
```

必要时增加 --broker；helper 固定启用 random suffix，让 CLI 完成已有 profile 写入，只返回 ID、profile 与保存结果。预览必须对应用户授权的创建意图。失败后可能已经在远端创建凭证，不能盲目重复创建；在目标平台核对后处理。后续 publish/subscribe/delete 继续使用已有 CLI 与本地 profile，不读取密码文件。
