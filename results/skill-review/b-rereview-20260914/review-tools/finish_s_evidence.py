import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).parent;W=pathlib.Path('F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg');E=W/'results/skill-review/b-rereview-20260914'
for name in ['skl001-postmerge-units','skl001-postmerge-examples','xsim-postmerge']:
    for p in (R/name).rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(R/name)
        if 'work' in rel.parts and p.suffix not in ('.log','.jou','.tcl'):continue
        target=E/name/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
tools=E/'review-tools';tools.mkdir(exist_ok=True)
for name in ['run_capture.py','audit_candidates.py','fetch_candidates.py','publish_main.py','prepare_d_release.py','prepare_s_release.py','finish_s_evidence.py']:
    shutil.copyfile(R/name,tools/name)
note='''# B 本轮独立复核证据

准确候选：SKL-001 a7e1ea976da91ba735af5c0a79fffdc7d10c121f；SKL-002 3ac597d1d16982e0a5c5a114202ca8568dc28d8f。

结论及实际命令：[B 复核记录](../../../docs/maintenance/skills-rereview-b-2026-09-14.md)。manifest-all.json 绑定本目录证据原字节；manifest-skl002.json 是首批发布时清单，后续新增输出另由全清单绑定。

- skl001-* / xsim-examples / s-independent：新候选执行的单位测试、结构测试、实际 XSim、B 原两级故障和独立见证及变体。每次保留编译/展开/运行原日志、inputs、result.json；vendor 生成的可重建 simulator 二进制不作为队伍源码发布。
- skl002-* / d-independent：新候选 55 方法/57 subtest，原 D1/D2 输入、14 次会话、60 项独立检查、guard 等。合成 bit/HWH 不可部署；模拟数据不得当硬件性能。
- *postmerge*：活动 main 路径的合入后实际复跑，输出都是新位置。
- candidate-audit：repair-manifest 与准确 Git blob/工作树核对。skl001-result-audit-r2 记录 Git LF 与外部 PCM 源检出 CRLF 的分别核对；初次严格字节审计及原始 FAIL 保留，未改写原日志。
- review-tools：复核时本机辅助脚本快照，不是 Skill 运行依赖；绝对路径记录执行来源，迁移时只在新的脚本副本中改工作根和输出目录。旧 reproduce.py 仍在旧反馈提交，版本锁未更改。prepare_d_release.py 首次遇到本机 GBK 解码问题后，其入口通知由 UTF-8 文件写入补全；不涉及作者实现或测试结果。

复跑行为可直接从准确候选调用所附 case.json / profile.json，而无需重用旧版本锁脚本。例如：新候选 run_xsim.py --case <本目录>/s-independent/fixtures/b-two-stage-new-tb/case.json --vivado-bin <2025.2/bin> --output <全新目录>；新候选 validate_profile.py --profile <本目录>/d-independent/thermal/missing-dma-ip.json --mode offline --output <新文件>。其原始命令和预期失败代码在报告和 command.json。

旧独立陌生模块/golden/原 S1 误 PASS 未重跑：[固定反馈与历史证据](https://github.com/TophBeifong1744/Competition_fpga/tree/0ef0355642ea8719d5e4cdde0a38c531550218d4/results/skill-review/b-20260914)。绝不将旧 SHA 上的工作改签为新候选结果。
'''
# Evidence is three levels below repository root (results/skill-review/b-rereview...).
(E/'README.md').write_text(note,encoding='utf-8')
post=json.loads((R/'xsim-postmerge/summary.json').read_text(encoding='utf-8'));assert post['status']=='PASS_DEMONSTRATION' and len(post['runs'])==6 and all(x['matched'] for x in post['runs'])
extra='''
SKL-001 合入后验证：从实际本地 main 仓库根再次执行同一 7 项单元测试及 run_examples.py，使用新的 xsim-postmerge 输出目录。PCM792、elastic/restored 各13800、三种故障均在仿真阶段检出，6 次全部符合预期。命令和日志见 skl001-postmerge-units/、skl001-postmerge-examples/、xsim-postmerge/。合并索引中的两个批准目录与 a7e1ea9 无差异。
'''
p=W/'docs/maintenance/skills-rereview-b-2026-09-14.md';p.write_text(p.read_text(encoding='utf-8')+extra,encoding='utf-8')
files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest-all.json']
(E/'manifest-all.json').write_text(json.dumps(dict(candidates=['a7e1ea976da91ba735af5c0a79fffdc7d10c121f','3ac597d1d16982e0a5c5a114202ca8568dc28d8f'],files=files),indent=2)+'\n',encoding='utf-8')
print('Evidence files:',len(files))
