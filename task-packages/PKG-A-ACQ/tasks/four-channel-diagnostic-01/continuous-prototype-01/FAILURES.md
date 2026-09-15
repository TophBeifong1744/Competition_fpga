# 失败、修复与重跑记录

失败原件没有覆盖。完整原目录快照存入delivery-01/history，来源及压缩包哈希见HISTORY.json；最终工作版本不是把失败标记改成PASS。

|运行|真实现象|处理/后续范围|
|---|---|---|
|ss-cont-build-01、02、b03|本机Vivado file normalize错误解析C用户目录下一层（AppData或.codex），快照路径安全检查拒绝|保留拒绝；改到允许写入的E工作区独立目录。未去掉路径保护|
|F:/ss-cont-build-03申请|自动审批服务容量错误，未执行、未创建该目录|没有绕过该目录拒绝；使用已有授权工作区。不是设计失败|
|continuous-work04|Common 17-539，无法加载tclapp::support::appinit 1.2；未综合|只给当前构建进程及子进程补安装目录TCLLIBPATH，无全局配置写入|
|continuous-work05|预检发现AMD安装data目录是junction，拒绝未解析路径|只读安装目录先resolve，输出目录仍拒绝junction|
|continuous-work06|补appinit后，仍无法加载xilinx::xsim Tcl应用|补齐已有安装包的搜索路径，不伪造/stub工具功能|
|continuous-work07|add_files把含空格路径当文件列表拆分|改用Tcl list传入单一文件路径|
|continuous-work08|update_module_reference传入BD cell对象失败|改成实际IP对象get_ips，与AMD命令合同一致；不是RTL修正|
|continuous-work09|Windows Script Host启动器提示Access is denied，未启动综合，Vivado等待|核对本次PID/启动时间后只结束自己的等待进程；改成直接Vivado综合/实现命令|
|continuous-work10|真实综合/路由/bit通过；-include_bit导出查找未运行的impl_1记录而失败|不篡改GUI运行状态；export11在副本上导出hardware-only XSA，单独绑定实际bit，BSP核对通过|
|continuous-work12|最终入口全流程新跑|功能设计未改，实际重新综合/路由/bit/XSA并编译PS，结果通过但未上板|
|ss-cont-sim-03|-generic_top P=250在Windows批处理调用中被拆成P与250，elaboration失败|改TB实例参数包装，sim04及最终sim真实跑250/1024配置通过|

其他sim01/02/04、host01/02、ps-final-01、safety-final-01也原样保存，最终选用的证据另在evidence中展开。

程序故障注入不是上述工具故障：主机C测试中的timeout、错号、长度、guard、溢出等是预期拒绝输入，日志记录expected；RTL故意制造背压溢出/失步验证锁存。没有用清零、补样、重新编号或改golden消除错误。

源码/接口定位参考：[AMD update_module_reference命令合同](https://docs.amd.com/r/2023.1-English/ug835-vivado-tcl-commands/update_module_reference)。本轮真正执行版本为2025.2，最终命令与日志原件保留。
