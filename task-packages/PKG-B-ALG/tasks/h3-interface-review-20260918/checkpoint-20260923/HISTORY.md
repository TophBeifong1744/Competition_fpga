# 实际执行、复用及失败历史

2026-09-20实际执行；本页9/23是目标检查点，不倒签结果。已fetch最新main=1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78，在独立工作树 algorithm-closeout-20260923 建任务分支。复用28d5c77原21文件，原清单不变；未读改A共享未提交工程。

环境：CPython3.12.14、NumPy2.3.5，Windows。以下命令在仓库根执行；本机解释器为Codex Python runtime，所有输出在 `F:/NUEC/review-evidence/algorithm-closeout-20260923/` 全新目录。

```text
python -B -m unittest discover -s task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source -p test_candidates.py -v
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/run.py --out F:/NUEC/review-evidence/algorithm-closeout-20260923/run01
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/golden.py --study F:/NUEC/review-evidence/algorithm-closeout-20260923/run01 --out F:/NUEC/review-evidence/algorithm-closeout-20260923/golden01
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/golden.py --study F:/NUEC/review-evidence/algorithm-closeout-20260923/run01 --out F:/NUEC/review-evidence/algorithm-closeout-20260923/golden02
```

首轮13项测试通过；补充真实影响范围的整数/解析符号测试后16项通过；加入参考收益公式及拒绝播放源替代后18项通过。是逐步扩展的同一测试集，不累计写成47项独立测试。三份完整输出均保留。三个解析方向用例是代码符号单测，不新增声学模拟验证集。

run01完成八段候选、方向和48WAV。首个golden01因新增调用错误，把原模型的关键字专用参数作为位置参数传入，抛TypeError；原始完整stderr见evidence/golden01-console.txt。未产出任何golden数组（目录为空），不记为测试通过。只修正两处调用为inverse=/width=，golden02在新目录成功产生8探针120数组；旧失败日志没有删改。

失败不仅是代码首错：原门背景1119/1122放行；C1/C2仍不能分开背景；C3仍拒绝部分候选语音；三类tracker在候选区间无fresh锁定；自动音频全段回退单麦；整数/浮点功率不逐码相等。上述完整结果保留，不挑好段，不为改善结果反复搜索阈值。

封存依赖和本轮代码后，source/reproduce.py用于发布前全新目录再现与A复核。它前后验证清单并保存实际argv/退出码/stdout/stderr，比较48WAV、逐帧JSON和120整数数组；本轮回执以工具实际结果为准，不把作者自测当A批准。

完整入口实际在包外 reproduce01 运行成功：18项测试、48WAV逐字节一致、120整数数组精确一致、全部研究JSON一致，三条命令退出0；完整日志及result.json已附evidence/reproduce01。该结果记录的是加入本条回执前125项候选清单，加入回执后最终清单重新封存；算法代码、原件、结果不变。旧28d5c77清单从未覆盖。

首次提交前新增文件diff --check发现RESULTS.md末尾多一个空行，未提交/推送；原始提示见evidence/whitespace-first.txt。仅修正本轮报告生成器末尾换行，重生成同数值报告并更新尚未发布的候选清单。未格式化作者原件或旧冻结材料。

复用未重跑：八段格式/源标记复核（94b5fe7 B记录）；run05（7a17edd）原39测试/14golden及断流；S1、计时入口、FFT29覆盖、耐久；28d5c77既有跨250包/双槽1024/512golden。依赖哈希核对不是重复技术验收。

旧H3-RUN05-FIRST-FAILURE-RAW-01仍NOT_ARCHIVED（第二受控副本/访问控制未验证），本轮不声称修复该历史流程缺口，不改写旧批准。未执行AMD新仿真、ARM编译、综合时序、实板或真实音频播放，未签正式M1/H3/整机。
