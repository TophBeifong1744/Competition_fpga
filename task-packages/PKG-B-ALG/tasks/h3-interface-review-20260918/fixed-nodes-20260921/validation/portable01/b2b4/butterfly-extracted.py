tr = rne_shift(wr * br - wi * bi, TWIDDLE_FRAC)
ti = rne_shift(wr * bi + wi * br, TWIDDLE_FRAC)
candidates = ((ar + tr, ai + ti), (ar - tr, ai - ti))
