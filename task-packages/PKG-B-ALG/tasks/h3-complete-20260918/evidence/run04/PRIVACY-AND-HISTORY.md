# run03 作者复现原件的隐私处理

原 evidence/run03/author-reproduction-result.json 含作者机器的绝对工作区及解释器路径。经拓芙明确授权，本返修分支从当前树移出仅此一个文件；原件未改写，现置于仓库外只读备份。旧提交 be3a2ed20d123a37bf79650f3d6a1685fc5d8625 亦保留可恢复的原始 Git blob，B 需取原件时应使用该准确提交，不应把当前树缺少该文件当作 run03 测试未发生。

- 原文件 SHA-256：97206dfd8e94c782cbc9c4d056870a484300bb411d7e3e07a66a95034fbfd43f；迁移后复核一致、只读。
- 脱敏摘要：原 run03 记录状态为 PASS_AUTHOR_REPRODUCTION_NOT_INDEPENDENT_REVIEW；8 个被统计的命令以及前后输入检查退出码均为 0；当时 H3 测试 29 项，沿用三路音频包报告 50 项。它是旧候选的作者自测，不延续为 run04 独立结论。
- run01 方向符号首错、run02 秩不足覆盖问题及 run03 其余原始证据没有被覆盖或重写。run04 是新的、可单独复核的证据目录。
- 新 source/reproduce.py 写入的命令记录会用 <REPO>、<PACKAGE>、<OUT>、<PYTHON>、<HOME> 脱敏。复核人可使用本机新目录获得完整执行日志，不应把含个人路径的原始日志提交进仓库。
