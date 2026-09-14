import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).parent;W=pathlib.Path('F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg');E=W/'results/skill-review/b-rereview-20260914';C=E/'closeout';C.mkdir(exist_ok=False)
refs=json.loads((R/'refs-implementation.json').read_text(encoding='utf-8'))
assert refs['local_main']==refs['origin_main']==refs['direct_remote_main']=='d2cff38c19e06238bed9d4a195f72640527a1c12'
for name in ['materials-before-cleanup.json','materials-after-cleanup.json','branch-cleanup.json','worktree-cleanup.json','duplicate-run-cleanup.json','release-verification-implementation.json','refs-implementation.json']:
    shutil.copyfile(R/name,C/name)
for name in ['material_audit.py','verify_release.py','snapshot_refs.py','close_branches.py','cleanup_worktrees.ps1','cleanup_duplicate_runs.ps1','finalize_closeout.py']:
    shutil.copyfile(R/name,C/name)
for sha in ['357265f3744c343355bb646e2b0e56ed352bf0e7','d2cff38c19e06238bed9d4a195f72640527a1c12']:
    dest=C/'publication'/sha;dest.mkdir(parents=True)
    for name in ['main-before-response.json','candidate-before-response.json','commit-response.json','update-response.json','main-after-response.json']:
        shutil.copyfile(R/'main-publication-api'/sha/name,dest/name)
rows=json.loads((R/'duplicate-run-cleanup.json').read_text(encoding='utf-8-sig'))
verified=sum(r['verified_files'] for r in rows)
extra=f'''
## 发布后核对与本批收尾（B 本机）

| 项目 | 实际结果 |
| --- | --- |
| 分项 main 合入 | SKL-002：`357265f3744c343355bb646e2b0e56ed352bf0e7`；SKL-001：`d2cff38c19e06238bed9d4a195f72640527a1c12`。各自合并提交的第二父提交为准确批准候选，历史完整可恢复。 |
| 推送方法 | Git HTTPS 网络路径不可用，使用已有 gh Git Data API 上传新对象；返回 blob/tree/commit SHA 均与本地对象相同，更新 main 使用 force=false，发布前再次检查远端没有并发变化。未强推。 |
| 主线核对 | {refs['time_utc']}，实际 main 工作树 main、origin/main、直接远端 main 均为 d2cff38，0/0；从脏 develop 查询的 main/origin/main 也相同，未切换其当前分支。主线工作树干净。此收尾记录补交后再核对，最终 SHA 由用户回报给出，避免文件自引用。 |
| 提交内容验证 | 从已合入 Git 提交读取 B 证据清单621项及作者清单504+105项，共1230条，字节/长度/哈希全部匹配；两项批准目录与准确候选无 blob 差异；rtl/tb/sim/ps/vivado/hardware/deliverables 未改。活动入口及新报告本地链接可达。 |
| 本批有用材料 | 所有新源码输入、命令、原始失败/修复后日志、单元/结构/负例结果、合入后测试、哈希与清理核对已纳入本轮证据。检查已修改、暂存、未跟踪和忽略项；候选工作树中6份额外结果均已逐字节入库。本批新增未保存或未说明材料为0。 |
| 保留的既有工作 | F:/NUEC/develop 仍在 feature/member-b-algorithm，HEAD 57b86e043410c43aeca8d7421e0afe4ada3a8788，原有198项差异保留。其中9项旧 PYNQ 文件经 CRLF 规范化与历史 main 57c50e6 匹配，属于此前基线副本，已经可从Git恢复，没有夹入新候选或为了清零而删除。它们不作为本轮活动源码。其他长期/算法工作树均保留。 |
| 分支清理 | 删除两条已完整批准且无后续提交的远端短期候选分支 codex/toph/skl001-module-verification-20260914、codex/toph/skl002-pynq-validation-20260914；直接查询均404。B 本地不存在同名 heads/远端跟踪引用，未虚报本地删除。准确候选仍可由 main 合并父链恢复。 |
| 复核副本清理 | 删除 b-skl001-a7e1ea9、b-skl002-3ac597d、b-skl001-c562466、b-skl002-55039cf 四个已结束工作树。清理18个重复运行目录前逐字节核对{verified}份已发布文件；可重建 simulator 缓存按路径/字节数/哈希登记后删除，日志/输入/结果均保留。 |
| 历史保留 | 旧反馈远端仍为0ef0355642ea8719d5e4cdde0a38c531550218d4；反馈分支和其只读证据工作树、旧陌生模块/golden、作者r1/r2证据及旧归档均保留。F:/NUEC/review-evidence/skills-b-rereview-20260914 保留Git API获取/发布控制缓存与辅助脚本；可复核结果唯一入口为已发布 results/skill-review/b-rereview-20260914，不保留另一个活动工程。 |
| A 设备边界 | 无法访问 A 电脑，未处理或代签其162项混合旧候选差异。A 本机仍需对照新 main 保存/分类独有材料并安全同步、检查已修改/未跟踪/忽略项；不得以 reset 脏目录方式强行清零。 |
| 最终状态 | 两项限定实现已独立批准并分别发布；B 本批材料收尾完成。A 设备核对由A完成，不阻塞已获准的离线/模块发布。本记录在仓库不等于其他成员已收到消息，本轮未向A/C发送工具消息。 |

原始发布响应与核对见 closeout/；manifest-closeout.json 单独绑定本次新增收尾资料，先前 manifest-all.json、manifest-skl002.json 及作者所有历史日志/清单保持原字节。
'''
p=W/'docs/maintenance/skills-rereview-b-2026-09-14.md';p.write_text(p.read_text(encoding='utf-8')+extra,encoding='utf-8')
items=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(C.rglob('*')) if p.is_file()]
(E/'manifest-closeout.json').write_text(json.dumps(dict(files=items),indent=2)+'\n',encoding='utf-8')
print('Closeout evidence files:',len(items),'deduplicated files:',verified)
