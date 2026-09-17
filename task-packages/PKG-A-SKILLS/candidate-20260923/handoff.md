# 给“拓芙工作执行”的一页回执

## 交付入口与范围

- 统一入口：`task-packages/PKG-A-SKILLS/candidate-20260923/README.md`
- 固定main：`5cfa02e51af44bb5c930babf732ddc864a1ab6cd`
- SKL-001批准基线：`a7e1ea976da91ba735af5c0a79fffdc7d10c121f`
- SKL-002批准基线：`3ac597d1d16982e0a5c5a114202ca8568dc28d8f`
- 两个批准活动目录均与各自批准提交无差异；本轮只新增独立候选目录。

## 实际变化

- SKL-001：小写入口；随包、归属明确的C-RTL-003 PCM源码；本地case；保留
  elastic第二案例；新增纠错证据索引。
- SKL-002：保留full-loopback与既有测试；新增独立S2MM-only静态合同、
  外部payload schema、8组正负例重放、adapter API/状态机设计和PYNQ准入报告；
  `pynq_probe.py`未改且继续fail-closed。
- 没有修改one、生产RTL/BD/XDC、Vitis、算法或旧批准证据。

## 本轮实际验证

- 纯英文无空格目录：`E:/skill_candidate_20260923_run02`。
- SKL-001：7/7 runner单测；XSim 2025.2 的PCM 792、elastic 13800及恢复
  13800均PASS；data/ready/two-stage三个mutant均在simulate阶段按预期FAIL并
  保存首错。
- SKL-002：65个测试方法、74个subtest，0 failure/error/skip；1个静态正例
  PASS，7个静态负例按目标issue code FAIL；缓存陈旧、短输出、双超时按预期
  FAIL；board guard退出1、拒绝信息存在、未生成输出。
- 两个临时安装副本均返回 `Skill is valid!`。作者自检不等于B批准。

## PYNQ准入与限制

结论为 `BLOCKED / NOT_RUN`。缺目标PYNQ镜像/板级支持、同构建可部署
bit/HWH/manifest、目标机pynq/驱动版本、allocator/cache语义和Overlay解析。
本轮没有上板；现有Vitis standalone采集不受影响，也不能替代PYNQ证据。

## 工作执行下一步

1. 核对 `MANIFEST.sha256.json`、原始证据与失败记录，确认没有夹带其他任务。
2. 仅提交本候选目录，固定准确待审SHA并推送原待审分支或新任务分支。
3. 将准确SHA、范围、复现入口和上述限制交B做增量独立复核；不要把作者测试
   写成验收通过。
4. 9月25日前补最终隐私/许可/链接审计和提交形态复现；PYNQ仍不准入时保持
   BLOCKED，不强行上板。

完成安全停止点时再次查询远端：main仍为固定基线，未发现新的B H3分支或
近期H3提交；因此没有中断本Skill候选制作。
