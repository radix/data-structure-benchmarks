import sys

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
    for i in xrange(size):
        l = l.concat(make_list(i))

def pyrsistent_vectors_append(size):
    l = v(0)
    for i in xrange(size):
        l = l.append(i)

def mutable_vectors_append(size):
    l = [0]
    for i in xrange(size):
        l.append(i)


# Pushing
def pysistence_vectors_push(size):
    l = make_list([0])
    for i in xrange(size):
        l = l.cons(i)

def pyrsistent_vectors_push(size):
    l = v(0)
    for i in xrange(size):
        l = v(i).extend(l)

def mutable_vectors_push(size):
    l = [0]
    for i in xrange(size):
        l.insert(0, i)


# modifying existing items

def pysistence_vectors_mutate(size):
    l = make_list(*range(size))
    for i in xrange(size):
        l = _pys_set(i, 'new-value', l)

def pyrsistent_vectors_mutate(size):
    l = v(*range(size))
    for i in xrange(size):
        l = l.assoc(i, 'new-value')


def mutable_vectors_mutate(size):
    l = range(size)[:] # copy the list just to be a little bit fair to how we construct the lists in other tests.
    for i in xrange(size):
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
    for i in xrange(n):
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


for size in sys.argv[1:]:
    size = int(size)
    for desc, func in [
        ("mutable vectors append", mutable_vectors_append),
        ("pyrsistent vectors append", pyrsistent_vectors_append),
        ("pysistence vectors append", pysistence_vectors_append),

        ("mutable vectors push", mutable_vectors_push),
        ("pyrsistent vectors push", pyrsistent_vectors_push),
        ("pysistence vectors push", pysistence_vectors_push),

        ("mutable vectors mutate", mutable_vectors_mutate),
        ("pyrsistent vectors mutate", pyrsistent_vectors_mutate),
        ("pysistence vectors mutate", pysistence_vectors_mutate),
        ]:
        print "{} (size {}): {}".format(desc, size, repeat(func, size))


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

