# TF-B-02 独立需求轴复核

对象：17afe32cebcff742bb2f9486388e91d9403f83dd。仅参数解析与比较，无固件构建、链接、加载及硬件操作；作者文件未修改。

## 阻断：P2，-Wl 参数被误当作单一路径

需求：repair-01/README.md 第10行声称“只规范化编译器及已识别路径参数；保留选项、宏名/值和字符串大小写及分词语义”，第13行声明未知布局拒绝。

位置：command_contract.py 第52～53行把整个 `-Wl,` 后缀交给第33行的 `ntpath.normpath`，但 GCC 按逗号拆分并向链接器传递多个参数。

最小输入：归档链接命令中将 `-Wl,"F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/lscript.ld"` 改成 `-Wl,"F:/College/verilog_digital_system/Vitis/four_mic_continuous/src/lscript.ld,-L,/../lscript.ld"`。二者归一化完全相同，check_entry.py 第179～180行完整比较返回 ACCEPTED；实际多出 `-L /../lscript.ld`。真实主机 MinGW GCC `-###` 独立确认这一参数拆分，未运行编译器后端或链接器。

进一步在 `,-L,/../lscript.ld` 前分别插入 `,-e,0x01000000`、`,--defsym,REVIEW_MARKER=1`、`,--wrap=XAxiDma_SimpleTransfer`，三个完整比较均错误接受。ELF入口另有检查，不能把该结果说成无效入口已通过全部 gate；已证明的缺项是“额外实际链接参数必须拒绝”未满足。建议先解析 `-Wl,` 子参数，再仅规范化明确的路径操作数，未知复合布局拒绝。

证据：`check_arguments.py`、`run01/result.json`、`extra_link_flags.py`、`extra01/result.json`。

## 通过与边界

六组旧大小写/宏值/字符串分词负例均正确区分；四种普通额外链接参数均拒绝。10种引号/反斜杠示例与主机 MinGW GCC 8.1的只打印结果一致，见 `quotes02/result.json`；未冒称验证作者ARM GCC 13.3运行时。`quotes01`保留初次缺少输入夹具导致无法输出COLLECT_GCC_OPTIONS的尝试，不计通过证据；补充空文本夹具后复跑。无额外范围扩张。
