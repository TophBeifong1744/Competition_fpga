# 本批原始记录目录

目前没有新的实板录音；本文件只建立目录并规定命名。

| 采集 | BIN | 完整串口 | XSDB 导出/暂停记录 |
| --- | --- | --- | --- |
| P0 局部激励 | map-p0.bin | map-p0.log | map-p0-xsdb.log |
| P1 局部激励 | map-p1.bin | map-p1.log | map-p1-xsdb.log |
| P2 局部激励 | map-p2.bin | map-p2.log | map-p2-xsdb.log |
| P3 局部激励 | map-p3.bin | map-p3.log | map-p3-xsdb.log |
| 后续安静复录 | quiet-repeat-01.bin | quiet-repeat-01.log | quiet-repeat-01-xsdb.log |

各轮 Vitis 加载过程可保存在 launch-sequence.log，保留时间，轮次对应另写 run-record.md。
每个成功 BIN 预期 1024000 字节；最终仍需匹配该轮完整串口 FNV/ID，不以大小独立判通过。

- 一轮 Run 对应一组文件；先导出保存，再启动下一轮。
- 不向 raw/ 内放合成数据或从首批复制的数据冒充本轮结果。
- 不编辑原始日志内容、重编号、去直流、过滤或补样。
- 同名文件存在时换新后缀，例如 map-p1-r02.bin / .log；失败材料保留。
- 对应 H1 输出以后生成在本批 captures/ 的新 acquisition_id 目录，不覆盖本目录原件或首批材料。

