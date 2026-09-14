import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).parent;W=pathlib.Path('F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg');E=W/'results/skill-review/b-rereview-20260914'
def copy_evidence(name):
    src=R/name;dst=E/name
    if src.is_file():shutil.copyfile(src,dst);return
    for p in src.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(src)
        if 'work' in rel.parts and p.suffix not in ('.log','.jou','.tcl'):continue
        target=dst/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
for name in ['independent_s.py','audit_s_runs.py','audit_s_runs_r2.py','s-independent','independent-s','skl001-units','skl001-structure','skl001-examples','xsim-examples','skl001-result-audit','skl001-result-audit.json','skl001-result-audit-r2','skl001-result-audit-r2.json']:
    copy_evidence(name)
audit=json.loads((R/'candidate-audit.json').read_text(encoding='utf-8'))
(E/'skl001-candidate-audit.json').write_text(json.dumps(audit[0],indent=2)+'\n',encoding='utf-8')
report='''
## SKL-001：PASS（限定模块开发与实际仿真）

准确批准 SHA：`a7e1ea976da91ba735af5c0a79fffdc7d10c121f`；批准范围仅 `skill/fpga-module-verification/` 和 `task-packages/PKG-A-SKILLS/`。这是 0.3.0 的 S1 修复，原候选 `c562466805aff08201cd457cc2e6ee7464a3566f` 的旧批准不能覆盖新提交。B 没有修改作者实现，批准的源码和原始证据按候选字节进入 main。

独立 clean detached 工作树：`F:/NUEC/review-worktrees/b-skl001-a7e1ea9`。Windows / Python `D:/Python/python.exe` 3.13.0；使用明确路径 `D:/AMD/2025.2/Vivado/bin` 的实际 XSim 2025.2。SW Build 6299465 沿用同一安装环境的原始版本记录；本轮每次 xvlog --version 均实际返回 Vivado Simulator v2025.2，没有借 PATH 选旧工具。

### S1 关闭与实际执行

```text
D:/Python/python.exe -B -m unittest discover -s skill/fpga-module-verification/tests -v
D:/Python/python.exe -B skill/fpga-module-verification/scripts/run_examples.py --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-rereview-20260914/xsim-examples
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-rereview-20260914/independent_s.py
F:/STUDY/IT/Anaconda3/python.exe -X utf8 -B C:/Users/BryanZheng/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/fpga-module-verification
```

前两条从新候选仓库根执行。每次实际 argv/cwd/退出码和完整日志在对应 command.json/stdout.log/stderr.log；XSim 每阶段日志、源输入快照、合同/case 及 result.json 随证据保存。

| 独立执行 | 实际结果 / 证据 |
| --- | --- |
| 运行器单元测试 | 7 项通过；skl001-units/。涵盖工具/阶段/超时错误分类、缺失/多重 PASS、晚 fatal、零检查及拒绝覆盖旧输出。 |
| 正确 PCM | 792 次比较通过；xsim-examples/pcm4/。符号扩展，宽度 2/24/32。 |
| 正确及恢复 elastic | 各 13800 次实际检查通过；每个宽度 1/8/16 均 sent177 = consumed176 + discarded1 + pending0；xsim-examples/elastic/、restored/。 |
| 数据、ready、两级错误 | 全部编译/展开成功，在仿真阶段被检出；xsim-examples/bad_data/、bad_ready/、two_stage/。两级首错 cycle=2、after_edge=1，expected valid=1 / actual=0。 |
| B 原始两级副本配新 TB | DUT 复用旧反馈原件，只把 TB 换为准确新候选；同样 cycle=2、after_edge=1 检出 one_edge_valid；s-independent/b-two-stage-new-tb/。 |
| B 独立延迟见证 | 正确源通过 2 项；同一两级副本在首个接收边沿后 valid=0/data=00，预期 1/5a，仿真失败；s-independent/b-witness-correct/、b-witness-two-stage/。 |
| 合法复位 ready 变体 | 只在复位期间拉低 ready，原激励/新 TB 仍通过 13800 项；s-independent/reset-ready-low/。没有增加合同外复位 ready 限制。 |
| 容量与未知态变体 | 满槽仍 ready 被 slot_ready 检出；payload X、payload Z、valid X 各在仿真阶段被检出；s-independent/ 下同名目录。 |

共执行示例 6 次和独立针对性 XSim 8 次，14 次均符合预期。所有预期负例要求 version/compile/elaborate 返回 0 且未超时，stage=simulate、FAIL_SIMULATION、退出 1；不以编译或工具启动失败充当故障检出。计数按实际日志记录，13800 不是人为凑数门槛。

代码审阅与同输入实测相互印证：`check_slot(0)` 在正边沿 NBA 前检查旧槽，`check_slot(1)` 在 #1 后检查新槽。占用由接收/消费的独立队列计算，严格 0/1，valid 必须对应占用，有效数据用四态全等比较；正常 ready 必须等于空槽或下游 ready。故两级到达延迟和两槽容量不能仅靠末端事务顺序蒙混通过。

负边沿驱动、正边沿握手和 NBA 后观察没有竞争；同步低有效复位优先，丢弃在途事务计入 discarded，复位数据清零；背压期间保持 valid/data、空槽接收、每拍启动、同拍消费/替换均保留。固定种子、原合同和激励未放宽，原四拍排空未缩短。计数每拍核对 sent=consumed+discarded+pending，最终 pending0。r1 的 13806 属于作者早期错误约束记录，本轮最终依据 r2，不要求恢复那条限制。

### 版本、历史复用与文档

repair-manifest 的 504 项全部与新提交 Git blob、检出文件原字节及字节数一致；作者 fix-r2/examples-r2/regressions-r2 对应最终源码，旧 r1/旧日志/旧清单保留其历史身份。B 对 14 次新运行核对了 191 条日志、快照、工具阶段、源码和计数关联；见 skl001-result-audit-r2.json。

首次辅助审计将 PCM 工作树字节直接等同于 Git blob，报告 1 项不一致（skl001-result-audit/ 与原脚本/JSON 保留）。原因是该仓库外部引用的生产 PCM 文件在 Windows 检出时由 LF 转 CRLF；实际仿真输入快照与工作树逐字节相同，git hash-object --path 清理过滤得到的 a300f74c48fe68eb34247d7a6f1cf97a28778f58 与候选 blob 完全一致，差异只为 CRLF。新增 r2 审计分别记录精确字节、检出转换和 Git 身份，191 项通过；没有改原始源码、日志或哈希清单掩盖差异。

旧版 B 陌生 signed8 饱和加法评测本轮 NOT_RUN，明确复用 `c562466805aff08201cd457cc2e6ee7464a3566f` 上的历史结果：隔离执行方只获 Skill、需求和必要输入；未知 -128+-1 故障定位后，同激励修复复测 66343 笔、337372 检查，B 自算全部 65536 组 golden 与实测零差异。旧原始失败、修复源码、结果及 golden 均保存在[固定反馈提交](https://github.com/TophBeifong1744/Competition_fpga/tree/0ef0355642ea8719d5e4cdde0a38c531550218d4/results/skill-review/b-20260914)。本次未修改旧 reproduce.py 版本锁，也未冒称陌生评测在新 SHA 重跑；按用户指定只复用原独立延迟见证并补针对性变体。核心 SKILL.md、run_xsim.py 相对旧候选保持原字节。

README 对场景、调用、失效条件、效果、C 的 PCM 来源/MIT 归属、独立导出规则及可见 AI 纠错说明足够；结构验证通过。PCM 示例需仓库已有的单个维护源或带归属导出；独立 elastic 可脱离声学工程使用。旧工程协作 Skill 保持退役，例子未接入生产 RTL。

## 分项发布进展

SKL-002 已先行独立合入并非强制发布：`357265f3744c343355bb646e2b0e56ed352bf0e7`（父提交 57c50e6 与准确候选 3ac597d）。发布后实际本地 main 工作树 `F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg` 的 main、origin/main 及直接 gh API 查询远端均为该 SHA，0/0，工作树干净；Skill 范围与批准候选逐 blob 一致。SKL-001 不作为该次发布的前提。
'''
p=W/'docs/maintenance/skills-rereview-b-2026-09-14.md';p.write_text(p.read_text(encoding='utf-8')+report,encoding='utf-8')
p=W/'skill/README.md';t=p.read_text(encoding='utf-8');t=t.replace('SKL-002 has independent B approval for its offline implementation; SKL-001 repair review is in progress.','Both Skills have independent B approval at the limited scopes below.')
t=t.replace('| SKL-001 [fpga-module-verification candidate](../docs/maintenance/skills-publication-2026-09-14.md#skl-001) | Module contract, RTL/self-checking TB development, real XSim execution, first failure and repair/retest | 0.3.0 author candidate: 792/1125 normal checks, two rejected DUT faults and restored PASS; B held-out use/review pending |','| SKL-001 [fpga-module-verification](fpga-module-verification/README.md) | Module contract, RTL/self-checking TB development, real XSim execution, first failure and repair/retest | B PASS (module simulation), exact a7e1ea9; PCM 792 / elastic 13800 checks; S1 timing/capacity fault independently rejected |')
t=t.replace('SKL-001 remains on its exact repaired candidate until its separate decision.','SKL-001 is active at its approved module simulation scope.');p.write_text(t,encoding='utf-8')
for rel in ['AGENTS.md','docs/maintenance/skills-publication-2026-09-14.md']:
    p=W/rel;t=p.read_text(encoding='utf-8');t=t.replace('SKL-001 修复仍在独立复核。','SKL-001 准确 a7e1ea9 也已获得限定模块仿真 PASS，按准确范围单独接入。').replace('SKL-001 修复另行复核。','SKL-001 准确 a7e1ea9 已另行通过限定模块仿真复核，按准确范围单独接入。');p.write_text(t,encoding='utf-8')
print('Prepared SKL-001 review evidence')
