# B Spec review — S1

Reviewed SHA: `8f708e42caf32c1de6f30726298e3edf0e1970b6`; base `02b578c730c539e7fb45e11386567f28ffe7ab71`.

Conclusion: **PASS, limited implementation/history/diagnostic archival scope**. No blocking finding within REVIEW.md's application. This does not approve the historical build/load gate or physical identity.

Read REVIEW.md first, delivery-01/README.md second; inspected proposed-src/continuous/{continuous_core.c,main_continuous.c,scene_store.c,scene_store.h}, POLICY.json, check_scene.py, verify_delivery.py, final UART, build-result.json and archived model tests/result. Independently executed:

```
C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -B F:/NUEC/review-evidence/s1-8f708e4/spec/inspect_artifacts.py
```

Final exit 0; results in artifact-result.json. First reviewer helper execution failed with KeyError 'now_us': the reused ELF parser exposes only global symbols. The reviewer helper was corrected to scan the symbol table for the local function; no author files changed. This was a reviewer-script failure, not an artifact defect. No ARM build, full historical gate or board action occurred.

## Findings and boundaries

1. Archive capacity is 300000 groups / 9600000 bytes, with 64-byte leading/trailing guards. Captured 288250 groups / 9224000 bytes leaves 11750 groups / 376000 bytes. scene_append checks guards and remaining capacity before memcpy, increments saved count only after the copy, and rechecks guards. Exact capacity is permitted; another packet rejects. This is a finite buffer with fail-stop behavior, not indefinite storage.
2. continuous_core only acquires completed DMA slots, validates a packet, calls archive storage while CPU_OWNED, then frees the slot. The alternate slot can be DMA_OWNED during CPU copy; same-slot reuse is refused. Copy/guard failure retains the owner and triggers the failure path. No successful partial-record substitution occurs.
3. prepare flushes and invalidates the full aligned 8064-byte slot before DMA; acquire invalidates only after completion. CPU-only archive is never the DMA target. After drain and CPU readback validation, main flushes the entire archive before READY_FOR_DDR_DUMP. Source-level ownership/cache reasoning supports this one archived run; cache hardware behavior was not independently exercised.
4. ELF independent parsing confirms both 16-word continuous and 11-word scene contracts, timer function's 333333343 divisor literal, scene_archive at 0x00112A80, data at 0x00112AC0, allocation 9600128 bytes, program end 0x00A400C0, and all LOAD/allocated sections inside program DDR below RX 0x01000000. This includes heap/stack. ELF hash matches the declared post-build report.
5. All 10 archived source hashes match build-result.json. The earlier host model's seven source/test hashes still match; its 16 reused and eight S1 scenarios are reused historical evidence, **not rerun by this reviewer**. Those cases include exact capacity, guard failure, preserved failure prefix, slow-copy overflow and DMA timeout. No need to rerun unchanged E1/DDR/RTL as part of this increment.
6. **Final post-build object is not archived in this package.** The only `.obj` is command-order-fix-01/before-fix/app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj, SHA256 3fd07ea3b80a955c660291e4a38fbee2ca022bb10088f725dedea487ba4bc150. It differs from post-build object SHA 0cb797800bb2f9791d35fa4c81bd995db6696513b0540d959c2e5e2614cabdc2. Thus the post-build object check is author-record evidence, not independently reproduced object inspection. Final ELF inspection is independent. This limitation does not block the requested archive/diagnostic scope, but must not be inflated into full build reproduction.
7. UART records one START, one successful stop/drain, FREE/FREE slots and archive integrity/readiness. Its build/date/profile/memory outputs align with archived ELF/source/report. Disk/UART agreement does not prove device JTAG identity. No full download/readback transcript is present; REVIEW and HANDOFF explicitly preserve this boundary.
8. Historical check_scene depends on pinned timerfixed-entry checker hashes. No dependency was substituted, no historical gate was run, and no safety approval is inferred from its report. The final user input's mic0 +X ~5cm and approximate phase boundaries remain diagnostic labels, not far-field truth or exact acoustic events.

No production input, author manifest, acquisition data or baseline evidence was altered. Main reviewer handles independent PCM/format statistics and publication checks separately.
