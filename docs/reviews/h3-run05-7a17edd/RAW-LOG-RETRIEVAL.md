# run05 首错原始日志的受控取回说明

## 2026-09-21当前状态：ARCHIVED_LOCAL_CONTROLLED

拓芙本轮确认授权后，在仓库外创建第二原字节副本：
`%USERPROFILE%/.codex/visualizations/2026/09/07/01a07c21-b7f9-74d2-92c5-7f8d235d8379/private-evidence-backup/H3-RUN05-FIRST-FAILURE-RAW-01/run05-first-failure.raw.log`。
从该副本恢复为同目录`restore-check.raw.log`并读回，两者均950字节，SHA256均为`DCF5A3FBE69CA7CD1D5537371B7F7A21777D770DFCCB110F71A67DD10C3762EE`；原件未修改。目录已禁用权限继承，仅当前拓芙账户、SYSTEM、本机Administrators具有允许访问项，文件继承该限定ACL。实际Get-Acl确认目录保护为true、文件仅上述三项；普通沙箱复读被拒，授权账户复读成功，未为沙箱放宽权限。

实际操作：先验原件长度/哈希，再创建新目录，以icacls移除继承并对上述三身份授权，Copy-Item按字节备份与恢复，Get-FileHash/Get-Acl核验。不公开原文，不改只读原件、不向B发送。此为**同机独立目录可恢复副本**，不是独立介质/异机灾备；B取回仍NOT_RECEIVED。归档/ACL缺口在上述本机范围内关闭，不扩大技术批准。以下NOT_ARCHIVED表保留为9/20历史。

2026-09-20，A/主流程实际核实文件存在、长度、只读属性和SHA-256；未运行技术测试，未公开原始日志内容。

| 字段 | 核实结果 |
| --- | --- |
| 制品编号 | `H3-RUN05-FIRST-FAILURE-RAW-01` |
| 保管人 | A / 拓芙（Toph Beifong） |
| 存放设备 | A 当前 Windows 开发电脑；非 Git 目录 |
| 存放路径 | `%USERPROFILE%/.codex/visualizations/2026/09/09/01a086de-c5a0-7ee2-b46c-c0bd5b6d3dfd/h3-private-evidence/run05-first-failure.raw.log`；这里的USERPROFILE指A的Windows用户目录，不是B电脑目录 |
| 字节数 | 950 |
| SHA-256 | `DCF5A3FBE69CA7CD1D5537371B7F7A21777D770DFCCB110F71A67DD10C3762EE` |
| 文件属性 | `IsReadOnly=true`；只读属性不等于访问控制或已完成异地备份 |
| 公开脱敏副本 | `task-packages/PKG-B-ALG/tasks/h3-complete-20260918/evidence/run05/first-failure.redacted.log`，不冒充原字节 |

取回流程：B或获授权复核人向A报制品编号与上述SHA-256；A从该位置以文件附件私下提供原字节，由接收人核对950字节和SHA-256，再记录接收时间与核对结果。原件包含个人绝对路径，不放入公开Git；不以复制脱敏件、改换行或重新运行失败实验代替原件。需要迁移时须保持原字节并补记新位置。

**当前归档状态：NOT_ARCHIVED。** A已验证单一原件身份及取回位置，但第二个可恢复受控副本和访问控制尚未验证；只读属性不能代替访问控制。本轮未发送B、无收件回执，不宣称缺口完全关闭，不扩大LIMITED PASS。

## 准确首错命令与退出码（从当时执行记录恢复）

执行记录时间：2026-09-18 05:45:36～37 UTC（北京时间13:45:36～37）。来源为A工程任务`01a086de-c5a0-7ee2-b46c-c0bd5b6d3dfd`的原始工具调用`call_K0jeiq5JCSmfHLLh3fJ3qsB7`及返回，未重跑失败实验。原日志本身不含shell命令，以下依据调用记录补录。

cwd：`%USERPROFILE%\.codex\visualizations\2026\09\09\01a086de-c5a0-7ee2-b46c-c0bd5b6d3dfd\h3-closeout-0918`。`%USERPROFILE%`是A的私有Windows用户目录；准确展开值不进入Git。

原PowerShell命令（换行仅为排版）：

```powershell
$d='task-packages/PKG-B-ALG/tasks/h3-complete-20260918/evidence/run05'
if (Test-Path -LiteralPath $d) { throw 'run05 already exists' }
New-Item -ItemType Directory -Path $d | Out-Null
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s task-packages/PKG-B-ALG/tasks/h3-complete-20260918/tests -k test_gap_enters_automatic_control -v 2>&1 | Tee-Object -FilePath "$d/first-failure.raw.log"
"EXIT_CODE=$LASTEXITCODE"
```

实际Python进程退出码 **1**；调用返回中明确打印`EXIT_CODE=1`。外层PowerShell记录命令正常完成、工具报告退出码 **0**，不可把外层0说成测试通过。原输出是cwd下`$d/first-failure.raw.log`，后迁至本页登记的仓库外私有目录；950字节与SHA-256身份不变。首错为新增测试在修复前实现上`StopIteration`，运行1项、`FAILED (errors=1)`；当时有新增未提交测试，不能声称只检出最终7a17edd即可重现首错。

## 第二副本及访问控制

| 项目 | 状态 |
| --- | --- |
| 首份原件 | 已核实位置、950字节、准确SHA-256和只读属性 |
| 第二个原字节副本 | NOT_ARCHIVED：未登记或验证位置/介质/哈希/恢复读取；脱敏件不计第二原件 |
| 访问控制 | NOT_VERIFIED：未核验ACL或建立可取回受控制品授权；“私下向A索取”不是已实施的访问控制证据 |
| B取回与收件核对 | NOT_RECEIVED |

本轮按“纯文档补充”范围未创建备份、调整ACL或搬迁原件。归档闭环尚需A保管第二个原字节副本，明确独立存放位置、访问授权和恢复读取结果，并核对同一950字节/SHA-256后补记；在此之前保持NOT_ARCHIVED。
