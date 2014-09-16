import sys

from functools import partial
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

# library
MUTABLE = 'built-in mutable'
PYRSISTENT = 'pyrsistent'
PYSISTENCE = 'pysistence'

# operations
VECTOR_APPEND = 'vector append'
VECTOR_PUSH = 'vector push'
VECTOR_MUTATE_BEG = 'vector mutate beginning'
VECTOR_MUTATE_MID = 'vector mutate middle'
VECTOR_MUTATE_END = 'vector mutate end'

def benchmarks(size):
    pys_list = make_list(*range(size))
    pyr_list = v(*range(size))
    mut_list = list(range(size))

    pys_vector_append = partial(pys_list.concat, make_list(1))
    pyr_vector_append = partial(pyr_list.append, 1)
    mut_vector_append = partial(mut_list.append, 1)

    mut_list = list(range(size))

    pys_vector_push = partial(pys_list.cons, 1)
    pyr_vector_push = partial(v(1).extend, pyr_list)
    mut_vector_push = partial(mut_list.insert, 0, 1)

    mut_list = list(range(size))

    pys_vector_mutate_beginning = partial(_pys_set, 0, 'new-value', pys_list)
    pyr_vector_mutate_beginning = partial(pyr_list.assoc, 0, 'new-value')
    mut_vector_mutate_beginning = partial(mut_list.__setitem__, 0, 'new-value')

    mut_list = list(range(size))

    middle_index = size // 2
    pys_vector_mutate_middle = partial(_pys_set, middle_index, 'new-value', pys_list)
    pyr_vector_mutate_middle = partial(pyr_list.assoc, middle_index, 'new-value')
    mut_vector_mutate_middle = partial(mut_list.__setitem__, middle_index, 'new-value')

    mut_list = list(range(size))

    pys_vector_mutate_end = partial(_pys_set, size-1, 'new-value', pys_list)
    pyr_vector_mutate_end = partial(pyr_list.assoc, size-1, 'new-value')
    mut_vector_mutate_end = partial(mut_list.__setitem__, size-1, 'new-value')

    benchmarks = [
        (MUTABLE, VECTOR_APPEND, mut_vector_append),
        (PYRSISTENT, VECTOR_APPEND, pyr_vector_append),
        (PYSISTENCE, VECTOR_APPEND, pys_vector_append),

        (MUTABLE, VECTOR_PUSH, mut_vector_push),
        (PYRSISTENT, VECTOR_PUSH, pyr_vector_push),
        (PYSISTENCE, VECTOR_PUSH, pys_vector_push),

        (MUTABLE, VECTOR_MUTATE_BEG, mut_vector_mutate_beginning),
        (PYRSISTENT, VECTOR_MUTATE_BEG, pyr_vector_mutate_beginning),
        (PYSISTENCE, VECTOR_MUTATE_BEG, pys_vector_mutate_beginning),

        (MUTABLE, VECTOR_MUTATE_MID, mut_vector_mutate_middle),
        (PYRSISTENT, VECTOR_MUTATE_MID, pyr_vector_mutate_middle),
        (PYSISTENCE, VECTOR_MUTATE_MID, pys_vector_mutate_middle),

        (MUTABLE, VECTOR_MUTATE_END, mut_vector_mutate_end),
        (PYRSISTENT, VECTOR_MUTATE_END, pyr_vector_mutate_end),
        (PYSISTENCE, VECTOR_MUTATE_END, pys_vector_mutate_end),
    ]
    return benchmarks


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

for size in sys.argv[1:]:
    size = int(size)
    print "==== data structure benchmarks ===="
    print
    print "initial structure size is {}".format(size)
    print "times are for 10k ops"
    print "mutable versions are left to grow between operations, so timings may be skewed."
    print
    for lib, op, func in benchmarks(size):
        result = timeit.timeit(func, number=10000)
        milliseconds = result * 1000
        print("{:<20} {:<25} {:>22.2f} milliseconds".format(lib, op, milliseconds))


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
# - pushing is much slower than appending, because it's really an append of
#   all elements onto a new list of length one.
# - mutating is pretty fast and constant across the board.
# - there is no insertion operation, so there's a ton of reallocation if you
#   want to put something at the beginning or middle. (this is same as the
#   issue with push)

## SUMMARY

# - of course, mutable vectors are pretty dang fast across the board, but the
#   one place where some persistent data structures (in this case, only
#   pysistence) wins is pushes onto the front.
# - However, if you're MOSTLY pushing onto the front, you're probably better
#   off just appending onto a different data structure (both mutable and
#   pyrsistent are faster at appending than pysistence is at pushing).

# - Apparently RRB-Trees and finger-trees are both better than all of these
#   things at insertion.
