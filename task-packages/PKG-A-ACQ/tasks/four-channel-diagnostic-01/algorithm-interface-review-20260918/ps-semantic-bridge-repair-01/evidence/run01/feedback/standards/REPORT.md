# B Standards 复核

准确SHA `fbbaa161098582ba1e5e112b86d39533769bb3e7`。已读发布入口、README/CONTRACT/MEMORY/HISTORY，复用AGENTS/workflow。

完整性通过：独立check.py退出0；实际1784份新增＝1481份候选包＋303份发布材料，原文件修改0。1479项封闭清单、字节数和清单摘要正确；所有新增文件匹配Git blob；32条历史绑定对应8份准确原件。run01失败、历次源码和sanitizer缺库记录保留。主机内存容量与ARM布局/真实DDR、软件批处理与异步硬件的边界清楚。

**需修改：有限generation边界。** `ps_bridge.c`中token_new允许生成UINT64_MAX，但frame_acquire以UINT64_MAX为初值且只选严格较小值。独立GCC C11/O2反例：正常输入1000行，仅按合同允许的白盒计数注入MAX−2，再正常enqueue/pump24行，生成READY/MAX帧；acquire却返回WAIT且active=1、failed=0。应使合法MAX帧可取得，或一致保留该值并显式拒绝。这是软件边界缺陷，不是实板故障证明。

另已向Spec轴交叉报告同session非法slot错误被归为STALE的合同疑点，由其独立裁决。无单纯风格阻断；不批准生产、ARM、WCET或H3。

实际命令：`python -B check.py`；`gcc -std=c11 -O2 -Wall -Wextra -Werror -I <原src> generation_max.c <原src>/ps_bridge.c -o generation_max.exe`；运行该exe。编译0、运行0表示预期缺陷复现；源码、stdout和results.json同目录。原包未修改。
