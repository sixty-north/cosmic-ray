Mutation Operators
==================

In Cosmic Ray we use *mutation operators* to implement the various forms
of mutation that we support. For each specific kind of mutation –
constant replacement, break/continue swaps, and so forth – there is an
operator class that knows how to create that mutation from un-mutated
code.

Implementation details
----------------------

Cosmic Ray relies on `parso <https://github.com/davidhalter/parso>`_ to parse
Python code into trees. Cosmic Ray operators work directly on this tree, and the
results of modifying this tree are written to disk for each mutation.

Each operator is ultimately a subclass of
``cosmic_ray.operators.operator.Operator``. We pass operators to various
parse-tree *visitors* that let the operator view and modify the tree. When an
operator reports that it can potentially modify a part of the tree, Cosmic Ray
notes this and, later, asks the operator to actually perform this mutation.

Implementing an operator
------------------------

To implement a new operator you need to create a subclass of
``cosmic_ray.operators.operator.Operator``. The first method an operator must implement
is ``Operator.mutation_positions()`` which tells Cosmic Ray how the operator could mutate
a particular parse-tree node.

Second, an operator subclass must implement ``Operator.mutate()`` which actually mutates
a parse-tree node.

Finally, an operator must implement the class method ``Operator.examples()``.
This provides a set of before and after code snippets showing how the operator
works. These examples are used in the test suite and potentially for
documenation purposes. An operator can choose to provide no examples simply by
returning an empty iterable from ``examples``, though we may decide to check
for an absence of examples in the future. In any case, it's good form to provide
examples.

In both cases, the operator implementation works directly with the ``parso``
parse tree objects.

Operator provider plugins
-------------------------

Cosmic Ray is designed to be extended with arbitrary operators provided by
users. It dynamically discovers operators at runtime using the ``stevedore``
plugin system which relies on the ``setuptools`` ``entry_points`` concept.

Rather than having individual plugins for each operator, Cosmic Ray lets users
specify *operator provider* plugins. An operator provider can supply any number
of operators to Cosmic Ray. At a high level, Cosmic Ray finds all of the
operators available to it by iterating over the operator provider plugins, and
for each of those iterating over the operators that it exposes.

The operator provider API is very simple:

.. code-block:: python

    class OperatorProvider:
        def __iter__(self):
            "The sequence of operator names that this provider supplies"
            pass

        def __getitem__(self, name):
            "Get an operator class by name."
            pass

In other words, a provider must have a (locally) unique name for each operator
it provides, it must provide an iterator over those names, and it must allow
Cosmic Ray to look up operator classes by name.

To make a new operator provider available to Cosmic Ray you need to create a
``cosmic_ray.operator_providers`` entry point; this is generally done in
``setup.py``. We'll show an example of how to do this later.

Operator naming
~~~~~~~~~~~~~~~

All operators in Cosmic Ray have a unique name for any given session. The name
of an operator is based on two elements:

1. The name of the ``operator_provider`` entry point (i.e. as specified in
   ``setup.py``)
2. The name that the provider associates with the operator.

The full name of an operator is simply the provider's name and the operator's
name joined with "/". For example, if the provider's name was "widget_corp" and
the operator's name was "add_whitespace", the full name of the operator would be
"widget_corp/add_whitespace".

A full example: ``NumberReplacer``
----------------------------------

One of the operators bundled with Cosmic Ray is implemented with the clas
``cosmic_ray.operators.number_replacer.NumberReplacer``. This operator looks for
``Num`` nodes (number literals in source code) and replaces them with new
``Num`` nodes that have a different numeric value. To demonstrate how to create
a mutation operator and provider, we'll step through how to create that operator
in a new package called ``example``.

Creating the operator class
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial layout for our package is like this:

.. code-block:: text

    setup.py
    example/
      __init__.py

``__init__.py`` is empty and ``setup.py`` has very minimal content:

.. code-block:: python

    from setuptools import setup

    setup(
        name='example',
        version='0.1.0',
    )

The first thing we need to do is create a new Python source file to hold
our new operator. Create a file named ``number_replacer.py`` in the
``example`` directory. It has the following contents:

.. code-block:: python

    from cosmic_ray.operators.operator import Operator
    import parso

    class NumberReplacer(Operator):
        """An operator that modifies numeric constants."""

        def mutation_positions(self, node):
            if isinstance(node, parso.python.tree.Number):
                yield (node.start_pos, node.end_pos)

        def mutate(self, node, index):
            """Modify the numeric value on `node`."""

            assert isinstance(node, parso.python.tree.Number)

            val = eval(node.value) + 1
            return parso.python.tree.Number(' ' + str(val), node.start_pos)

Let's step through this line-by-line. We first import ``Operator`` because we need to inherit from it:

.. code-block:: python

    from cosmic_ray.operators.operator import Operator

We then import ``parso`` because we need to use it to create mutated nodes:

.. code-block:: python

    import parso

We define our new operator by creating a subclass of ``Operator`` called
``NumberReplacer``:

.. code-block:: python

    class NumberReplacer(Operator):

The ``mutate_positions`` method is called whenever Cosmic Ray needs to know if an operator can mutate a particular
node. We implement ours to report a single mutation at each "number":

.. code-block:: python

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.Number):
            yield (node.start_pos, node.end_pos)

Finally we implement ``Operator.mutate()`` which is called to actually
perform the mutation. ``mutate()`` should return one of:

-  ``None`` if the ``node`` argument should be removed from the tree, or
-  a new ``parso`` node to replace the original one

In this case, we simply create a new ``Number`` node with a new value and
return it:

.. code-block:: python

    def mutate(self, node, index):
        """Modify the numeric value on `node`."""

        assert isinstance(node, parso.python.tree.Number)

        val = eval(node.value) + 1
        return parso.python.tree.Number(' ' + str(val), node.start_pos)

That's all there is to it. This mutation operator is now ready to be
applied to any code you want to test.

However, before it can really be used, you need to make it available as
a plugin.

Creating the provider
~~~~~~~~~~~~~~~~~~~~~

In order to expose our operator to Cosmic Ray we need to create an operator
provider plugin. In the case of a single operator like ours, the provider
implementation is very simple. We'll put the implementation in
``example/provider.py``:

.. code-block:: python

    # example/provider.py

    from .number_replacer import NumberReplacer

    class Provider:
        _operators = {'number-replacer': NumberReplacer}

        def __iter__(self):
            return iter(Provider._operators)

        def __getitem__(self, name):
            return Provider._operators[name]

Creating the plugin
~~~~~~~~~~~~~~~~~~~

In order to make your operator available to Cosmic Ray as a plugin, you
need to define a new ``cosmic_ray.operator_providers`` entry point. This is
generally done through ``setup.py``, which is what we'll do here.

Modify ``setup.py`` with a new ``entry_points`` argument to ``setup()``:

.. code-block:: python

    setup(
        . . .
        entry_points={
            'cosmic_ray.operator_providers': [
                'example = example.provider:Provider'
            ]
        })

Now when Cosmic Ray queries the ``cosmic_ray.operator_providers`` entry point it
will see your provider - and hence your operator - along with all of the others.
