# 动态时间语义及9/23实施边界

本页为待裁决合同。D=父目录 `dynamic-das-20260921/dynamic_das.py`；旧固定= `fixed-nodes-20260921/b5b6/stream_das.py`。二者均保留，不把新结果倒签给旧合同。

| 项 | 已批准离线实际行为 | 生产尚缺/责任 |
|---|---|---|
| 8前视/17历史 | D输出emit=t对应源局部n=t−8；延迟±8，非零邻点位于[t−16,t]，整数−8不读取零权重右邻点 | A映射原uint64 sample_id及session/interval；局部n不是原ID，不能用浮点；gap后重建映射，禁止跨interval拼接 |
| 旧9前视 | 旧固定StreamDAS总读右邻点，零延迟也可能等1点，最坏9；只获固定延迟16组PCM批准 | 保留旧golden，不宣称其HOLD/TTL/动态均通过；A+B选择具体profile |
| startup/flush | D启动前8个输出为0、n<0；真实EOF补8个尾输出，真实记录外取0；不是每个chunk补尾 | A输出包显式区分startup/source_sample；flush不是STOP，也不能把输入缺号补0伪装连续。final之后再push/control拒绝；真实外设flush握手未实现 |
| available | D控制在push前当前物理time接收，仅影响该emit及之后；调用者必须按控制到达点分块 | 流水线真实available=完成状态可见时刻，不能倒填帧尾；A提供采样时钟/PL计数转换与延迟上界 |
| TTL | D采用emit坐标，emit>valid_through才过期；旧tracker ready及TTL均+8映射。同拍fresh先处理再expiry | A+B决定生产统一时基；already-expired控制必须丢弃；输出等待不能暂停物理TTL，不能将源ID/emit/CPU时间混用 |
| HOLD | D不改延迟/截止；携带新TTL/方向拒绝 | 显示held_angle不能当fresh；不得通过HOLD续租 |
| 串行pending | 淡变480点，最多两beam端点+一个最新目标，新的pending覆盖旧的，完成当前淡变才切仍有效目标 | 并非每请求必执行；稳定新请求最多等480再淡变480。A需裁决此取舍，不默换旧立即重定向 |
| STOP/SEARCH/TTL | D清期望目标，不取消已开始的淡变；最坏960点≈20ms才完全mono。A实测反例有959点等待 | 这是音频平滑回退，不是硬件急停。fatal session STOP/reset必须另行取消在途输出/方向。A决定硬停与平滑STOP是否分信号 |
| reset | D无reset方法；新session用新对象，清history/方向/TTL；控制不带session身份 | A真正同步复位、epoch和有限计数溢出；不得把new Python object当CDC复位证明 |
| 背压 | D push是离线同步函数，无ready；返回数组/输入块均无部署内存界 | 新checker只检查捕获轨迹的valid/payload保持、顺序、有限stall与取消。A提供实际缓冲、服务界、队满fail-stop及持续吞吐 |
| 原子提交 | f879提交谓词和a7f70c5 Results返修已限定通过：当前epoch已提交晚错fail-stop，旧epoch回调审计，新session可换配置 | 生产还需所有FFT/IFFT输出计数/TLAST/index/status汇总、不可变配置身份、可靠available、error/reset优先，再一次commit；PS C/RTL未实现证明 |
| late error | 已提交事实不能撤回，故障审计并停止当前会话后续发布；旧epoch回调不能杀新会话 | 已消费PCM无法“撤销”。A接实际晚status及致命错误；B checker只有同步捕获顺序模型 |

## 轨迹准备材料与使用

`trace_scoreboard.py`读取JSON列表，每行对应**连续捕获tick**，从0递增，不得省略等待拍；`now`为session局部物理采样计数，可以多拍不变。事件先于当拍commit/输出检查，reset/fatal优先。`session`须唯一非空字符串，frame为uint64，config为调用方冻结配置哈希；这是检查schema，不是线缆ABI。

轨迹中的 `submit.expected` 必须等于命令行外部给定的完整完成集合，不能由DUT删状态降低标准。当前夹具集合仅`fft ifft`，明确是检查器单元夹具，不代表真实14事务；9/23全分支应独立绑定 gate_fft0..3、doa_fft0..3、ifft0..5以及实际required后级状态。提交前每unit恰好一条最终status；真正TLAST/索引/输出数量须由现有IP scoreboard先验证，并由A桥接到该unit完成事件，不能只见TLAST生成status。

输出payload包括session、emit、source_sample=emit−8、available=emit、pcm。该等式只适用于D离线profile；真实硬件有额外处理延迟时必须新版本合同和测试，不能给轨迹改时间伪装相等。ready等待期间payload包括available保持，now仍反映真实时钟。输入采样源不因ready暂停；本checker没有实现输入FIFO或证明其容量。

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/trace_scoreboard.py <capture.json> --max-stall-ticks <已约定拍数> --expected-units <完整状态集合>
```

`evidence/run05/checks/valid-trace.json`为可跑样例；其他命名反例应退出非零。`late-reset-trace.json`和`reset-cancels-stall.json`分别覆盖已提交晚错/旧epoch回调及复位取消被背压输出。实际硬件capture目前**NOT_RUN**，没有以样例充当硬件通过。

本轮不新增帧/门模型，不复审E01～03；checker只是B交给A的可运行准备材料。生产完整实现、有限身份回绕、输入背压、同步/异步事件同时性以及输出设备中止仍属于9/23工程工作。
