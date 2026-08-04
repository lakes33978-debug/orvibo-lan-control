# Orvibo LAN Control

Orvibo LAN Control 是一个 Home Assistant 自定义集成。它通过 Orvibo 云端获取家庭、房间、设备和网关拓扑，并通过局域网内 MixPad 的 TCP 8088 接口控制 Zigbee 子设备。

> 本仓库基于 [orvibo-lan](https://github.com/maycode0-0/orvibo-lan)（对本项目的工程化重写）继续迭代：代码基线采用新版分层架构，实机验证记录、命令速查等知识资产保留自本项目的旧版积累。

> 本地控制仅适用于可通过 MixPad 网关访问的 Zigbee 子设备。WiFi、BLE、红外、摄像头和其他直连设备不在当前 LAN 控制范围内。

## 功能

- 通过 Home Assistant UI 配置 Orvibo 账号、家庭和设备。
- 支持多个家庭与多个 MixPad 网关，配置项按账号和家庭隔离。
- 通过 UDP 10000 发现已知网关的新局域网地址。
- 通过 TCP 8088 完成 Hello、Login、控制、心跳和状态接收。
- 使用单一 TCP 读取循环按序列号路由响应，避免控制回复与状态推送相互抢读。
- 接收 `cmd=42` 局域网状态推送，并用云端快照补充属性型只读设备。
- 将 App 房间映射到 Home Assistant 区域。
- 提供 `orvibo_lan.refresh_devices` 服务手动刷新设备拓扑。

## 运行要求

- Home Assistant 2024.1.0 或更高版本。
- Home Assistant 能访问 Orvibo 云端 HTTPS 接口。
- Home Assistant 与 MixPad 位于可互通的局域网，且 TCP 8088 可达。
- Orvibo 账号中至少存在一个可识别的家庭和 MixPad 网关。

集成首次加载依赖云端拓扑，当前不支持在从未成功获取拓扑的环境中完全离线启动。账号、密码、Token 和会话密钥均不应写入日志或诊断资料。

## 安装

### HACS

1. 在 HACS 中将当前项目仓库添加为“集成”类型的自定义仓库。
2. 搜索并安装 **Orvibo LAN Control**。
3. 重启 Home Assistant。
4. 进入“设置 -> 设备与服务 -> 添加集成”，搜索 **Orvibo LAN**。

发布资产固定为 `orvibo_lan.zip`，HACS 从 ZIP 根目录安装集成文件。

### 手动安装

将 `custom_components/orvibo_lan/` 复制到 Home Assistant 配置目录下的 `custom_components/orvibo_lan/`，然后重启 Home Assistant 并添加集成。

## 配置

| 参数 |   必填   | 说明                                           |
| ---- | :------: | ---------------------------------------------- |
| 账号 |    是    | Orvibo 账号，通常为手机号                      |
| 密码 |    是    | Orvibo 账号密码                                |
| 家庭 | 多家庭时 | 单家庭会自动选择，多家庭需要在配置流程中选择   |
| 设备 |    是    | 从当前家庭中选择需要接入 Home Assistant 的设备 |

配置完成后，集成会获取设备拓扑、解析所属网关、建立局域网连接，并按设备能力创建实体。配置选项发生变化后，配置项会重新加载以更新实体集合。

如果之后修改了智家365账号密码，可在该集成的 **配置** 菜单中选择 **重新登录**。新密码会经过云端登录和局域网网关登录验证；成功后只更新原配置项，不会删除家庭、已选设备、实体或区域设置。

## 支持范围

源码中的设备能力以 `custom_components/orvibo_lan/profiles.py` 和 `device_profiles.py` 为准。文档中的“支持”表示已有实体和协议实现，不等同于所有同类型型号都经过实机验证。

| Home Assistant 平台 | deviceType                                    | 能力                                         |
| ------------------- | --------------------------------------------- | -------------------------------------------- |
| `light`             | 0、1、38、102、501、502、503                  | 开关、亮度、色温，具体能力由类型和子类型决定 |
| `cover`             | 34、35                                        | 开、关、停止、位置                           |
| `climate`           | 36、81                                        | 电源、模式、目标温度、风速                   |
| `fan`               | 81、516                                       | 电源和档位/百分比映射；516 仍需更多实机样本  |
| `sensor`            | 22、23、25、26、27、46、54、56、107、300、522 | 温湿度、电量及设备暴露的数值属性             |
| `binary_sensor`     | 25、26、27、46、54、56                        | 告警、人体、烟雾、门磁、水浸、紧急状态       |
| 属性型只读实体      | 状态中包含 `battery_power` 或 `door_status`   | 电量或门状态                                 |

以下设备当前不提供本地控制：

- WiFi 直连电动晾衣架、智能遥控器和其他 WiFi 设备。
- 摄像头、门铃、BLE 门锁和红外设备。
- 不经过已识别 MixPad 网关的设备。
- 协议或能力尚未通过抓包确认的未知型号。

## 实机验证记录（保留自旧版实测）

> 以下记录来自旧版 orvibo-lan-control 的实机测试，仅代表当时实测的型号；代码迁移到新版架构后需按 [DEVICE_INTEGRATION_ANALYSIS.md](DEVICE_INTEGRATION_ANALYSIS.md) 的验证基线重新验收。

### ✅ 实测通过

| 类别 | 型号/系列 | 功能 |
|:----|:----------|:-----|
| 🔘 **开关** | MixSwitch 系列（Classic / Bach / Defy / Gauss） | 开/关 |
| ❄️ **空调** | AirMaster 系列空调网关 | 模式/温度/风速 |
| 🪟 **窗帘** | 精筑系列 / 超静音系列 窗帘电机 | 开/关/停/位置 |
| 💡 **筒射灯** | SoPro 系列（S3 / S5 / S10）智能筒射灯 | 开/关/亮度/色温 |
| 💡 **调光灯** | 二代智能调光灯 | 开/关/亮度 |
| 🌈 **灯带** | 智能灯带控制器 | 开/关/亮度/色温 |
| ❄️ **空调/新风** | AirMaster 系列控制器 | 开/关/模式/温度/风速 |

### 🔧 待测试

| 类别 | 型号/系列 | 功能 |
|:----|:----------|:-----|
| ⚡ **调光** | 0-10V 调光模块 | 待验证 |

### ❌ 不支持（WiFi 直连设备）

| 类别 | 原因 |
|:----|:-----|
| 电动晾衣架 | WiFi 直连，不走 MixPad 网关 |
| 智能遥控器 | WiFi 直连，不走 MixPad 网关 |
| 摄像头/门铃 | WiFi 直连 |
| 梦幻帘一代/二代 | 协议不支持 |
| 其他 WiFi 直连设备 | 协议不支持 |

## 命令速查（旧版抓包结论）

### 空调控制（type=36）

| 操作 | order | value1 | value2 | value3 | value4 |
|:----|:------|:------:|:------:|:------:|:------:|
| 关机 | `off` | 1 | 当前模式 | 当前风速 | 当前温度<<16 |
| 开机 | `on` | 0 | 模式码 | 风速码 | (温度×100)<<16 |
| 切换模式 | `mode setting` | 0 | 2除湿/3制冷/4制热/7送风 | - | 当前温度<<16 |
| 设温度 | `temperature setting` | 0 | 当前模式 | 当前风速 | (目标温度×100)<<16 |
| 设风速 | `wind setting` | 0 | 当前模式 | 1低/2中/3高 | 当前温度<<16 |

> 所有控制命令都保持 `groupId=""`、`qualityOfService=1`、`defaultResponse=1`、`propertyResponse=0`，与 App 行为一致。

**模式码对照：** `2=除湿` `3=制冷` `4=制热` `7=送风`

**温度编码：** `value4` 高16位 = 目标温度×100（如 26℃ → `0x0A28` = 2600）

### 灯控制

| 类型 | 开 | 关 | 调亮度 | 调色温 |
|:----|:---|:---|:------|:------|
| 38（调光调色灯） | `order=on` | `order=off` | `order=move to level` | `order=fast color temperature` |
| 102 / 通用 | `order=on, value1=0` | `order=off, value1=1` | `order=on, value2=亮度` | - |
| 501 | `set property onoff=on` | `set property onoff=off` | - | - |
| 502 | `set property onoff=on` | `set property onoff=off` | `set property brightness.percent` | - |
| 503 | `set property onoff=on` | `set property onoff=off` | `set property brightness.percent` | `set property colorTemp.value` |

### 窗帘控制（type=34）

- **开：** `order="open"`
- **关：** `order="close"`
- **停止：** `order="stop"`
- **设定位置：** 传 position=0~100，≥50 发 `"on"`，<50 发 `"off"`

## 工作原理

```text
Home Assistant
  |-- HTTPS --> Orvibo 云端
  |              |-- 家庭、房间、设备、状态和网关 IP
  |
  |-- UDP 10000 --> 已知 MixPad 地址发现
  |
  `-- TCP 8088 --> MixPad
                   |-- Hello / Login / Heartbeat
                   |-- cmd=15 控制
                   `-- cmd=42 状态推送 --> Home Assistant 实体
```

云端负责拓扑和属性型只读状态，局域网连接负责 Zigbee 子设备控制与实时状态。LAN 实体的可用性取决于所属网关连接；属性型只读实体的可用性取决于云端协调器。短暂云端故障不会直接使仍可通过 LAN 控制的设备离线。

## 协议摘要

- 包格式：42 字节头 + AES-ECB/PKCS7 加密的 JSON。
- 包头：`hd`、总长度、`pk`/`dk`、CRC32、32 字节 Session ID。
- 默认密钥：`khggd54865SNJHGF`，仅用于初始会话包。
- 会话密钥：Hello 成功后由网关返回，用于后续 `dk` 包。
- 心跳：`cmd=32`，默认 60 秒。
- 控制：`cmd=15`。
- 状态推送：`cmd=42`。

协议字段和设备命令详见 [DEVICE_PROTOCOL_REFERENCE.md](DEVICE_PROTOCOL_REFERENCE.md)。新增设备所需资料见 [DEVICE_EXTENSION_GUIDE.md](DEVICE_EXTENSION_GUIDE.md)。

## 开发

开发环境使用 Python 3.11 或更高版本：

```bash
python -m venv .venv
python -m pip install --upgrade "pip>=25.1,<26"
python -m pip install --group dev
ruff check custom_components tests
mypy custom_components/orvibo_lan
pytest --cov=custom_components.orvibo_lan --cov-report=term-missing
```

Windows PowerShell 激活虚拟环境时使用 `.venv\Scripts\Activate.ps1`。完整开发约束和发布流程分别见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [RELEASING.md](RELEASING.md)。

## 文档

- [架构说明](ARCHITECTURE.md)
- [设备接入分析](DEVICE_INTEGRATION_ANALYSIS.md)
- [设备扩展指南](DEVICE_EXTENSION_GUIDE.md)
- [协议参考](DEVICE_PROTOCOL_REFERENCE.md)
- [Model ID 资料池](MODEL_ID_POOL.md)
- [变更日志](CHANGELOG.md)
- [安全策略](SECURITY.md)

## 版本历史

### v0.4.0（未发布）

- 代码基线升级为 orvibo-lan 的工程化重写架构（单 Reader 请求路由、网关管理器、状态仓库、云端客户端分层）。
- 删除 `clothes_horse_control` 服务（电动晾衣架不支持局域网控制）。
- 发布流水线与契约校验对齐新版（`orvibo_lan.zip` 固定资产、tag 与 manifest 一致）。
- v0.3.1 ~ v0.3.7 期间的修复项（门锁/传感器/配置流/内存泄漏等）已并入本版基线。

### v0.3.0（2026-07-18）

- 局域网状态推送（cmd=42），实时光效不轮询
- 设备区域自动同步（从 App 房间配置映射到 HA 区域）
- 网关设备注册修复（via_device 兼容 HA 2025.12+）
- 所有日志降级为 debug，减少日志量

### v0.2.0（2026-07-17）

- 修复空调开机（改用 `order="on"`）
- 修复空调风速控制（补全 `value2` 当前模式、`value4` 当前温度）
- 修复温度设定（补全 `value2` 当前模式、`value3` 当前风速）
- 保留 `groupId` 字段（不再被 `_to_lan` 删除）
- 对齐智家365 App 抓包格式

### v0.1.0（2026-07-17）

- 初始版本
- 基础设备控制：灯、窗帘、风扇
- 空调基础控制（`order="off"` / `"mode setting"` / `"temperature setting"` / `"wind setting"`）
- UDP 自动发现多网关
- 心跳保活

## 致谢

- [orvibohomebridge](https://github.com/yinjimmy/orvibohomebridge) — 在线控制版实现参考
- [orvibo-lan](https://github.com/maycode0-0/orvibo-lan) — 工程化重写与架构参考

## License

MIT
