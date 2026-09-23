# Issue 26：实体迁移诊断证据

基线 `0a5f544893cff1094bcd1bad5346a1cf05790707`；范围仅为活动文件搬迁和入口适配。准确交审版本以 PR head 为准；真实非作者批准尚未取得，不能自行合入 main。

## 实际运行

Windows、PowerShell 7、Python 3.14.6、Vivado Simulator v2025.2。`validation/run-manifest.json` 保存完整 argv、cwd、输出目录、时间、逐项退出码和日志哈希；`validation/summary.json` 保存实际加载路径、检查活动和输入身份。所有入口从候选仓库根运行，工具明确指定 `F:/AMD/2025.2/Vivado/bin`，不使用 PATH 中其他版本。

| 命令/检查 | 退出码 | 实际结果 |
| --- | --- | --- |
| `xvlog.bat --version` | 0 | banner为2025.2 |
| `pwsh -NoProfile -File simulation/run_regression.ps1 -VivadoBin F:/AMD/2025.2/Vivado/bin -OutputDirectory <新codex_out目录>/regression` | 0 | 7/7 case完成 |
| `pwsh -NoProfile -File simulation/run_servo.ps1 -VivadoBin F:/AMD/2025.2/Vivado/bin -OutputDirectory <新codex_out目录>/servo-1mhz -ClockHz 1000000` | 0 | 39 checks |
| `python -B scripts/check_h1_fixtures.py` | 0 | 原H1样例读取检查 |
| `python -B scripts/run_module_skill_examples.py --case all --vivado-bin F:/AMD/2025.2/Vivado/bin --output <新codex_out目录>/skill-examples` | 0 | PCM4 792、elastic 13800 checks |
| regression指定非codex_out目录 | 1 | 预期拒绝，未启动EDA |
| regression复用已存在输出目录 | 1 | 预期拒绝，既有日志未改变 |
| Skill适配器复用已存在输出目录 | 2 | 预期拒绝，既有日志未改变 |

结论仅为 `DIAGNOSTIC_SMOKE / SIM_SMOKE / DIAGNOSTIC_ONLY`。原始日志的PASS保留原文，不转为新功能/Skill/成员/整机批准。37个运行输入前后稳定；11份HDL/TB和5份H1数据原字节不变；清单只改变11项target和7项sources，来源、历史哈希及批准状态不变。实际编译加载新路径，Skill源、快照与编译副本一致。

`static-checks.json`为写批自检：另包含两个模型，共18份字节及Git blob身份、62文件移动、ignore及链接检查。既有4份六麦WAV缺项不是本轮新增断链；官方PDF存在Git树，只是未展开到稀疏工作树。

## 原始证据与边界

- `validation/`归档原始文字/JSON/Tcl日志及诊断记录脚本；`archived-log-hashes.json`列出106文件哈希、合计211635字节。没有修改旧原始清单使哈希通过。
- 可重建编译库、波形和重复源快照仅留本机`codex_out/layout-validation-01/`，不作为活动源码提交；加载依据为编译日志和原件/副本哈希。
- 初次记录器预检误取稀疏检出未展开的历史来源；在启动任何EDA前改为实际执行依赖，不是DUT或仿真失败，见summary限制说明。
- 实际Tcl导入、综合、实现、STA、CDC/RDC、板测、桌面BAT/Questa、声学/FFT/耐久、实际one操作均NOT_RUN；工程adapter仍UNVERIFIED。旧input-boundary固定architecture哈希在迁移前即不匹配，本轮未重跑或改checker。
- 未修改产品/TB/checker。舵机参数候选仍待独立复核；H1样例检查不是B生产reader验收；Skill正例路径诊断不是其完整正负例重新批准。

## 交接

B复核本轮准确SHA、迁移身份、关键入口差异与原始证据，按疑点做最小必要复现，不重审全仓。真实非作者批准后才合入、快进共享main，核对local/origin/直接远端及本批遗留。AI终审不能代签B。

旧新映射及299MB本机保留材料的位置见[迁移说明](../../../document/layout-migration.md)。共享main的108项无关未提交材料保留，未夹带候选。本轮没有删除原始实验文件，仅删除两个空目录。
