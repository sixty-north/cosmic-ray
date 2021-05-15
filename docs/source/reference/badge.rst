=====
Badge
=====

Utility to generate badge useful to decorate your preferred
Continuous Integration system (github, gitlab, ...).
The badge indicate the percentage of failing migrations.

This utility is based on `anybadge <https://github.com/jongracecox/anybadge>`__.

Command
=======

::

 cr-badge [--config <config_file>]  <badge_file> <session-file>

Configuration
=============

::

 [cosmic-ray.badge]
 label = "mutation"
 format = "%.2f %%"

 [cosmic-ray.badge.thresholds]
 50  = 'red'
 70  = 'orange'
 100 = 'yellow'
 101 = 'green'
