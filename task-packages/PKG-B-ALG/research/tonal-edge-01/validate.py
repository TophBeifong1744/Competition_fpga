"""Run prior package regression and bounded diagnosis tests in one suite."""
import io,json,platform,sys,unittest
from pathlib import Path
import study as d

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(d.ROOT/'payload/tb/python'))
    import test_study
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_study))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    out=d.HERE/'tests'
    if out.exists():raise ValueError('output exists')
    out.mkdir();(out/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    report=dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,python=platform.python_version(),numpy=d.np.__version__,
        source_sha256={n:d.s.entry.sha256(d.HERE/n) for n in ['study.py','test_study.py','validate.py']},
        prior_sources_sha256={p.relative_to(d.ROOT).as_posix():d.s.entry.sha256(p) for p in sorted((d.ROOT/'payload').rglob('*.py'))})
    d.s.entry.write_json(out/'validation.json',report)
    print(report['status'],result.testsRun,'tests')
    if not result.wasSuccessful():print(stream.getvalue());sys.exit(1)
