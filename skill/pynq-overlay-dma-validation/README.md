# PYNQ Overlay 与 DMA 通用验收 Skill

## 结论

本 Skill 把 PYNQ 工程验收拆成“离线合同检查”和“真实上板检查”两条证据链，所有板卡、寄存器、DMA 长度和数据格式都由外部 profile 提供，因此能从 SoundSight 迁移到其他 Overlay、其他算法和其他受支持 PYNQ 板。

它对应 2026 AMD FPGA 自主选题赛道中单独加分的通用 PYNQ Skill 场景：Overlay 加载与校验、寄存器映射、DMA 与缓存一致性、常见故障定位、黄金参考比对，以及性能和资源证据生成。它不替代作品必须提交的 RTL/仿真、Vivado 时序、板上实测和复现材料。

## 适用场景

- PYNQ Overlay 发布前核对 `.bit`、`.hwh`、构建清单和接口版本。
- 检查 AXI4-Lite 地址、访问权限、身份寄存器和原子配置合同。
- 验收 AXI DMA MM2S/S2MM loopback、自定义流核或采集路径。
- 排查缓存未 flush/invalidate、长度或对齐错误、TLAST 缺失、DMA 超时和错误状态。
- 用同一 profile 生成 golden-reference、吞吐、延迟、时序和资源的可追溯证据。
- 将 PYNQ 控制层替换为 Vitis/PetaLinux 时，复用同一硬件接口与验收口径。

不适合用它证明算法本身正确、CDC 正确、时序收敛或物理传感器连续采集；这些需要各自独立的模型、RTL、Vivado 和实板证据。

## 文件

```text
pynq-overlay-dma-validation/
├── SKILL.md
├── README.md
├── scripts/
│   ├── validate_profile.py
│   ├── pynq_probe.py
│   └── compare_golden.py
├── references/
│   ├── profile-contract.md
│   ├── hardware-runbook.md
│   └── example-profile.json
└── tests/
    └── test_validate_profile.py
```

## 快速使用

先复制并修改示例 profile。示例值只是结构说明，不能直接当作板卡合同：

```bash
cp references/example-profile.json validation-profile.json
python scripts/validate_profile.py \
  --profile validation-profile.json \
  --mode offline \
  --output results/offline-validation.json
```

在已确认支持的 PYNQ 板上安装 `numpy` 和 `pynq` 后运行：

```bash
python scripts/pynq_probe.py \
  --profile validation-profile.json \
  --download \
  --supplemental-evidence results/vivado-evidence.json \
  --output results/hardware-evidence.json

python scripts/validate_profile.py \
  --profile validation-profile.json \
  --evidence results/hardware-evidence.json \
  --mode hardware \
  --output results/hardware-validation.json
```

对经过自定义计算核的输出另做黄金参考比对：

```bash
python scripts/compare_golden.py \
  --expected data/golden.bin \
  --actual results/capture.bin \
  --format bytes \
  --output results/golden-comparison.json
```

浮点或量化后允许误差的数据可改用 `--format json-numbers --atol <绝对容差> --rtol <相对容差>`；容差必须来自项目数据合同，不能为通过测试临时放宽。

`pynq_probe.py` 默认只读取身份寄存器并执行 profile 明确列出的有界 loopback，不会猜测寄存器地址、写控制寄存器或自动复位整个 PL。运行前必须阅读 [上板清单与故障映射](references/hardware-runbook.md)。

## 失败条件

以下任一项出现时，报告必须为 `FAIL`，不能降级为“基本通过”：

- `.bit/.hwh/manifest` 缺失、哈希不一致，或 device/build/interface/Vivado 信息冲突；
- HWH 不含 profile 要求的 AXI-Lite/DMA IP，寄存器偏移重复、越界或未对齐；
- DMA 长度不满足 stream beat、buffer alignment 或最大长度约束；
- flush/invalidate 责任不明确，或上板证据没有记录实际执行的缓存操作；
- 身份寄存器不匹配、TLAST 缺失、超时、DMA error、输出长度错误或 golden mismatch；
- 性能低于门槛、时序 WNS 为负、资源超过 profile 上限，或证据源报告不可追溯；
- mock/static 结果被标成 `hardware`，或没有真实 board observation/Overlay download 记录。

## 已验证效果

当前 v0 已完成离线验证：

- 使用临时生成的 mock `.bit/.hwh/manifest` 和合成 loopback 证据，通过合法 profile；
- 对 manifest 哈希篡改、DMA 长度未按 stream beat 对齐、以及把 mock 证据冒充 hardware 三类错误均能确定性拒绝；
- 全部脚本只使用 profile 输入的板型、器件、IP、寄存器、长度和数据格式；未写入 SoundSight 专用地址或 payload 规则。

这些结果只证明静态门禁和合成数据逻辑有效，不是任何开发板的上板通过证明。

## 当前边界

SoundSight 当前只有以下候选证据：ATK-DF7010P_7020P 系列、底板 V3.9、Zynq XC7Z020 器件族，工程工具为 Vivado 2025.2。完整器件料号/速度等级、可复现的板级 PYNQ 镜像、Overlay、DDR/DMA 路径和最大安全块长仍待 M0 实物核实，因此目前只能交付“可离线验证的 v0 + 上板验收清单”。

PYNQ 是 SoundSight 首选控制层；PL 实时声学核心不得依赖 Python。若该板无法满足 PYNQ 准入条件，应切换为 Vitis 或 PetaLinux 控制层，同时保持 AXI4-Lite、AXI DMA、中断合同和本 Skill 的证据格式不变。

## 比赛报告写法

报告中应分别给出：

1. 从哪些真实失败或工程观察提炼出 profile 字段和停止条件；
2. 一张 Overlay 构建身份表和一张 AXI/DMA 合同表；
3. 离线测试、上板 loopback、golden 比对、吞吐/延迟、时序/资源的独立结果与证据路径；
4. 在另一题目或另一受支持板卡上只替换 profile、无需修改脚本的复用演示；
5. 未验证边界，特别是不得把 mock、HWH 静态解析或 Notebook 显示称为“板上通过”。

加分说明可概括为：该 Skill 将板卡和算法特定信息外置为版本化合同，提供 fail-closed 的 Overlay/DMA 验收与证据分级；陌生队伍只需填写自己的 profile 和黄金向量，就能复用同一离线门禁、PYNQ loopback 与报告格式。
