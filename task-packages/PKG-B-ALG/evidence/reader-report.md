# H1 读取器本轮验证结果

结论：47项自动测试通过，A提供的15项读取器预期全部由B的新读取器实际执行并通过。使用的是固定码型及其受控修改，不是四麦声学模拟，也不是A的样例自检成绩。

最终源码、环境和逐测试状态见 reader-validation-final/validation.json；完整日志见同目录 tests.txt；两个样例的真实读取输出见 fixture-diagnostics.json。

| A 的用例 | 实际结果 |
|---|---|
| exact-uint64 | uint64存储；9007199254740992和9007199254740993保持不同 |
| pcm-boundaries | -8388608与8388607正确读为int32，无缩放 |
| gap | 保留缺失ID9007199254740994及drop/overflow；保留所有原行 |
| restart | 新acquisition从0开始可读取，不拼接前段 |
| unknown-schema | 拒绝并定位schema_version |
| swapped-header | 拒绝列序，物理行1 |
| duplicate-channel | 拒绝重复channel_order |
| pcm-overflow | 拒绝8388608，物理行2/mic0 |
| duplicate-id | 拒绝重复ID，物理行3/sample_id |
| silent-gap | 拒绝未标drop的跳号，物理行4/error_flags |
| error-inconsistency | 拒绝error=0但有overflow，物理行2/error_flags |
| unknown-coordinates | 保留幅值/格式诊断，方向禁止；不填猜测坐标 |
| unknown-error-token | 拒绝mystery，物理行6/error_flags；输入原样保留 |
| uint64-overflow | 拒绝18446744073709551616，物理行2/sample_id |
| uint64-maximum | 18446744073709551614和18446744073709551615均精确接受 |

另外32项测试覆盖BOM/CRLF、空行/空输入、整数写法/范围、JSON重复键/NaN/布尔值、坐标维度与未知说明、错误标志组合、全错误数据、版本冲突与会话回滚、采集重启、证据声明和命令行成功/错误路径。

code-pattern有6行；干净区间为零基半开[0,2)、[3,4)、[5,6)，长度2、1、1。数据行3和5的错误行被保留用于诊断，但不属于干净区间。restart独立保留2行。这些短码型不能组成1024点声学帧，读取器没有拼接或补零来制造可定位输入。

读取器返回格式诊断，不验证实际电平、采样同步、物理坐标或标定结果。accepted/calibrated引用的存在只作结构检查，人工真实性未确认；零错误标记不等于硬件通过。

实现限制：整段内存读取，只支持当前四列CSV；没有六麦格式转换、声学算法接入或小时级吞吐验证。config/geometry冲突检查需复用同一个ReaderSession；跨片段载入须按时间顺序。详见payload/docs/h1-reader.md。

当前PKG-B-ALG仍在持续开发。本轮完成读取器和异常诊断，下一步在同包内接分帧/统一算法入口及golden，不将本子功能拆成新的审批任务，不因等待场地或C材料而停工。完整包达到H3条件后交A复核和合入。
