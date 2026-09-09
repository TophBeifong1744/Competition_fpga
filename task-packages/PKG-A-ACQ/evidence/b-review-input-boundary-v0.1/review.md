# B 复核：输入标度与 PL/PS 分工

日期：2026-09-09。执行者：B 侧 Codex，按 B 本轮明确授权复核及合入。
结论：通过，仅批准接口说明、源快照及软件复核证据入库。

- A 审核提交：`d262f275ed6817b07f732d5c85f675fd4ebeccdc`。
- 对比 main 基线：`e3f49050cb695beaa8e2ea869ae365a8135a6750`。
- 复核范围：两提交间 10 个文件；未改默认 PHAT、跟踪器或实际硬件工程。

## Standards

独立规范复核未发现阻断或需修改项。任务包隔离、来源与 SHA-256 绑定、字节保护、管理文档的交付指针符合交付约束；未扩大硬件批准范围。

## Spec

独立需求复核未发现阻断或需修改项。signed16 三拍测试流、H1 signed24/int32 交换及六麦浮点输入明确区分。PL 实时数据面与 PS 控制面、尚未验证的真实抽取增益均有明确边界。

## 执行与结果

在仓库根目录使用带 NumPy 的 Python，顺序执行：

```text
python -B task-packages/PKG-A-ACQ/evidence/input-boundary-v0.1/check_input_boundary.py
python -B task-packages/PKG-A-ACQ/payload/scripts/check_h1_fixtures.py
python -B task-packages/PKG-A-ACQ/evidence/b-review-input-boundary-v0.1/independent_check.py
git diff --check e3f49050cb695beaa8e2ea869ae365a8135a6750...HEAD
```

均通过。对应 selfcheck.txt、h1-fixtures.txt、independent-result.txt。运行环境见 environment.json。
第一项验证 7 个固定文件哈希及 8 个标度码值；第二项检查 6 行码型和 2 行重启样例，15 项是计划，不能表述为已执行 15 项读取器测试。
独立检查解析 BD 配置，验证 signed16 符号解释及 /2^23 换算，并调用六麦适配器确认大于 1 的浮点幅值及编号保留。

## 批准边界与交付映射

H1 是 signed24 码值存入 int32，浮点为 pcm/2^23；不能据此推断声学有效位数。16 位测试码型候选桥接保留整数，不隐含左移 8 位。六麦浮点不承诺硬件满量程。
PL 目标包括抽取、FFT/PHAT、几何求解、质量和跟踪状态、连续音频；PS 负责配置、DMA 管理、日志及导出。这是目标分工，不是已实现模块清单。
100 MHz 仅为现有 BD 配置，真实抽取结构、增益、移位、舍入饱和、FFT IP 与周期、采样时序仍待验证。没有运行 RTL 仿真或实板检查，不批准 H2/H3、完整 PKG-B-ALG 验收、默认算法替换或四麦主线性能。

按 A 指定目标路径发布 docs/input-scale-and-pl-ps-boundary.md，正文使用已审核 payload，追加前置复核状态说明。原 payload、A 原始证据及失败记录保持不变；原 README 的“未提交/推送”是作者当时状态，本记录取代其当前状态含义。
本轮固定文件 SHA 匹配只覆盖上述 7 文件，不扩展为历史研究输出 JSON 字节一致或硬件输入复现。历史输入哈希一致、算法数值复现通过、生成 JSON 字节不同仍须分别表述。

规范轴 0 项；需求轴 0 项；均无阻断。
