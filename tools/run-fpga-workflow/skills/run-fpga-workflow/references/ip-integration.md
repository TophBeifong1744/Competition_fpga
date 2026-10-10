# Official vendor IP integration

Read this reference only when adding, regenerating, upgrading, copying, or
repairing vendor IP, or when IP output products, models, or constraints cannot
be reproduced.

## Ownership

`fpga_engineer` in `IP_INTEGRATION` mode is the only default writer of
versioned IP configuration and official regeneration recipes.
`fpga_vendor_platform_reviewer` independently checks identity, tool/target,
contracts, generated products, and reopen evidence. Neither role may invent an
approximate primitive or IP model.

## Fast decision order

1. Reuse a project-managed official IP when identity, status, ports,
   parameters, latency/reset semantics, and target match.
2. If only output products are missing, regenerate them incrementally with the
   current confirmed tool.
3. For copied or legacy configurations, inspect source-view and output-product
   ownership. Stage/import under the current project output or recreate with
   the local official tool; never generate into another checkout.
4. For a new IP with a confirmed official Tcl/CLI recipe, use batch generation.
5. If current vendor/version parameters or commands cannot be proven from
   official documentation or local Help, automate the official GUI once,
   export the configuration/recipe, and use the recipe thereafter.

Internet research supplies version-matched manuals, parameter semantics,
commands, examples, and known limitations. It does not supply a product XCI,
IDF, or IPC to copy directly into the design.

## Evidence depth

### IP_DISCOVERY

- confirm vendor/tool/version/part;
- locate official managed objects/configuration;
- compare module/entity, ports, widths, parameters, and required behavior;
- decide reuse, regenerate, upgrade, recreate, or GUI-once.

### IP_PREPARE

- create/customize through the official local tool;
- materialize XCI/IDF/IPC or vendor-equivalent managed configuration;
- save a versioned official regeneration recipe when supported;
- generate only the products needed for integration.

### IP_INTEGRATION_ACCEPTANCE

- clean regeneration when required;
- unique official identity and status;
- tool/version/part and source-view owner;
- port/width/parameter contract;
- latency, reset, busy, and FIFO/RAM mode;
- output products and OOC synthesis where applicable;
- IP constraints and processing scope;
- simulation model/library plus exported defines/includes;
- canonical project close/reopen with the IP still managed;
- explicit upgrade delta.

## Vendor boundary

- Xilinx/Vivado: prefer installed Catalog Tcl (`create_ip`, confirmed CONFIG,
  `generate_target`, IP run/status, and tool-exported IP Tcl).
- Pango/PDS: use the current-version official IPC/IP Generator, IDF, and an
  exported recipe when proven; do not invent a Vivado-like CLI.
- Anlogic/TD: use the current-version official IP Generator,
  IPC/RTL/constraint outputs, and exported flow Tcl when proven.

GUI automation is a one-time fallback, not the steady-state build flow.
