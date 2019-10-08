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
- pragma-no-mutate


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


pragma-no-mutate
................
**TODO**
not documented because a new better interceptor will be available soon.


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
