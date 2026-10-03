# Source review records

Scope: new fixed-angle wrapper and standalone XDC; approved motor_drive v2 unchanged.

Architect froze static signed-parameter clamps, one-shot command, startup16 edges, first-frame reset target and second-frame selected target. CDC/timing reviewer independently inspected the actual new files after the product writer released its batch.

Reviewed product SHA256:

- top: 072bbe373c302cb410fe6120c8c2cb43027f5f5d4f018ff7c704d85c0b367677
- XDC: b6626652e028f12969046e4c9f5c8263dd9783996826fab125df17c4193e58e7

CDC_STRUCTURE and constraint-source inspection: no source-level blocker found. One sys_clk domain, static commands, no generated clocks or crossings. Valid sampled once on edge17. Edge16 registers release startup reset, edge17 uses old commanded RESET for first pulse while capturing target. PWM-port false path only; no internal timing or reset path exception. No ASYNC_REG falsely applied to startup delay chain.

Evidence boundary: synthesis, recovery/removal, STA, physical pulse integrity and BOARD are unverified/not run. This source review is AI specialist evidence, not A's member approval.

Tool discovery: XSim2025.2 installed. Initial xvlog help attempt exited1 silently because PROCESSOR_ARCHITECTURE was absent; vendor loader was inspected, and process-local AMD64 restored the known Windows host architecture. Version/help then executed. No persistent environment change. Tool-help .pb files were moved from repository root into tool-help/ without deleting evidence.
