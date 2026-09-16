# 离线构建顺序调整

2026-09-16，工程实现说明“离线Clean/Build可提前，B放行仍保留在上板前”后，用户回复“先不等b了吧”。本次据此推进用户操作的离线构建，不视作授权下载/运行，也不表示B已批准。

已完成：用户接入候选后，实际F盘four_mic_endurance的E1_PRECHECK_ONLY通过，见evidence/20260916_200439_pre_91508ff9cd。

下一步由用户在Vitis仅对four_mic_endurance执行Clean、Build，保存完整构建输出；不Clean continuous_platform，不修改原four_mic_continuous或Vivado，不Run。检查失败保留记录，不禁用入口绕过。

构建完成后由Codex只读检查实际对象、ELF、memory.map及检查记录，再核对加载配置。此时仍不是实板验证或独立批准。

本调整仅替代README/OPERATOR/INSTALLED-CHECK中要求等待B回执才能离线构建的顺序，不改变硬件范围、测试合同、上板操作分工或证据边界。
