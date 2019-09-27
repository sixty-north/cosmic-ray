Interceptors
============

In Cosmic Ray we use *Interceptors* to change the list of planified works.

Interceptor can be activated in your config file with:

::

 [cosmic-ray.interceptors]
 enabled = ['spor', 'operators-filter']



Actually, available intercaptors are:

- spor
- operators-filters


spor
----
**TODO**


operators-filter
----------------

This interceptor allows to filter out operators according to their names.
You need to configure in your config file the list of operators to filter out
as list of regex like that:

::

 [cosmic-ray.operators-filter]
 exclude-operators = [
   "core/ReplaceComparisonOperator_Is(Not)?_(Not)?(Eq|[LG]tE?)",
   "core/ReplaceComparisonOperator_(Not)?(Eq|[LG]tE?)_Is(Not)?",
   "core/ReplaceComparisonOperator_[LG]tE_Eq",
   "core/ReplaceComparisonOperator_[LG]t_NotEq",
 ]

The list of all available operators can be show by running
-``cosmic-ray init`` with INFO debug level

::

 cosmic-ray init -v INFO your_session_file.db


The list are displayed in a condensed form like that:

::

 019-09-27 16:28:52,808 root INFO Operators available:
 2019-09-27 16:28:52,808 root INFO  - core: AddNot, ReplaceTrueWithFalse, ReplaceFalseWithTrue, ...
 2019-09-27 16:28:52,809 root INFO  - core: ReplaceBinaryOperator - Add_Sub, Add_Mul, Add_Div, ...
 ...

That's means that followed operators are available:

::

 core/AddNot
 core/ReplaceTrueWithFalse
 core/ReplaceFalseWithTrue

 core/ReplaceBinaryOperator_Add_Sub
 core/ReplaceBinaryOperator_Add_Mul
 core/ReplaceBinaryOperator_Add_Div
 ...
