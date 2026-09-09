import io,platform,unittest
import run_study as s
import test_features

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(s.ROOT/'payload/tb/python'))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_features))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    out=s.HERE/'tests'
    if out.exists():raise ValueError('output exists')
    out.mkdir();(out/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    s.s.entry.write_json(out/'validation.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,python=platform.python_version(),numpy=s.np.__version__,
        source_sha256={n:s.s.entry.sha256(s.HERE/n) for n in ['features.py','run_study.py','test_features.py','validate.py']}))
    print('PASS' if result.wasSuccessful() else stream.getvalue(),result.testsRun)
    if not result.wasSuccessful():raise SystemExit(1)
