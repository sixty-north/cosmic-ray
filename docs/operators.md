# Mutation Operators

**TODO:** Update this to reflect the changes that occurred during celery
  development.

In Cosmic Ray we use *mutation operators* to implement the various
forms of mutation that we support. For each specific kind of mutation
– constant replacement, break/continue swaps, and so forth – there is
an operator class that knows how to create that mutation from
un-mutated code.

## Implementation details

Cosmic Ray uses abstract syntax tree (AST) modification to implement
mutation. This means that we first compile the original source code
into an AST and then make changes to copies of that AST. The modified ASTs are
inserted into the module tables `sys.modules` so that they can be
tested. We use the standard library's `ast` module to work with the
ASTs.

Each operator is ultimately a subclass of
`cosmic_ray.operators.operator.Operator` which is itself a subclass of
`ast.NodeTransformer`. `NodeTransformer` is used to traverse and
modify ASTs, so our operators work by hooking into the
`NodeTransformer` protocol to add and remove nodes from the AST. When
an operator visits a potential mutation site (i.e. a node that it
knows how to mutate) it informs the `Operator` machinery which in turn
decides if the mutation should be supplied.

An operator always operates on a copy of the original AST. In this way
we ensure that no mutation interferes with any other mutation. This is
critical because we need to avoid a) misattributing test results and
b) missing survivors due to interacting/interfering mutations.

## Implementing an operator

To implement a new operator you need to create a subclass of
`cosmic_ray.operators.operator.Operator`. This, again, is a subclass of
`ast.NodeTransformer`. The `NodeTransformer` class provides a number of
`visit_*` functions which are called during AST traversal as different types of
nodes are visited. Examples include `visit_Num` which is called when a `Number`
node is visitied, or `visit_UnaryOp` which is called when a unary operator is
visited. Your operator class should override the `visit_*` functions that it
needs in order to determine when it can apply its mutation. In any of these
functions, if your operator can perform a mutation it should call
`Operator.visit_mutation_site()`.

Your operator class should also implement `Operator.mutate()`. This is
the function that actually mutates the AST by adding or removing
nodes. This method will only over be called with nodes for which your
operator called `visit_mutation_site()` during traversal. In other
words, Cosmic Ray splits mutation into two phases:

1. Detecting where a mutation might potentially be applied
2. Applying the mutation

Your operator needs to implement both of these behaviors, and the
mutation machinery will take care of calling them at the right time.

### Operators are provided as plugins

Cosmic Ray is designed to be extended with arbitrary operators
provided by users. It dynamically discovers operators at runtime using
the `stevedore` plugin system which relies on the `setuptools`
`entry_points` concept. To make a new plugin available to Cosmic Ray
you need to create a `cosmic_ray.operator` entry point; this is
generally done in `setup.py`. We'll show an example of how to do this
later.

## A full example: `NumberReplacer`

One of the operators bundled with Cosmic Ray is
`cosmic_ray.operators.number_replacer.NumberReplacer`. This operator
looks for `Num` nodes (number literals in source code) and replaces
them with new `Num` nodes that have a different numeric value. To
demonstrate how to create a mutation operator, we'll step through how
to create that operator in a new package called `example`.

### Creating the operator class

The initial layout for our package is like this:
```
setup.py
example/
  __init__.py
```

`__init__.py` is empty and `setup.py` has very minimal content:
```
from setuptools import setup

setup(
    name='example',
    version='0.1.0',
)
```

The first thing we need to do is create a new Python source file to hold our new
operator. Create a file named `number_replacer.py` in the `example` directory.
It has the following contents:

```
import ast

from cosmic_ray.operators.operator import Operator


class NumberReplacer(Operator):
    def visit_Num(self, node):
        return self.visit_mutation_site(node)

    def mutate(self, node):
        new_node = ast.Num(n=node.n + 1)
        return new_node
```

Let's step through this line-by-line. We first import `ast` because we'll need
to create new `ast.Num` nodes later and we need access to its constructor.

```
import ast
```

Next we import the `Operator` base class.

```
from cosmic_ray.operators.operator import Operator
```

We define our new operator by creating a subclass of `Operator` called
`NumberReplacer`:
```
class NumberReplacer(Operator):
```

In order to do its job, `NumberReplacer` needs to detect when AST traversal
reaches `Num` nodes. To do this, it implements `ast.NodeTransformer.visit_Num()`
which is called when `Num` nodes are visited. Since our operator can mutate
*any* `Num` node, it implements this method by simply calling
`visit_mutation_site()`; remember that this informs the rest of the mutation
machinery that its possible to perform a mutation at this node:

```
    def visit_Num(self, node):
        return self.visit_mutation_site(node)
```

Finally we implement `Operator.mutate()` which is called to actually
perform the mutation. `mutate()` should return one of:

* `None` if the `node` argument should be removed from the AST, or
* a new `ast.Node` instance to replace the original one

In this case, simply create a new `Num` node with a new value and return it:

```
    def mutate(self, node):
        new_node = ast.Num(n=node.n + 1)
        return new_node
```

That's all there is to it. This mutation operator is now ready to be applied to
any code you want to test.

However, before it can really be used you need to make it available as a plugin.

### Creating the plugin

In order to make your operator available to Cosmic Ray as a plugin,
you need to define a new `cosmic_ray.operators` entry point. This is
generally done through `setup.py`, which is what we'll do here.

Modify `setup.py` with a new `entry_points` argument to `setup()`:
```
setup(
    . . .
    entry_points={
	    'cosmic_ray.operator': [
	        'example_number_replacer = example.number_replacer:NumberReplacer'
	    ]
	})
```


Now when Cosmic Ray queries the `cosmic_ray.operator` entry point it
will see your operator along with all of the others.
