# S1 限定发布记录

2026-09-20。B限定PASS，审核8f708e42caf32c1de6f30726298e3edf0e1970b6，见B-REVIEW.md。

以直接远端确认的main d4f91054bd3c0dd417e3902c221cf02636fdfa65为基线，在独立s1-integration工作树仅导入本批186文件准确快照及包外B证据，不合入作者分支其他路径。作者原件和清单不改；S1候选留存实现仍在批次目录，未部署实际工程。历史check_scene依赖保持POLICY原版本，不因最新main有timerfixed入口就改用新依赖。

按9/17规则，集成后只复跑只读verify_delivery.py（44清单、BIN/UART/CSV/WAV、ELF、H1读取器），检查已暂存包与准确SHA逐字节相同、相关依赖字节未变；不重复17项导出测试、历史模型或硬件工作。集成结果见integration-check.json。B新测试写入独立副本的唯一新evidence目录，随后搬入B报告export-tests，未纳入作者冻结集合。

技术结论、数值诊断与未验证项见B-REVIEW；脚本原始输出及完整数值在本目录。主Python缺Matplotlib时使用既有Anaconda绘图，不安装或替换任务运行依赖。原件空白检查单独记录在integration-audit.json及压缩日志，不因保留原始生成文件而伪称全部通过。

此文写入时尚未推送；最终发布SHA、直接远端核对、本机main引用及本批材料处置由CLOSEOUT.md和最终回报记录。共享F:/NUEC/develop仍为原成员B任务分支，不切换、重置；A实际one、F盘工程、共享目录及其他任务均未操作。作者分支尚未确认无后续引用，保留；本次新建的干净B复核/集成副本在发布与恢复校验后清理。
