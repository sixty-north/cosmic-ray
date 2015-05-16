[![Build Status](https://travis-ci.org/sixty-north/cosmic-ray.png?branch=master)](https://travis-ci.org/sixty-north/cosmic-ray) [![Code Health](https://landscape.io/github/sixty-north/cosmic-ray/master/landscape.svg?style=flat)](https://landscape.io/github/sixty-north/cosmic-ray/master) [![Documentation](https://readthedocs.org/projects/cosmic-ray/badge/?version=latest)](http://cosmic-ray.readthedocs.org/en/latest/)

# Cosmic Ray: mutation testing for Python

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*  
*— The Fantastic Four*

Cosmic Ray is a tool for performing mutation testing on Python
code.

## N.B.! Cosmic Ray is still learning how to walk!

At this time Cosmic Ray is young and incomplete. It doesn't support
all of the mutations it should, its output format is crude, it only
supports one kind of test discovery, it may fall over on exotic
modules...[the list goes on and on](https://github.com/abingham/cosmic-ray/issues). Still,
for the adventurous it *does* work. Hopefully things will improve
fairly rapidly.

And, of course, patches and ideas are welcome.

## The short, short version

If you just want to get down to the business of finding and killing
mutants, here's what you do:

```
pip install cosmic_ray
cosmic-ray run my_module path/to/tests
```

This will print out a bunch of information about what Cosmic Ray is
doing, including stuff about what kinds of mutants are being created,
which were killed, and – chillingly – which survived.

**[Further documentation is available at readthedocs](http://cosmic-ray.readthedocs.org/en/latest/).**
