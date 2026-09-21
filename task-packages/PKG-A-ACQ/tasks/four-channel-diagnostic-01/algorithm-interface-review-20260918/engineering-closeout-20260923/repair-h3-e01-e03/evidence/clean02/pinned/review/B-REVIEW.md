# B 独立复核：H3 两项增量

实际复核日期：2026-09-21；9/23 是检查点名称。远端准确分支已 fetch 并核对；两份作者原件在 detached 工作树固定，未重封存或修改。两提交共同父提交为 1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78。

## 1. 软件逻辑增量：限定 PASS

审核 SHA：f879a54cf40359209895af955bcef92accdf79ea。
批准范围为 algorithm-interface-review-20260918/increment-20260923 的29文件，以及父目录 .gitattributes、PUBLICATION-INCREMENT-20260923.md；共31新增，无旧件修改。28项包清单不覆盖父目录两文件；另核对其 Git blob。12项历史依赖快照准确，完整包字节与审核提交一致。

Python 3.12.14 / NumPy 2.3.5，在独立仓库根执行：
`python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/increment-20260923/source/run_checks.py --out F:/NUEC/review-evidence/h3-two-review-20260921/logic-run01`

实际28 PASS、0 FAIL，退出0。包含8个合成分帧golden、262401个RNE整数、mask/epsilon及TTL谓词；历史run01/run02不累计。另执行 spec/framing_oracle.py：30个确定性随机序列、180000行、87完整帧；独立clean-run分段oracle逐值核对PCM、原ID、行界、interval、错误行全部通过。运行脚本原路径及环境保存在证据中；复制脚本保留原字节，异机需包外适配路径。

允许作为软件accepted-row、固定移位数学与提交谓词研究模型入库，入口继续保留任务包，不替换默认算法。available必须由调用方提供可信时钟映射；本谓词不是完整时间验证器。未批准生产ABI、RTL握手/CDC、有限硬件计数器、AMD整链逐码、实时或实板；预算仍REALTIME_BLOCKED。

## 2. 工程路线与条件预算：需修改，不合入

审核 SHA：0abdc91c57787b7c868a797b88f35129de169faf。
75新增仅工程目录，73项包清单及两份清单文件完整；21条Git来源绑定匹配。10条实际PS快照哈希可核对，但未访问A原机器，不证明实际加载。

执行：
`python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/source/seal.py --verify`
结果 PACKAGE_VERIFY_PASS 73。

`python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/source/run_checks.py --out F:/NUEC/review-evidence/h3-two-review-20260921/engineering-run01`
结果20 PASS、1 FAIL，退出1。未传 --inspect-ps，不照抄A的现场路径。

### Standards

完整性、范围、证据分层通过，独立详单见 standards/REPORT.md。补充复现缺陷 H3-E-03：run_checks.py:123 从工作区读取 f879 增量，但两个提交是兄弟关系；准确0abdc检出没有该目录，published_increment_preserved 报 FileNotFoundError。README 的直接命令不能完整通过。请从准确Git对象安全准备依赖或明确提供可执行组合检出流程，保留此次失败，不声称已有21/21独立复跑。

### Spec

- H3-E-01（阻断）：engineering_model.py:69-72 将COMMITTED改成REVOKED，:99-104 只看当前状态。commit→CLIP→新clean interval→旧帧晚错之后 failed=False，后续帧仍COMMITTED，违反ROUTE.md:25的追溯错误fail-stop。需分离历史提交事实与当前可用性，覆盖CLIP/STOP/RESET交错。
- H3-E-02（阻断）：:52-67 只绑定每帧，configA、configB可在同epoch/interval依次提交，违反ROUTE.md:23。可变bindings还被按引用保存，外部改写会改变所谓快照。需冻结session配置和每帧不可变绑定，变更配置必须新session。

独立脚本 spec/adversarial.py 与JSON保留具体参数及源哈希；脚本退出0仅表示成功记录反例，不表示被测行为通过。直接晚错无中间barrier的控制例正确fail-stop。

数值/预算部分实际复跑：1024 Hann系数、4096窗乘、4097互谱、2054归一化等检查通过；这不关闭上述状态合同错误。串行1633192周期大于1066666预算；477432周期的快速例依赖未验证假设。202816字节仅逻辑容量，无链接地址证明。两者仍REALTIME_BLOCKED。

## 复用、未测和发布边界

准确历史依赖未替换。B checkpoint R1/R2 的后续 fe67547 已批准，旧快照中的“待修”仅为历史，不重新要求关闭。既有八段、S1、FFT、耐久及计时入口复核未重跑。没有新ARM/AMD编译、XSim、综合、布局布线、现场PS检查、下载或上板。不批准完整H3/M1、音频收益、方向精度或长稳。

仅任务1原始31文件与本次包外B报告/证据进入main；任务2原件保留待修分支。未触及A实际one、共享未提交工作或第三项状态文档。规范轴新增复现问题1项；需求轴阻断2项。软件包限定通过，工程包需修改。
