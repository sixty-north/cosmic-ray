Interceptors
============

Usage
-----
In Cosmic Ray we use *Interceptors* to change the list of planified works.

Interceptor can be activated in your config file with:

::

 [cosmic-ray.interceptors]
 enabled = ['spor', 'operators-filter']



Actually, available interceptors are:

- spor
- operators-filter
- pragma


spor
....
**TODO**


operators-filter
................
This interceptor allows to filter out operators according to their names.
You need to configure in your config file the list of operators to filter out
as list of regex like that:

::

 [cosmic-ray.interceptors.operators-filter]
 exclude-operators = [
   "core/ReplaceComparisonOperator_Is(Not)?_(Not)?(Eq|[LG]tE?)",
   "core/ReplaceComparisonOperator_(Not)?(Eq|[LG]tE?)_Is(Not)?",
   "core/ReplaceComparisonOperator_[LG]tE_Eq",
   "core/ReplaceComparisonOperator_[LG]t_NotEq",
 ]

The list of all available operators can be show by running
-``cosmic-ray operators``


pragma
......

Skip all mutation:
    This interceptor filter mutation according to pragma annotation in your source
    comments.

    ::

     a = 1  # pragma: no mutate

    If this example, no mutation will be performed in this line.


Skip a specific mutation:
    You can filter specific mutation by specifing pragma category:

    ::

     a = b + 3  # pragma: no mutate: number-replacer

    Only `core/NumberReplacer` will be skipped, but all operators
    `core/ReplaceBinaryOperator_Add_*` will be apply.


Skip line marked as 'no coverage':
    Make mutation on uncoverable code have no meaning. Then if you set in your
    configuration file `filter-no-coverage` to true, all lines marked with
    `# pragma: no coverage` will be filtered too.

    ::

     [cosmic-ray.interceptors.pragma]
     filter-no-coverage = true


pragma syntax:
    - Any comment can be present before 'pragma:' declaration
    - You can have multiple pragma family separated with double space
      (allowing family name having multiple words)
    - You can declare sections of pragma if the pragma name is followed
      directly with ':'
    - Pragma family can have an empty section set if no section is declared
      after ':'  ex "fam:" or "fam1:  fam2
    - Section names can have a space (two spaces indicate the end
      of section list)
    - Sections are separated with ',', comma directly present after the
      previous section (no space)



Writing your own plugin
-----------------------
All Interceptors are classes based on `cosmic_ray.interceptors.base.Interceptor`


class Interceptor
.................
You can implement one or many of those methods:

- def set_config(self, config):

    Allow interceptors get some configurations

    `config`: Sub part [interceptors.<class-name without "Interceptor">]


- def pre_scan_module_path(self, module_path) -> bool:

    Called when we start exploring a new file.
    Can be useful to handle some caches.

    return True to allow this file exploration.


- def post_scan_module_path(self, module_path):

    Called when we end exploring a file.


- def pre_add_work_item(self, operator: Operator, node: Node, new_work_item: WorkItem) -> bool:

    Called when an operator have generate a work_item.
    This work_item is not in db yet.

    return True to allow this work item to be inserted in db.


- def post_add_work_item(self, operator: Operator, node: Node, new_work_item: WorkItem):

    Called when a work_item id insrted in db.
    Here, you can add a skipped result for this work item.


- def post_init(self):

    Called when the ent of init process.
    Here, you can do any job in the database.


deployement (setup.py)
......................
In your `setup.py`, you have to call `setup` with:

::

    setup(
        ...
        entry_points={
            'cosmic_ray.interceptors': [
                'name': my.interceptor.module:MyClassInterceptor',
            ]
        }
    )

Of course, you have to fill all other needed fields setup (see `setuptools` documentations).
