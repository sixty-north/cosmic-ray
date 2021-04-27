This is intended to be a very fast test suite. On some platform (e.g. Windows) we've found that test suites like this
can run faster than the resolution of the filesystem timestamps. This leads to problems where Python doesn't regenerate
pycs files when necessary, leading to incorrect mutation testing results. 

We've modified CR to work around these problems, and this test (as driven by the pytest suite) will hopefully detect
regressions in our workaround.