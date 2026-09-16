# 独立证据复现与边界

本目录属于B的包外需求轴复核，不是作者测试目录。固定工作树HEAD为5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c。

## 最终归档绑定复现

输出需选择尚不存在的新目录，避免覆盖本次记录：

```powershell
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/NUEC/review-evidence/endurance-5606e1a/spec/binding_audit.py' --repo 'F:/NUEC/review-worktrees/endurance-5606e1a' --out 'F:/NUEC/review-evidence/endurance-5606e1a/spec/binding-new'
```

`binding04/result.json`为最终结果。真实对象SHA为4eeb96edabcb79b2b6df29bbdbe2c67ee3532b14a71bfbe08117f4df63a3dc15，ELF为75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449。只复用current_build的ELF容器解析，未调用E1完整gate、编译器或硬件；源码比对、合同读取、main调用和调度实参追踪由独立脚本完成。

main+1140处`e59fe120`取常量池指针，main+1172及+1200的`e8be000f`各后增16字节，+1204复制到r9，+1212的`e4993004`再后增4字节。该地址加36等于endurance_schedule符号1074992；+1252的`e1a02009`将r9传入r2，+1264直接BL到session_run_config符号1052568。这是固定归档指令人工核对，不是通用ARM反汇编器。

保留中间观察：binding01仅核对表和调用；binding02因B脚本过窄地只寻找直接常量/MOVW+MOVT引用而断言失败，无result.json；binding03保存扩大后的原始指令观察；binding04已按实际io初始化数据尾部相邻布局验证实参指针。该失败属于B分析脚本，不是作者gate失败。

## 期限边界模型

编译实际E1 portable核心，复用原fake外设但不运行其原16项套件。仅新增在已达到短段最小组数、尚未STOP时推进模拟时钟的回调。输出：

```text
case=resume_after_total_deadline result=OK jumped=1 elapsed_us=12000140 deadline_us=12000000 groups=576000 packets=2304 stop_sent=1
```

实际编译参数：

```powershell
& 'F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe' -std=c11 -O2 -Wall -Wextra -Werror -Wno-misleading-indentation '-IF:/NUEC/review-worktrees/endurance-5606e1a/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/proposed-src/continuous' '-IF:/NUEC/review-worktrees/endurance-5606e1a/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/tests' 'F:/NUEC/review-worktrees/endurance-5606e1a/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/proposed-src/continuous/continuous_core.c' 'F:/NUEC/review-evidence/endurance-5606e1a/spec/deadline_boundary.c' -o '<新的包外可执行文件路径>'
```

首次B夹具使用`%llu`，本机MinGW8默认printf格式检查不支持而拒绝编译；原源保留为deadline_boundary.attempt01.c。改为本例数值范围内的unsigned打印，原Werror不变，编译/运行均退出0。工具初次报错保留于任务调用记录，本目录不声称保存了完整原stderr。退出0表示观察复现，不表示硬期限要求通过。根README明确期限只针对组数仍不足，因此最终判断为合同边界，非阻断、非板上故障注入，也不追加硬件任务。
