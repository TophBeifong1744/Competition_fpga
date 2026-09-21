# PSB 修复 Spec 独立复核

审核 SHA：ca512a8be7978ab6ca2ade3d5e0b922e53a89c79。
原候选：fbbaa161098582ba1e5e112b86d39533769bb3e7。仅审修复目录的 C 增量及其合同。结论：Spec 轴限定 PASS，未发现新的阻断。

## 代码检查

- PSB-B-01：src/ps_bridge.c:195 开始全批聚合，208 对冲突置 INVALID，218 在 commit 前全批拒绝；219 后才提交。原 was_committed 保留，不因 revoke 清除。status=0 不覆盖 payload，但仍校验 binding。不同事务遇任一有效身份的一致性冲突，本批均无新 commit；后续显式 dispatch 才可提交未冲突事务，与 README 一致。
- PSB-B-02：174 先按 session 隔离；179 使用有界 slot 取值；184 未知当前事务或历史已提交事务 error 触发 terminal，192 在控制和新提交前执行 global_fault。STOP/RESET 后仍检查当前 session 晚错，新 session 旧回调按 STALE 处理。
- PSB-B-03：134 用尚无候选 slot 判断选中首 READY，UINT64_MAX 不再混同空哨兵。41 在生成新 token 前拒绝耗尽；publish 在 token 成功之后才设 READY。结合最终六个 generation 场景静态审查，不声称自然运行到 2^64。

## 本轴实际独立执行

新增 spec.c，不修改作者源码或证据。使用 GCC 8.1.0，分别 O0、O2：

```powershell
$src='F:/NUEC/r/psr/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/ps-semantic-bridge-repair-01/src'
$ev='F:/NUEC/review-evidence/ps-repair-ca512a8/spec'
foreach ($opt in @('O0','O2')) {
  & 'F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe' -std=c11 "-$opt" -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -I $src "$ev/spec.c" "$src/ps_bridge.c" -o "$ev/spec-$opt.exe" 2> "$ev/compile-$opt.stderr.txt"
  & "$ev/spec-$opt.exe" | Tee-Object "$ev/run-$opt.txt"
}
```

两种优化均退出 0，编译 stderr 空；各为 SPEC_PASS cases=13 assertions=279，不叠加成 26 个不同场景。

- 6 场景：commit→CLIP/STOP/RESET→晚错，含结果 release 后；确认 was_committed 历史、take 拒绝、fail-stop、无新增提交。
- 2 场景：正常 STOP/RESET、释放、新 session 启动，旧 session 错误回调与当前合法完成同批；当前事务可消费，旧回调不杀新会话。
- 4 场景：status=0 与完成双排列，payload 不替换；若其 binding 错误，则本批不能 commit 或 take。
- 1 场景：调用者 config/binding 修改，bridge 和结果快照不变，required_status 仍要求原完整集合。

官方 33 对照及最终 122 场景由主复核流程单独执行，本轴不将作者 run01/run02 或原缺陷记录器退出码充当独立通过证据。

## 范围

仅独立单执行者主机 C 候选及 PSB-B-01～03 相邻合同。原 0ab 引用不替换；a7 Python 返修仅独立合同背景。ARM/BSP、真实线程/ISR 并发、Vitis、CDC/RTL、实板、WCET、生产 ABI、实时/完整 H3 均未验证。本审不扩大此前软件归档批准。
