# A 独立复核：C 板四路离线算法增量

2026-09-13。结论：**通过限定复核**，没有阻断项。仅批准四路真实录音离线诊断与 reference25 参考模型增量入库，不批准完整 H3、默认算法替换、配置冻结、声学精度/收益、RTL 或实板资源时序。

## 身份与范围

- 实际远端待审 SHA：`e5b675301faef12bf13cd9f5d827f7db9ca6fd13`，分支 `task/member-b-0914-algorithm`。
- 基线：`a402375df223214340b3638a3c7202135dfb0a8b`。
- 比较基线至待审提交仅新增 `task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/` 下26文件，无其他修改。复用的6份源码亦通过manifest哈希检查。
- 独立 detached worktree：`E:/ss-cboard-alg-review-0913`；新输出 `E:/ss-cboard-alg-review-0913-a-run01`。未操作B工作树，未覆盖作者run01/run02或manifest。
- 保留该任务包作为诊断入口；未接入活动生产算法。之后获得整链批准再迁移。没有重新批准A FFT29或C格式接收，也不向C派任务。

## 实际命令及环境

Windows 11 build26200，CPython3.12.14，NumPy2.3.5。FFT DLL SHA256：`79ec8ccc56cd56c4277a3c8c46ed0fca8435f6e62107854414b1672eda5575ca`，由run.py运行前验证。依赖加载目录 `F:/AMD/2025.2/win64/tools/fpo_v7_1`；不分发AMD DLL。

在独立副本根目录执行，下列均成功：

```powershell
$py='C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg='task-packages/PKG-B-ALG/tasks/c-board-algorithm-01'
& $py -B -m unittest discover -s $pkg -p test_run.py -v
& $py -B "$pkg/verify_manifest.py"
& $py -B "$pkg/run.py" --out E:/ss-cboard-alg-review-0913-a-run01 --dll F:/AMD/2025.2/win64/tools/fft_v9_1/libIp_xfft_v9_1_bitacc_cmodel.dll --dependencies F:/AMD/2025.2/win64/tools/fpo_v7_1
& $py -B "$pkg/compare.py" --candidate E:/ss-cboard-alg-review-0913-a-run01 --out E:/ss-cboard-alg-review-0913-a-run01/comparison.json
```

另执行随本记录保存的 `audit_cboard.py <repository-root> <fresh-run-directory>`，检查双符号边缘峰插值后的接受/拒绝、完整fixed调度的零输入/前向溢出不执行IFFT、122帧编号与732对连续合法界以及逐对分歧。结果PASS。

## 逐项结果

| 项目 | 独立结果 |
|---|---|
| 原测试/交付身份 | 10/10测试；31项文件与依赖SHA256通过；输入5项运行前后哈希检查通过 |
| 调度/覆盖 | quiet与speech各61帧，各覆盖31744个不同样本、尾部256未用；不跨clean_interval拼接。488次前向、726次逆向，无报告溢出 |
| 符号 | `X_i conj(X_j)` 的正lag表示i晚到；`(p_j-p_i)·u Fs/c`与向声源方向一致；交换通道反号测试通过 |
| 几何/声源 | 沿用操作者40mm正方形/共面声明；约10cm、−45°以mic1为参考。不能当阵列中心远场精确真值 |
| 峰/边界 | 搜索边±6、对角±8，Q12/浮点插值后检查连续界加旧0.05样点容差；该容差不是几何精度 |
| 拒绝传播 | 零输入/不足12点拒绝；任意前向溢出全帧拒绝，任意IFFT溢出全帧拒绝；少于3对或秩不足不投影 |
| quiet | 双有效366对，整数峰变化23，最大差0.5304042925151208样点；一致性35/33帧不代表有目标 |
| speech | 各链344有效，但双有效343；有效性分歧2；双有效整数峰变化3，最大差0.2570502476726051样点 |
| 数据与数值 | 整数阶段/掩码/离散结果严格一致；两NPZ连同浮点相关数组字节一致；两frames JSON投影浮点出现末位差，最大2.842170943040401e-14，满足1e-10预设容差；summary含环境/耗时而字节不同 |

speech分歧均为mic1–mic3（帧号从0计）：

| 帧/起始行 | 浮点时延与判定 | reference25时延与判定 |
|---|---|---|
| 2 / 1024 | −7.964947691906318，合法 | −7.966796875，TAU_BOUND |
| 43 / 22016 | −8.020465212473857，TAU_BOUND | −7.909423828125，合法 |

对角物理界7.916297492000999，加容差后7.966297492000999；一进一出不能被总计数掩盖，也不能仅归因于最终Q12舍入（第43帧差约0.111样点，包含上游链差异）。原报告保留分歧，未把定点对浮点一致性冒充定位精度。

## 非阻断发现、待验证与下一步

1. `run.py::floating/fixed/projection`：当前缺绝对声源存在门，quiet合法对不证明目标存在；`direction_accepted=false`与一致性诊断分离正确。下游不得使用advisory方位驱动已验收锁定输出。
2. `compare.py`正确区分整数/离散、浮点、字节；本机除summary外frames JSON也有字节差，不应沿用作者“仅summary不同”的本机结果描述。完整差异保存在comparison.json。
3. `H3-GAPS.md`保留reference25和29/25切换、DOA/DAS、存在门、RTL背压/资源时序、声学真值等缺口合理。预算为计数和逻辑工作集，非硬件实现保证。
4. A需提供的声源方式/活动区间/AGC与标定、中心相对位置及不确定度、手动指向与独立参考、PC或板端播放及数据流信息仍按H3-GAPS一次清单处理；本轮没有新增这些硬件/声学证据，不代填。缺失不阻塞本次离线诊断入库。
5. 9/14为阶段检查，9/16是B内部音频对照目标，9/18为完整评审包目标；本次不是阶段或整机验收。

## 证据与批次发布

同目录保存A生成的frames/summary/comparison、新测试日志、独立审计脚本及结果。A生成的两个NPZ与作者run02逐字节一致，使用 `npz-references.json` 记录SHA与唯一入库来源，不重复归档同字节大文件；原A输出在确认入库后方可清理。

本批候选与原证据全部原样保留。发布后核对共享main/origin/main/实际远端，检查本批未跟踪/忽略材料；共享PYNQ在做改动不属于本批，保留不提交。B的F盘工作树在本机不存在，不能代签其本地清理完成。
