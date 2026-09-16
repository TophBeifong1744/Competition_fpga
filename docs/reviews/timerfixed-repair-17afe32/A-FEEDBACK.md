# 给 A 的修复提示词

请继续修复 TF-B-02-R1，勿合入 main。

仓库：TophBeifong1744/Competition_fpga。原分支：codex/toph/timerfixed-entry-20260916。此次受检 SHA：17afe32cebcff742bb2f9486388e91d9403f83dd。B反馈位于 review/member-b-timerfixed-bbe39c3 分支的 docs/reviews/timerfixed-repair-17afe32/，先读 B-REVIEW.md 和 spec/REVIEW.md，并固定B给出的准确反馈提交。

本轮82项Python测试及14次Tcl模拟通过，TF-B-01的ELF入口检查和TF-B-03的封存锁在限定离线范围关闭。唯一阻断为command_contract.py:52-53：把绝对-Wl,后缀整体按路径normpath，吞掉了GCC按逗号拆分的额外链接参数。

归档 -Wl,"F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/lscript.ld" 加入 ,-L,/../lscript.ld 后被verify_link_output错误判等；在该后缀前插入 ,-e,0x01000000、,--defsym,REVIEW_MARKER=1、,--wrap=XAxiDma_SimpleTransfer 也均被误接受。证据及复现脚本在spec/run01、extra01、check_arguments.py、extra_link_flags.py。这是命令比较组件反例；B没有声称错误entry通过全部gate，也没有运行ARM链接或板卡。

请先解析-Wl子参数，仅规范化确定的路径操作数；未知复合布局拒绝，不能删除参数或笼统忽略差异。保留选项、宏名/值、引号、分词和顺序。加入这4个反例及合法路径变体正例，再复跑现有82项/14次Tcl和原B负例，确保启动与锁保护不回退。

只改timerfixed-entry-01范围，保留原件、旧清单、此次17afe32证据和失败历史；新修复/复跑输出另存，不覆盖B脚本或旧日志。未执行的现场gate、新编译、真实XSDB下载、实板和长稳继续明确标注。不要覆盖实际工程引用入口或代签共享目录同步，不新增M1/H3/阶段门。

交回准确远端SHA、相对17afe32改动范围、新清单、命令/结果/失败历史与未验证项，等待B独立复核。B明确通过前不合并。
