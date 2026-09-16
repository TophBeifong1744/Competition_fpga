# E1 待审发布说明（2026-09-16）

结论：工程实现的 E1 交付完整性检查与包外离线复跑通过，发布到独立待审分支，**不是 B 独立复核通过，不合入 main**。本轮没有操作板卡，也不要求拓芙重新 Run。

## 范围与最新状态

- 发布分支：`codex/toph/endurance-20260916`；父提交为直接远端 main `ad9ca72388fb676946c71b13517ab279c11cfc61`。交付提交 SHA 以发布回报和远端查询为准，不把父提交充当交付 SHA。
- 唯一新增范围：`task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/`。
- 工程实现原件 139 文件（原 SHA256 清单 138 项加清单自身）全部保留原字节。新增 publication 是工作执行的复现入口、结果与范围说明；`.gitattributes` 只用于禁止换行转换，不隐藏材料。旧准备、旧构建和失败清单均未更新。
- 本批包括调度/循环源码、CMake/检查器、测试、两次真实布局拒绝记录、真实构建产物、完整串口及现场确认，不是仅提交 PASS 日志。
- 原 `README.md`、`OPERATOR.md` 和构建报告是相应早期时点记录，其中“尚未实板”等不得当最新状态。本次作者实板状态看 `board-run-20260916-01/README.md`；发布/复核边界以本文件为准。没有改写原来的执行顺序或补造 B 放行记录。

## 计时入口复核仍有阻断，不能混称通过

已直接核对 B 反馈分支 `review/member-b-timerfixed-bbe39c3` 为 `d1fd9d1db2be7ed292c17faf9dc9d27d407c9009`。该提交 `docs/reviews/timerfixed-repair-17afe32/B-REVIEW.md` 结论是**需修改**：17afe32 修复版的 TF-B-01、TF-B-03 限定通过，TF-B-02-R1（复合 `-Wl,` 子参数被路径规范化吞掉）仍为 P2 阻断；17afe32 未合入 main。本次没有修复该问题或修改其分支。

更重要的是，E1 的 POLICY 固定的是更早的 `bbe39c38dc36ccb4c0492f492b86f6c46d885fbe` 中 `timerfixed-entry-01/check_entry.py` 与 `POLICY.json`，不是 17afe32。E1 自有 `timer_layout.py` 检查计时指令、重定位、调用目标、数值合同与内存区间，但**不继承 17afe32 的启动检查或封存加载保护**；E1 仍复用旧命令比较器。`--stage load` 是只读预检查，实际使用 GUI Run，并非受保护的封存下载。

因此，本批只申请 **E1 源码/构建/实板记录的限定复核和证据归档**，不申请把这些检查入口批准为安全构建/加载工具，不部署为活动入口，不以正常一次运行证明异常配置会被拒绝。B 若只批准实板证据，必须显式写明此限制；认为依赖影响本批归档结论时，先反馈，不合并。不整条合并计时入口分支，也不夹带未审入口进 main。

## 实际结果及本轮新检查

作者实板是一次初始加载后，由同一程序完成一段约 300 秒及十段约 10 秒；段间无操作者重新 Run/复位的声明有独立现场确认。初始加载本身仍有初始化和复位。

- 串口重算：19,202,750 组、76,811 包、614,488,000 字节在线处理，11 段全部完成；逐段 ID 跨度、包/字节数量、停止/排空、状态、44 组通道统计与报告一致，饱和标志合计 0。
- 这不是保存了上述字节的录音，也不是一段连续 400 秒；数据检查后回收，段间编号间隔保留。
- 本轮新复跑：原 138 项清单、46 项成功构建清单、23 项归档快照绑定；4 个日志测试方法（含 12 个变异）、7 个合同/源文件测试、12 个计时布局测试，合计 23 个 Python 测试方法。
- 新复跑主机 C 模型：原 16 场景、11 段调度与配置错误/失败复用/空配置/总期限断言通过；模拟外设与计时，不当作新的实板故障注入。
- 对实际归档对象/ELF 重新检查：ELF `75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449`；对象 `4eeb96edabcb79b2b6df29bbdbe2c67ee3532b14a71bfbe08117f4df63a3dc15`；除数 333333343；程序 end=0x00113890；E1 10 字段合同与 11 段实际调度表匹配。
- 新结果见 `run01/`，完整命令、返回码与输出保留。依赖来自准确 Git blob，复用 C1/current_build/硬件文件也逐字节核对；不是把存在文件当可用链路。
- 没有重新运行完整现场 pre/post/load、ARM 编译、RTL 仿真、综合/实现、下载或板测。138/46/23 等集合存在重叠，不累加声称独立文件总量。本轮未重新测量采样频率、增益/同步或声学质量。

## B 复现入口（不需要 A 的 F 盘工程）

先固定准确发布 SHA 到独立工作区。以下命令在该仓库根运行，`python` 替换为 B 自己的 Python 3.11+；输出使用**不存在的包外目录**。不要运行原脚本的 seal/record 或覆盖旧 evidence。

```powershell
$e1 = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01'
python -B "$e1/publication/package_manifest.py"
python -B "$e1/board-run-20260916-01/record_checks.py" verify
python -B "$e1/board-run-20260916-01/test_verify_log.py"
git -c core.longpaths=true fetch origin codex/toph/timerfixed-entry-20260916
python -B "$e1/publication/reproduce.py" --repo . --out F:/NUEC/review-evidence/e1-new-run01
```

如需复跑主机 C 模型，给最后一条追加 `--gcc <本机主机GCC绝对路径>`，或用不同的新输出目录再运行。未提供 GCC 时明确记为 NOT_RERUN，不影响其余归档检查。

复现器按 bbe39c38 固定 Git 对象提取最小历史依赖到新输出目录，不向工作区/实际应用安装旧入口，不要求整包放入 main，也不调用 Vitis。依赖对象不可取得就报错，不自动改用较新或本机检查器。提取后再与 E1 POLICY 的两个哈希及已批准 helper/硬件哈希核对；所有失败保留 result.json 和日志。

本轮比旧 C1 多了 300 秒/10 次短段调度、配置拒绝/全段超时/排空终态检查，以及受限的 now_us 常量池布局处理；不是只有串口文案改变。请 B 审查这些实际源码差异和证据层级。

## 允许范围与未完成项

申请归档位置仍为本任务包，不将 `proposed-src` 自动接入活动 ps/rtl，不修改实际 F 盘 one、continuous_platform、four_mic_endurance 或其引用入口。正式 M1/H3、一小时、全故障恢复、定位/波束/音频收益均未通过本批证明。计时入口 TF-B-02-R1 由 A 工程实现另行修复并交 B，不要求用户为它再采录。

本机共享 main 仍为 `57c50e6c99731cd57e7738ac91b02f985ad229b1`，检查时 origin/main 与直接远端 main 同为 ad9ca723，共享 main 落后 30 个提交；其他 Skill 等未提交内容保留。没有切换/重置脏共享目录，不代签 B 设备同步；本批尚未获批合入，因此不能称 main 批次收尾完成。原件留共享目录，发布副本在独立 endurance-publication 工作树；B 审核完成前均不删除，实际应用引用文件永不按临时副本清理。
