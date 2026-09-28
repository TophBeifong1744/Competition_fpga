# D14-02有限机械检查

`check_contract.py`只运行固定的合成文稿探针，不接受生产配置、不发布身份，也不是生产encoder或完整准入validator。`result.json`绑定实际schema/checker字节摘要；82项通过仅为`FINITE_DOCUMENT_PROBES_PASS_NOT_PRODUCTION`。

消除的不确定性：JSON Schema 2020-12自身合法性；三个合成容器结构；必需字段、类型、未知字段、非零摘要、ref种类、mic顺序、规范整数串；B原反例的两个准确摘要及解析后相同字节；键序、数组顺序、ASCII转义、重复解码键/BOM/非ASCII/非法scalar拒绝。另明确展示未约分有理数会通过结构schema而被gcd关系拒绝，避免把schema通过当作完整语义通过。

所有合成坐标、参数及重复字符摘要都只是负载探针，未解析真实外部引用，没有可下发生产hash。完整几何关系、跨根身份一致性、递归引用/无环检查及生产生成器均未实现或验证。I14-TOKEN-01仅静态核对，没有编译/运行C反例；无RTL/EDA/ARM/板测。

依赖：Python 3.14，`jsonschema==4.25.1`。本次将依赖装在ignored的`codex_out/i14-review-fix-20260924-01/validator-deps`，没有改全局Python环境。依赖已可导入时可省略`--validator-deps`；脚本不联网或安装依赖。

从仓库根复核（新结果写ignored目录，不覆盖交审原件）：

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/identity-contract-checks-20260924/check_contract.py --validator-deps codex_out/i14-review-fix-20260924-01/validator-deps --out codex_out/i14-review-fix-recheck/result.json
```

B原发现：[PR #30固定ec5017d的NEEDS_FIX](https://github.com/TophBeifong1744/Competition_fpga/pull/30#issuecomment-5810446729)。本检查由A制作，作者机械检查不替代B成员复核，也不重新运行旧FFT/录音/耐久测试。
