首次审计启动退出1：Python子进程调用的Git报 detected dubious ownership，status退出128；尚未读取依赖blob或执行数组检查。该次不是算法失败，也不是检查通过。

修复仅在本工作目录audit.py的Git进程增加准确源路径的 `-c safe.directory=...` 和 `GIT_OPTIONAL_LOCKS=0`。未修改全局或仓库Git配置；checks-01保留，后续结果写checks-02。原工具输出保留在本任务记录。
