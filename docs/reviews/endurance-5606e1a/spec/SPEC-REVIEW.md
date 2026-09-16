# E1 需求轴复核

对象：5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c。**未发现阻碍本次限定实现/证据归档的新问题。**

实际 src 的7项文本哈希符合 POLICY；proposed-src 的4文件与归档应用逐字节一致。对象及ELF均含正确10字段合同与11段调度表。另独立追踪真实ELF的main：常量池指针经36字节后增恰到endurance_schedule，随后作为r2传入session_run_config；对象存在同位置R_ARM_CALL重定位，排除只放无关常量表。源码main_continuous.c第90～102行对应一次300秒、十次10秒及排空后段间等待。timer_layout.py第44～107行仅容许两种常量池对齐，仍约束计算指令、除数、重定位和真实调用目标。

非阻断边界：根README第17行只承诺“达到run_us+2秒仍未达到组数时失败”。独立C模型在组数达标后跳时，实际核心返回OK（12.000140秒）；因此core第73～77行不是任意CPU停顿下的硬停止期限，不违背上述限定条件，亦不推翻正常实板记录。

批准范围仍为300秒加10次10秒的源码/构建/实板记录归档；不是连续400秒、一小时、M1/H3或安全加载工具批准。旧TF入口限制已披露，不重复作为本批阻断。

证据：`binding04/result.json`、`binding_audit.py`、`deadline_boundary.c`和`deadline_boundary.log`。全部离线，未改作者文件，未构建ARM或操作硬件。
