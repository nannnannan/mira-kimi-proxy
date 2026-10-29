# Mira Kimi Proxy

Windows 本机 OpenAI Chat Completions 兼容代理，使用当前 Windows 用户已登录的 Mira 平台账号，默认模型 **K3.1 Pro**。

支持普通 JSON 与 SSE 转发，保留 `system`、`tools`、`tool_choice`、`tool_calls`、`reasoning_content` 和 `role=tool`。代理不执行工具、不自动注入提示词。

## 快速开始

1. 安装 Node.js 18+（已验证 Node 24），打开并登录 Mira。
2. 本版本已验证 Mira **0.0.697**；默认加载 `%LOCALAPPDATA%\Programs\@mirasimdesktop\resources\server-main.cjs`。如果该文件不存在，先按下文配置你的实际安装布局。
3. 在仓库根目录运行：

```powershell
& .\kimi-api\start.ps1
```

首次启动自动生成 `kimi-api/.local-api-key`。脚本会显示连接参数；不要提交或分享这个文件。

| 参数 | 值 |
| --- | --- |
| Base URL | `http://127.0.0.1:18890/v1` |
| 模型 | `kimi-k3.1-pro` |
| API Key | `kimi-api/.local-api-key` 的内容 |
| 请求超时 | 建议 180 秒以上 |

```powershell
# 停止本项目代理，不退出 Mira
& .\kimi-api\stop.ps1
```

也可在前台运行 `npm start`，用 Ctrl+C 停止。无需安装 npm 依赖。脚本启动和前台启动不要同时使用同一端口；前台方式不生成用于 stop.ps1 的 PID 文件。

## 模型映射

| 输入模型 | 上游模型 |
| --- | --- |
| 省略 model | `kimi-k3.1-pro` |
| `kimi-k3.1-pro`、`kimi-code/k3.1-pro`、`kimi-code/k3.1`、`k3.1`、`k3.1-pro` | `kimi-k3.1-pro` |
| `kimi-code/k3`、`kimi-k3`、`k3` | `kimi-k3`，保留旧 K3 |

`GET /v1/models` 返回本地别名列表，不代表实时配额检查。`GET /health` 返回代理运行信息，不自动调用云模型。所有接口均要求本地 API Key。

## Mira 版本与安装位置

`kimi-api/runtime-selection.json` 当前为 `{"version":null}`，读取原安装目录。设置版本号可显式选择 `%USERPROFILE%\.mirasim\app\<版本>` 下的更新包；环境变量 `MIRA_BUNDLE_VERSION` 可以覆盖文件配置。不要保留已被 Mira 清理的旧版本路径。

源码保留了 0.0.447、0.0.479、0.0.620、0.0.622、0.0.626、0.0.697 的已核验映射。当前发布测试对应 0.0.697。文件哈希未知时拒绝启动；不要通过删除哈希检查来适配新版本。更换配置后先停旧代理，再启动。

这是非官方、本机专用的版本适配程序，依赖已安装 Mira 的内部协议代码，不包含或分发 Mira 安装包。Mira 更新可能破坏兼容性。

## 工具材料与单文档

- [完整使用说明、代理源码与 25 工具协议](docs/完整使用与工具协议.md)
- [工具定义 JSON](kimi-protocol/tools.json)
- [系统提示模板](kimi-protocol/system-prompt.template.txt)
- [请求构造助手](kimi-protocol/adapter.py)
- [真实调用验证记录](docs/validation.json)
- [会话日志导出方法](docs/会话日志导出方法.md)

工具材料来自 Kimi Code 0.29.2 的隔离捕获，没有私有 skills、MCP 或项目指令。客户端必须实现自己的工具执行器；工具结果通过匹配的 `tool_call_id` 回传，保留模型的 `reasoning_content`。模板内的 OS、路径、日期和权限说明需要按真实环境调整，未实现的工具不要传给模型。

单文档中的 `YOUR_USER` 是脱敏占位符，直接使用仓库启动脚本时不需要修改脚本中的用户名。

## 验证与打包

```powershell
npm test
python -m unittest discover -s tests
python scripts/package.py
```

这些检查不访问账号或云模型。最后一步生成 `dist/mira-kimi-proxy-0.1.1.zip`，使用文件白名单并校验完整性。

代理启动后，可手动执行真实测试：

```powershell
python kimi-api/verify_k31.py
python kimi-api/validate_tools.py kimi-k3.1-pro kimi-code/k3.1-pro
```

真实测试会使用少量现有订阅额度。2026-10-29 在 Mira 0.0.697 上实测通过普通回复、完整 25 工具 SSE Read 调用及客户端结果回传。没有验证全部工具实现、高并发、长期续期、Linux 部署或不同地区的可用性。

## 凭据与访问范围

仅监听 `127.0.0.1`，本地客户端凭据与 Mira 登录凭据分开。程序在当前 Windows 用户环境中解锁该用户已有的 Mira 登录材料，只在进程内使用，不导出明文账号凭据。保持 Mira 正常登录，让桌面端维护续期。

服务端地区与额度限制继续生效。不要将端口直接开放公网；本项目没有为多用户公网服务设计。仓库和发行包不包含账号数据、本地 API Key、日志、Mira 安装包或运行备份。

本仓库未声明第三方程序或捕获提示的再许可授权。Mira、Kimi Code 及其工具材料的相关权利仍属于原权利人。
