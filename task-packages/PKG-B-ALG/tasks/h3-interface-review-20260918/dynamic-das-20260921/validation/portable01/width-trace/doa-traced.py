def doa_q20(pair_lags: list[dict], pair_deltas=PAIR_DELTAS) -> dict:
    """Solve the fixed-point 2-D least-squares direction vector.

    Production calls use the frozen six square-array baselines.  The optional
    geometry argument exists so the checker can exercise the rank-deficient
    failure branch, which is structurally unreachable after selecting any
    three distinct baselines from the frozen square geometry.
    """
    if len(pair_lags) != len(pair_deltas):
        raise ValueError('one geometry row is required for every pair lag')
    valid = checked('valid', [(pair_deltas[k], int(row['tau_q12'])) for k, row in enumerate(pair_lags) if row.get('valid')])
    if len(valid) < 3:
        return {'valid': False, 'reason': 'INSUFFICIENT_PAIRS', 'valid_pairs': len(valid)}
    sxx = checked('sxx', sum((dx * dx for (dx, _), _tau in valid)))
    syy = checked('syy', sum((dy * dy for (_, dy), _tau in valid)))
    sxy = checked('sxy', sum((dx * dy for (dx, dy), _tau in valid)))
    bx = checked('bx', sum((dx * tau for (dx, _), tau in valid)))
    by = checked('by', sum((dy * tau for (_, dy), tau in valid)))
    determinant = checked('determinant', sxx * syy - sxy * sxy)
    if determinant == 0:
        return {'valid': False, 'reason': 'RANK_DEFICIENT', 'valid_pairs': len(valid)}
    ux = checked('ux', rne_div((syy * bx - sxy * by) * 343 * (1 << FRAC_DIR - FRAC_LAG), determinant * 1920))
    uy = checked('uy', rne_div((sxx * by - sxy * bx) * 343 * (1 << FRAC_DIR - FRAC_LAG), determinant * 1920))
    residual_sq = checked('residual_sq', 0)
    for (dx, dy), tau in valid:
        predicted = checked('predicted', rne_div((dx * ux + dy * uy) * 1920 * (1 << FRAC_LAG), 343 * (1 << FRAC_DIR)))
        residual_sq += (predicted - tau) ** 2
        checked('residual_sq', residual_sq)
    norm_sq = checked('norm_sq', ux * ux + uy * uy)
    residual_ok = checked('residual_ok', residual_sq <= len(valid) * (1 << FRAC_LAG - 1) ** 2)
    norm_ok = checked('norm_ok', round(0.1 * (1 << FRAC_DIR)) ** 2 <= norm_sq <= round(1.3 * (1 << FRAC_DIR)) ** 2)
    accepted = checked('accepted', residual_ok and norm_ok)
    return {'valid': accepted, 'reason': 'VALID' if accepted else 'GEOMETRY_REJECT', 'valid_pairs': len(valid), 'ux_q20': ux, 'uy_q20': uy, 'residual_sum_square_q24': residual_sq, 'norm_square_q40': norm_sq, 'azimuth_q8_deg': atan2_q8(uy, ux) if ux or uy else None}