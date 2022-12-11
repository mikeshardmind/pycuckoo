# pycuckoo

Code based on https://www.cs.cmu.edu/~dga/papers/cuckoo-conext2014.pdf

Insertion time is still a little slower than I'd like,
and memory consumption is slightly higher than I'd like as well,
but it's good enough for my own use for now.

Hash function of choice here is xxhash.

Provides a single class `CuckooFilter` Membership uses python `in`.

The public interface is typed.

Versioning: calver, no guarantees against breaking changes, but unlikely to be needed.
