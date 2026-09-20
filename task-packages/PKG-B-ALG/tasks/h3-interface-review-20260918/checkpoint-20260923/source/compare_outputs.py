"""Field-semantic JSON comparison. Unlisted floats remain exact, never rounded."""
import math
import re
import numpy as np
from common import load, sha

# Explicit suffixes within the pinned report schema, not a blanket float tolerance.
# (absolute tolerance, relative tolerance); units documented in REPAIR-R1-R2.md.
RULES = [
    (r'/numeric_angle$', 1e-10, 0.),
    (r'/projection/advisory_azimuth_deg$', 1e-10, 0.),
    (r'/numeric/nominal_deviation_p(?:50|95)_deg$', 1e-10, 0.),
    (r'/projection/(?:projection_xy/\d+|projection_norm|residual_samples)$', 1e-12, 1e-12),
    (r'/features/(?:raw_rms|centered_rms)/\d+$', 1e-8, 1e-12),
    (r'/features/band_power/\d+$', 1e-6, 1e-12),
    (r'^/(?:noise_power_codes_squared|effective_on_power|effective_off_power)/\d+$', 1e-6, 1e-12),
    (r'/descriptive_audio/(?:single|manual|automatic)/(?:rms|peak|waveform_difference_rms)$', 1e-12, 1e-12),
    (r'/descriptive_audio/(?:single|manual|automatic)/output_level_change_db_vs_mic0$', 1e-10, 0.),
    (r'/files/\d+/(?:rms|peak_abs|max_quantization_error)$', 1e-12, 1e-12),
]
GOLDEN_RULES = [
    (r'^/reports/\d+/float_power/\d+$', 1e-6, 1e-12),
    (r'^/reports/\d+/relative_power_difference/\d+$', 1e-12, 1e-12),
]

def compare_json(a, b, *, golden=False):
    stats = dict(float_differences=0, max_absolute_difference=0., differences=[])
    def visit(x, y, path):
        def fail(reason):
            raise AssertionError(f'{path or "/"}: {reason}; expected={x!r}, actual={y!r}')
        if type(x) is not type(y): fail('type mismatch')
        if isinstance(x, dict):
            if x.keys() != y.keys(): fail('key mismatch')
            for k in x: visit(x[k], y[k], path+'/'+k)
        elif isinstance(x, list):
            if len(x) != len(y): fail('length mismatch')
            for i, (u,v) in enumerate(zip(x,y)): visit(u,v,path+'/'+str(i))
        elif isinstance(x, float):
            if not (math.isfinite(x) and math.isfinite(y)): fail('non-finite float')
            atol,rtol=next(((at,rt) for pattern,at,rt in (GOLDEN_RULES if golden else RULES)
                            if re.search(pattern,path)), (0.,0.))
            error=abs(x-y); limit=atol+rtol*abs(x)
            if error>limit: fail(f'float outside tolerance abs={error} limit={limit}')
            if x != y:
                stats['float_differences']+=1
                stats['max_absolute_difference']=max(stats['max_absolute_difference'],error)
                stats['differences'].append(dict(path=path,expected=x,actual=y,absolute_error=error,limit=limit))
        elif x != y: fail('discrete mismatch')
    visit(a,b,'')
    return stats

def compare_file(expected, actual, *, golden=False, environment=False):
    a,b=load(expected),load(actual)
    environments=None
    if environment:
        # Existing exclusion, only this explicit summary field; retained in report.
        environments=dict(expected=a.pop('environment'),actual=b.pop('environment'))
    result=compare_json(a,b,golden=golden)
    result.update(file=expected.name,expected_sha256=sha(expected),actual_sha256=sha(actual),
                  bytes_equal=sha(expected)==sha(actual),environments=environments)
    return result

def exact_file(a,b):
    if sha(a)!=sha(b): raise AssertionError(f'PCM/WAV byte mismatch: {a.name}; expected={sha(a)} actual={sha(b)}')

def exact_array(a,b,label):
    if a.dtype!=b.dtype or a.shape!=b.shape or a.dtype.kind not in 'iu' or not np.array_equal(a,b):
        raise AssertionError('integer array dtype/shape/code mismatch: '+label)
