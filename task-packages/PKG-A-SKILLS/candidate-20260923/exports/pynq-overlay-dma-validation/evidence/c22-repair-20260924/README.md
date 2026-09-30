# C22-01 / C22-02 限定返修证据

Issue #22、PR #32，原候选 `d57875f3c561bfde06fb3a23a2f110744245276b`。本次仅检查导出的 S2MM-only 静态验证器。`inputs.json` 固定合成 fixture 身份；`baseline-summary.json` 与 `repaired-summary.json` 分别记录修前、修后**同一组**真实 CLI 调用的输入哈希、退出码、报告哈希及问题码。逐例原始 stdout/stderr/report 留在执行机全新 `codex_out/c22-repair-20260924-184254/`，不以该 ignored 目录作为团队唯一证据。

## 独立预期与首错

- C22-01：`timeout_seconds` 只能是有限正整数或有限正浮点数。原始 JSON 数字 `1e999` 在 Python 3.12 的 `json.load` 后成为正无穷，必须由 `RECEIVE_TEST_TIMEOUT` 拒绝；`0.25` 和原示例 `2.0` 必须保留通过。
- C22-02：控制与 DMA 的**规范化 HWH 完整路径**必须不同。完全同名或仅前导 `/` 不同，须由 `HWH_CONTROL_DMA_DISTINCT` 拒绝；`system_i/axi_gpio_run` 及其前导 `/` 别名与 DMA 是独立实例，必须保留通过。
- 修前上述三个无效输入均 exit 0/PASS，且 bit/HWH/manifest/payload 文件与哈希均有效；没有用缺文件或哈希失败抵扣目标检查。

## 修复与结果

仅修改 `scripts/validate_receive_profile.py` 的这两项判定，新增 `tests/test_receive_profile.py` 的针对性负例；不修改 HWH 解析、no-DRE、长度、manifest、payload 或已批准的活动 Skill。Python 3.12.14；在 PR 工作树根执行：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest discover -s task-packages/PKG-A-SKILLS/candidate-20260923/exports/pynq-overlay-dma-validation/tests -p test_receive_profile.py -v
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B task-packages/PKG-A-SKILLS/candidate-20260923/exports/pynq-overlay-dma-validation/scripts/replay_receive_cases.py --profile task-packages/PKG-A-SKILLS/candidate-20260923/exports/pynq-overlay-dma-validation/references/example-receive/receive-profile.json --output codex_out/c22-repair-20260924-184254/receive-replay
```

前者 exit 0，20 tests OK；后者 exit 0，9/9 cases 符合预期，`board_execution=false`。修后目标 CLI：`1e999` → exit 1 / `RECEIVE_TEST_TIMEOUT`；同实例及前导 `/` 别名 → exit 1 / `HWH_CONTROL_DMA_DISTINCT`；三项合法输入仍 exit 0/PASS。CLI 形式是 `scripts/validate_receive_profile.py --profile <独立合成profile> --output <全新report>`；具体六个输入和报告的 SHA-256、退出码见两个 summary。

本轮原作者 69 methods / 76 subtests 和先前 9-case 原证据按身份**复用，未重跑全套**；本轮仅运行上列受影响检查。C22-01、C22-02 为 `FIXED_PENDING_REVIEW`，待 C 按新准确提交独立复核后才能 `VERIFIED_CLOSED`。所有 PASS 仅为离线静态候选；PYNQ、真实 DMA、TLAST、缓存、Vivado/Vitis 与板测均 `NOT_RUN`，既有板端准入阻断继续有效。
