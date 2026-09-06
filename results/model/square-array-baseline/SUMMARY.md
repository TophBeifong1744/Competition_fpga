# Ideal square-array baseline

- Evidence class: analytic floating-point model; not measured data
- Git commit at run time: `ec55cdbcf0112a17b99172f15c6bb1bbde55f25c`
- Working tree at run time: `dirty`
- MATLAB: `25.2.0.2998904 (R2025b)`
- Reproduce: `matlab -batch "run('model/matlab/square_array_baseline.m')"`
- Geometry: four ideal omnidirectional microphones on a 40 mm square
- Sound speed: 343.0 m/s; sample rate: 48000 Hz

## Numeric checks

- Edge maximum delay: 5.598 samples; legal integer search bound: 6 samples
- Diagonal maximum delay: 7.916 samples; legal integer search bound: 8 samples
- One sample near broadside corresponds to about 10.29 deg
- A 5 deg change near broadside corresponds to 0.488 sample

## Ideal 90 deg interferer attenuation

| Frequency | Attenuation |
|---:|---:|
| 500 Hz | 0.293 dB |
| 1000 Hz | 1.193 dB |
| 2000 Hz | 5.152 dB |

These values apply only to the stated ideal narrowband geometry. They are not broadband speech improvement, room performance, or measured SNR.
