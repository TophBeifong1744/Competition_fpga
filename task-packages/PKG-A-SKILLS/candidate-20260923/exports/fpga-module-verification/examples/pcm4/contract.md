# Existing module contract and provenance

Uses the bundled unmodified `pcm4_signext_pack.v` from the project's
`rtl/acquisition/pcm4_signext_pack.v`, attributed to member C's C-RTL-003
delivery. The approved baseline Git blob at `a7e1ea976da91ba735af5c0a79fffdc7d10c121f`
is `a300f74c48fe68eb34247d7a6f1cf97a28778f58`; the exported Windows checkout
file SHA-256 is recorded in the candidate manifest. Line-ending conversion does
not change the HDL text. The source is distributed under the repository MIT
license in `license.txt`; retain member C attribution. This TB is a Skill-use
example, not a repeated request for C acceptance or a microphone/room simulation.

Pure combinational logic; no clock/reset/ready/valid. SAMPLE_WIDTH supports 2..32. Four signed inputs independently sign-extend to four 32-bit words, mic0 in bits31:0 and mic3 in127:96. All two's-complement bit patterns legal. No rounding, sample-numbering or synchronization claim.

TB interprets values through a signed 64-bit integer, compares each resulting 32-bit word with case inequality, covers width2/24/32, extrema and 64 deterministic patterns (seed0x76543210). 66 groups x4 words x3 widths = 792 comparisons. This is HDL code-pattern simulation, not four-microphone acoustic simulation, FPGA synthesis, board or system acceptance.

The case references the adjacent exported source and therefore runs without the
parent repository. The maintained production copy remains in the project; this
exported file is a version-bound example input rather than a second development
location.
