# Changelog

本文件记录 Orvibo LAN Control 的用户可见变化。v0.4.0 起代码基线采用 [orvibo-lan](https://github.com/maycode0-0/orvibo-lan) 的工程化重写架构。

## [Unreleased]

## [0.4.0] - 2026-08-02

### Added

- 采用新版分层架构：单 Reader TCP 会话与序列号路由、`GatewayManager` 网关管理、`StateStore` 状态仓库、`CloudClient` 云端客户端分层（继承 orvibo-lan 0.0.x 的工程改进）。
- 配置流升级至版本 3：唯一 ID 按账号与家庭隔离、支持 reauth 与旧条目自动迁移。
- 新增 `orvibo_lan.refresh_devices` 服务，手动刷新云端拓扑。
- 新增属性型只读实体（`door_status` / `battery_power`）与集中式设备能力判定。
- 补齐测试与 CI：ruff、mypy、pytest（覆盖率门槛 62%）、HACS 校验、hassfest、actionlint、发布契约校验。

### Changed

- 发布策略对齐新版：`orvibo_lan.zip` 固定发布资产，tag 与 `manifest.json` 版本严格一致。
- 云端请求默认启用 TLS 校验，错误按传输/HTTP/JSON/schema/API/认证分类。
- UDP 网关发现仅接受私有 IPv4，并要求 TCP 登录确认网关 UID 后才采用。

### Removed

- 删除 `clothes_horse_control` 服务（电动晾衣架为 WiFi 直连设备，不支持局域网控制）。

### Security

- 日志不再记录账号、密码、Token、会话密钥或完整控制 payload。
