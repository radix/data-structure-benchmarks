import sys

import six
from six.moves import range

import timeit

from pysistence import make_list
from pyrsistent import v, s

# Usability notes

# PYSISTENCE:
# - bugs:
#   - EmptyList doesn't support a bunch of operations (concat)
#   - they left a "print" statement in the implementation of "concat", annoying
# - missing functions:
#   - take(n) -> return first n elements
#   - drop(n) -> return all after first n elements
#   - insert(i, v) -> insert an element between others
#   - assoc(i, v) -> replace an element by index

# PYRSISTENT:
# - no insert, but they do have assoc.


# Appending
def pysistence_vectors_append(size):
    l = make_list(0)
    for i in range(size):
        l = l.concat(make_list(i))

def pyrsistent_vectors_append(size):
    l = v(0)
    for i in range(size):
        l = l.append(i)

def mutable_vectors_append(size):
    l = [0]
    for i in range(size):
        l.append(i)


# Pushing
def pysistence_vectors_push(size):
    l = make_list([0])
    for i in range(size):
        l = l.cons(i)

def pyrsistent_vectors_push(size):
    l = v(0)
    for i in range(size):
        l = v(i).extend(l)

def mutable_vectors_push(size):
    l = [0]
    for i in range(size):
        l.insert(0, i)


# modifying existing items

def pysistence_vectors_mutate(size):
    l = make_list(*range(size))
    for i in range(size):
        l = _pys_set(i, 'new-value', l)

def pyrsistent_vectors_mutate(size):
    l = v(*range(size))
    for i in range(size):
        l = l.assoc(i, 'new-value')


def mutable_vectors_mutate(size):
    l = list(range(size)) # copy the list just to be a little bit fair to how we construct the lists in other tests.
    for i in range(size):
        l[i] = 'new-value'


# Utilities

def _pys_take(n, l):
    result = []
    for i in range(n):
        result.append(l.first)
        l = l.rest
    return make_list(*result)

def _pys_drop(n, l):
    origl = l
    for i in range(n):
        l = l.rest
    return l

def _pys_insert(i, newv, l):
    if i == 0:
        return l.cons(newv)
    after = _pys_drop(i, l)
    if after is None:
        after = make_list()
    return _pys_take(i, l).concat(after.cons(newv))

def _pys_set(i, newv, l):
    after = _pys_drop(i + 1, l)
    if after is not None:
        new_and_after = after.cons(newv)
    else:
        new_and_after = make_list(newv)
    if i == 0:
        return new_and_after
    return _pys_take(i, l).concat(new_and_after)


# Benchmark

def repeat(f, vector_size):
    results = timeit.repeat(lambda: f(vector_size), number=1000, repeat=3)
    return sum(results) / len(results)


# library
MUTABLE = 'built-in mutable'
PYRSISTENT = 'pyrsistent'
PYSISTENCE = 'pysistence'

# operations
VECTOR_APPEND = 'vector append'
VECTOR_PUSH = 'vector push'
VECTOR_MUTATE = 'vector mutate'

benchmarks = [
    (MUTABLE, VECTOR_APPEND, mutable_vectors_append),
    (PYRSISTENT, VECTOR_APPEND, pyrsistent_vectors_append),
    (PYSISTENCE, VECTOR_APPEND, pysistence_vectors_append),

    (MUTABLE, VECTOR_PUSH, mutable_vectors_push),
    (PYRSISTENT, VECTOR_PUSH, pyrsistent_vectors_push),
    (PYSISTENCE, VECTOR_PUSH, pysistence_vectors_push),

    (MUTABLE, VECTOR_MUTATE, mutable_vectors_mutate),
    (PYRSISTENT, VECTOR_MUTATE, pyrsistent_vectors_mutate),
    (PYSISTENCE, VECTOR_MUTATE, pysistence_vectors_mutate),
]


for size in sys.argv[1:]:
    size = int(size)
    for lib, op, func in benchmarks:
        print("{} {} (size {}): {}".format(lib, op, size, repeat(func, size)))


# TODO:

# - the accumulation functions are a bit crappy, it'd probably be better to
#   just do one operation per vector of a particular size, and then graph
#   the performance of that operation over various sizes.
#   but maybe accumulation speed is also useful? JIT/cache performance may
#   differ.


# ANALYSIS OF RESULTS:

# PYSISTENCE
# - pysistence concat is extremely slow, because it's just a linked list,
#   meaning the list must be reversed and consed onto new part.
#   - pypy speeds it up QUITE a bit relative to CPython, but still very slow
# - getting the length of a pysistence list is very slow, because they do
#   not store the size of a list -- you must walk the list to find the length.
#   This could be fixed easily.
# - pysistence cons is extremely fast, because it's just a linked list.
#   It's even faster than mutable list inserting when *accumulating* lists
#   ~1000+ elements on my macbook. Another test would be to *start* with a big
#   list and just cons onto the head once, to see exactly at which size the
#   balance between insert(0) and cons() is tipped.


# PYRSISTENT
# - for some reason pushing to the front is WAY, WAY slower than appending.
#   probably worth filing a bug.

