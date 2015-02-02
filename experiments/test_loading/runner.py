import importlib
import runpy
import tempfile
import unittest


with tempfile.NamedTemporaryFile() as f:
    f.write('def func(): return True\n')
    f.close()
    mod = runpy.run_path(f.name)
    print(mod)

suite = unittest.TestLoader().discover('tests')
result = unittest.TestResult()
suite.run(result)
print(result)
