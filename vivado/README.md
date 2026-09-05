# Vivado 工程

本目录保存可复现工程所需的 Tcl、XDC、Block Design Tcl 和必要 IP 配置；本机生成的 `.xpr`、runs、cache、bitstream 和硬件导出文件不进入 Git。

预期入口：

```text
vivado/
  create_project.tcl   # 后续生成：从受控源码重建工程
  constraints/         # 板级与时序约束
  bd/                  # Block Design Tcl
  ip/                  # 必要且可审计的 IP 配置
  reports/             # 小型构建摘要模板
```

创建首个工程时，应把目标器件/板卡、Vivado 版本、顶层模块、源文件和约束全部写入脚本，并在干净目录验证可重建性。

