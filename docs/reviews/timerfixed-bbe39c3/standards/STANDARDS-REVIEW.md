# Standards axis — bbe39c38dc36ccb4c0492f492b86f6c46d885fbe

范围：父提交8371f014711e04553749e6c2ffc29f34b9d5ccc9之后唯一交付commit；仅只读检查作者工作树，证据写在本目录。依据AGENTS.md、CONTRIBUTING.md、docs/team-workflow.md、docs/git-workflow.md及包README/OPERATOR/BUILD-RESULTS。

## 硬性行为问题

**[P1] 已检查的ELF没有绑定到实际下载字节。** `load_timerfixed.tcl:8-9`完成检查后，`:16`等待3000毫秒，`:25`才重新按活动build路径打开ELF。在等待期间以另一个产物替换该文件，脚本仍执行dow和con。两项全部mock硬件的反例先真实调用`verify_elf`检查新ELF `726a91fe…`，随后分别换成旧错计时ELF `7b5630de…`（真实合同检查拒绝：Wrong actual timer divisor）及另一合同有效修复版 `ebc576e2…`（不同于先前收据绑定内容）；mock dow均读取替换字节并继续。建议检查并加载同一受保护快照，协调构建写入。规则：CONTRIBUTING.md:9要求文档与实现一致；README.md:38声称检查后替换产物均拒绝。该文案也可能专指post→load期间，最终批准应明确覆盖范围；本反例针对load→dow窗口，与GUI绕过无关。

## 维护观察（非硬违规）

**可能的Duplicated Code：** `load_timerfixed.tcl:18,20,25`与`check_entry.py:134-135`分别硬编码同一套产物路径。当前路径已独立核对一致，但后续改名需同步维护；`test_load.tcl:13-14,29`只检查命令名和顺序，不校验参数，无法自动发现两处漂移。建议共享路径合同并对mock实参做断言。

## 实际验证及边界

- 作者Tcl四项原测试通过；独立七组补充通过，包含11种非法dry参数、含空格/字面元字符路径、改变cwd、实际硬件实参和10种步骤失败立即停止。
- 真实Tcl→Python的缺失应用反例在任何硬件mock调用之前拒绝。
- 两项竞态反例复现。竞态中的真实检查仅为verify_elf，其余完整gate前置条件模拟满足；没有宣称本机重建作者Vitis环境。
- 历史15项初测单失败、后续18项通过、Tcl环境失败及未装新环境的记录相符。整理后的Vitis尾段明确不是完整控制台。
- 生成物按冻结证据身份保存；不因个人绝对路径或已明确的编辑器缓存保守拒绝机械阻断此限定交付。
- 所有硬件命令均mock或禁止；没有真实connect、download、Run、编译或板测；作者工作树git status保持空。

证据：author-four-mocks.json、independent-loader-mocks.json、real-checker-rejection.json、artifact-race-results.json；重现程序run_tcl_checks.py与reproduce_artifact_race.py。本目录已有重现产物，第二个程序有意拒绝复用同名race目录，重跑应复制脚本到新的包外证据目录。
