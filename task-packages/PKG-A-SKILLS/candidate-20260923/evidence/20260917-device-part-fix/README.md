# SKL-002 HWH device PART 增量修复证据

日期：2026-09-17  
状态：作者增量自检完成，等待独立复核；不是 B 批准。  
硬件状态：`BLOCKED / NOT_RUN`；未导入 PYNQ、未下载 Overlay、未分配 DMA 缓冲区、未上板。

## 修复范围

只修改以下三个候选文件：

1. `exports/pynq-overlay-dma-validation/scripts/validate_receive_profile.py`
2. `exports/pynq-overlay-dma-validation/tests/test_receive_profile.py`
3. `exports/pynq-overlay-dma-validation/scripts/replay_receive_cases.py`

校验器现在只读取 HWH 根节点的权威 `PART` 属性。HWH `PART` 与
`board.device_part` 分别执行 `strip()` 和 `casefold()`，随后进行完整值相等比较。
不再扫描 MODULE、PARAMETER 或其他 XML 属性，也不再使用子串匹配。

原候选 `MANIFEST.sha256.json` 未修改，SHA-256 仍为
`9f43655abad38798c51671ec394071771c7857dcd34572346c27cca576fe5c1e`。
`original-manifest-integrity.json` 证明原 474 项中 471 项字节不变、只有上述三个
允许文件变化、没有缺失项或意外变化。原作者证据目录未覆盖。

## 独立反例前后结果

独立反例来源：

`C:/Users/Toph Beifong/.codex/visualizations/2026/09/07/01a07c21-b7f9-74d2-92c5-7f8d235d8379/skill-candidate-review-20260917-01/review-device-part-counterexample.py`

- 修复前：HWH 根 `PART=xc7z010clg400-2`，无关 MODULE 的 `COMMENT` 含
  `xc7z020clg400-2`，校验器错误 `PASS`。冻结报告：
  `counterexample/pre-fix/fixture/result.json`，SHA-256
  `96b2b52b02abb4b4586c42c75ceb70a99094dab1b04bc7702d141fa5da618bb0`。
- 修复后：同一份输入退出码为 1，状态 `FAIL`，唯一 issue code 为
  `HWH_DEVICE_PART`。报告：`counterexample/post-fix-run02/result.json`，SHA-256
  `d816ce9d38a9ea6c60bcd364e1db25e8db63476d0ff0d52e8ce19228a08ebdd7`。
- `counterexample/post-fix/` 保留了第一次复跑时 PowerShell `Start-Process`
  未正确引用含空格路径导致的启动失败；该次没有生成产品报告，未被计为测试通过。

## 新增边界测试

`test_receive_profile.py` 新增四个测试方法，覆盖五种输入：

1. HWH 与 profile 的器件值仅大小写和首尾空白不同：通过。
2. 错误根 PART 加无关属性诱饵：拒绝，`HWH_DEVICE_PART`。
3. 根 PART 缺失加无关属性诱饵：拒绝，`HWH_DEVICE_PART`。
4. 声明值的子串：拒绝，`HWH_DEVICE_PART`。
5. 声明值的超串：拒绝，`HWH_DEVICE_PART`。

receive profile 重放新增 `device-part-mismatch`，其错误 HWH 同时包含无关属性诱饵；
实际状态为 `FAIL`，实际 issue code 仅为 `HWH_DEVICE_PART`。

## 本轮实际执行

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| SKL-002 全部离线单元测试 | PASS；69 methods、76 subtests、0 failure/error/skip | `skl002-offline-tests-run02.json` 与 console log |
| receive 正例 | PASS | `receive-profile-pass.json` |
| receive 正负例重放 | PASS；9 cases = 1 正例 + 8 预期负例 | `receive-replay/summary.json` |
| 生命周期正常接收 | 预期 PASS | `lifecycle-normal.json` |
| 缓存陈旧 | 预期 FAIL；golden mismatch | `lifecycle-stale-cache.json` |
| 短输出 | 预期 FAIL；actual 95 / requested 96 | `lifecycle-short-output.json` |
| 超时且 abort 超时 | 预期 FAIL；buffer retained | `lifecycle-timeout-retained.json` |
| board guard | 预期退出 1；请求输出不存在 | `board-guard.console.log` |
| 临时安装结构 | PASS；只在临时副本映射 `skill.md -> SKILL.md` | `install-structure-run02.json` |
| SKL-001 逐文件哈希 | PASS；265/265 相同，未运行 XSim | `skl001-unchanged.json` |

最终有效的完整离线测试报告是 `run02`；前一份报告保留但发生在最后一次测试增强前，
不用于当前源码绑定结论。

## 复现命令

以下命令从 `exports/pynq-overlay-dma-validation/` 运行，并为输出选择新路径：

```text
C:/Python314/python.exe -B scripts/run_offline_tests.py --output <new>/skl002-offline-tests.json
C:/Python314/python.exe -B scripts/validate_receive_profile.py --profile references/example-receive/receive-profile.json --output <new>/receive-profile-pass.json
C:/Python314/python.exe -B scripts/replay_receive_cases.py --profile references/example-receive/receive-profile.json --output <new>/receive-replay
C:/Python314/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --output <new>/lifecycle-normal.json
C:/Python314/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --fault rx-invalidate-noop --output <new>/lifecycle-stale-cache.json
C:/Python314/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --fault short-output --output <new>/lifecycle-short-output.json
C:/Python314/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --fault timeout --fault abort-timeout --output <new>/lifecycle-timeout-retained.json
C:/Python314/python.exe -B scripts/pynq_probe.py --profile references/example-receive/receive-profile.json --download --output <new>/forbidden-board-output.json
```

最后四个故障/保护命令按合同应非零退出；board guard 还必须不创建请求的输出文件。
安装结构检查在临时副本把 `skill.md` 恢复为 `SKILL.md` 后调用
`skill-creator/scripts/quick_validate.py`，不改变候选导出。

## 交付与边界

- 新最终清单：`MANIFEST.device-part-fix.sha256.json`；它在本说明和全部证据完成后生成，
  与原 `MANIFEST.sha256.json` 并存。
- SKL-001 源码及历史证据只做原清单逐文件哈希核对，没有重复运行 XSim。
- `pynq_probe.py` 仍 fail-closed；离线报告中的 PYNQ driver、Overlay download、
  physical DMA、TLAST waveform、hardware performance、Vivado resources 均为 `NOT_RUN`。
- 本修复没有修改实际 RTL、Vivado/Vitis 工程、算法、板端配置或历史批准证据。
- 未提交、未推送、未合入；本目录是交给“拓芙工作执行”的增量复核入口。
