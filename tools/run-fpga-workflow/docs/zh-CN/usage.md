# 使用

[中文导航](README.md) · [架构](architecture.md) · [角色](roles.md) · [证据与安全](safety-and-evidence.md)

## 模式

| 模式 | 适用范围 |
|---|---|
| `ANALYZE` | 只读诊断、架构、报告和代码审核 |
| `QUICK` | 明确授权、单时钟、接口和 latency 不变的小改 |
| `FULL` | 新模块、CDC、IP、约束、接口、P&R、release 或高风险任务 |

风险不会自动扩大权限。

## Profile 和 claim stage

| Profile | 用途 |
|---|---|
| `DIAGNOSTIC_SMOKE` | preflight、compile、elaboration、有限运行 |
| `FUNCTIONAL_ACCEPTANCE` | 使用仿真接受 DUT 功能 |
| `SPECIALIST_ACCEPTANCE` | formal、CDC/STA、电气或 release |

claim stage 用于限制当前声明：

```text
PREFLIGHT COMPILE SIM_SMOKE FUNCTIONAL_SIM SYNTHESIS
IMPLEMENTATION_QOR TIMING_CLOSURE FORMAL RELEASE BOARD_PREP
```

## 工程身份卡

```text
工程根：
正式工程入口：
厂商和工具版本：
完整 part：
产品 top / 仿真 top：
正式脚本入口：
长期保护项：
```

身份卡不是长期写入授权。后续问题通过 task delta 更新。

## 示例：构建脚本诊断

```text
使用 $run-fpga-workflow，claim_stage=COMPILE。只诊断正式
project/script/run.bat 的路径、工具、IP、compile 和退出码。
不要修改产品 RTL，不要跑 P&R、功耗或 release。
```

## 示例：官方 IP

```text
使用 FULL / IP_INTEGRATION。确认本机厂商工具版本、part、现有 managed IP
和端口/latency/reset 契约。按复用、增量生成、staging/import、官方 Tcl/CLI、
GUI一次性兜底的顺序选择。不要从网上复制 IP 配置。只生成本任务需要的
IP proof 深度。
```

## 示例：实现 QoR

```text
使用 claim_stage=IMPLEMENTATION_QOR。冻结工具、part、源码、约束、seed 和
strategy。分类最高影响路径或拥塞根因，一次修改一个变量，重跑并比较
WNS/TNS/hold/route status/congestion/resources/runtime；改善则保留，否则回滚。
```

## 示例：功能仿真

```text
使用 FUNCTIONAL_ACCEPTANCE / FUNCTIONAL_SIM。按真实 accepted edge 建立
cycle-indexed scoreboard，检查 latency、early/late/drop/duplicate/reorder、
data 和 sideband；scoreboard 排空并使用能触发 checker 的负向 canary。
验证资产作者不能自签。
```
