import random
import numpy as np
from xxhash import xxh64_digest

__all__ = ["CuckooFilter"]


class _CuckooTable:
    __slots__ = ("size", "bucket")

    def __init__(self, size=4):
        self.size = size
        self.bucket = np.array((), dtype=np.ulonglong)

    def insert(self, item_fingerprint):
        s = self.bucket.size
        if s < self.size:
            self.bucket.resize(s + 1)
            self.bucket.put(s, item_fingerprint)
            return True
        return False

    def remove(self, item_fingerprint):
        if item_fingerprint not in self.bucket:
            return False

        self.bucket = np.delete(
            self.bucket, np.argwhere(self.bucket == item_fingerprint)
        )
        return True

    def swap_fingerprints(self, item_fingerprint):
        r = random.randrange(0, self.size)
        item_fingerprint, self.bucket[r] = self.bucket[r], item_fingerprint
        return item_fingerprint

    def __contains__(self, item_fingerprint):
        if item_fingerprint in self.bucket:
            return True
        return False


class CuckooFilter:
    def __init__(
        self, filter_capacity, num_swaps=500, bucket_size=4,
    ):

        self._filter_capacity = filter_capacity
        self._bucket_size = bucket_size
        self._num_swaps = num_swaps
        self._cur_size = 0
        self.table = [_CuckooTable(size=bucket_size) for _ in range(filter_capacity)]

    def obtain_index_from_hash(self, string_item):
        hash_value = xxh64_digest(string_item)
        index = int.from_bytes(hash_value, byteorder="big")
        index = index % self._filter_capacity
        return index

    def get_indices_and_finger(self, string_item):
        hash_value = xxh64_digest(string_item)
        index_1 = int.from_bytes(hash_value, byteorder="big") % self._filter_capacity
        int_finger = int.from_bytes(hash_value, byteorder="big")
        index_2 = (
            index_1 ^ self.obtain_index_from_hash(hash_value)
        ) % self._filter_capacity
        return index_1, index_2, int_finger

    def add(self, item_to_insert):
        if not isinstance(item_to_insert, str):
            raise TypeError("Expected a string, got a %s" % type(item_to_insert))

        index_1, index_2, finger = self.get_indices_and_finger(item_to_insert)
        if self.table[index_1].insert(finger):
            self._cur_size += 1
            return index_1

        if self.table[index_2].insert(finger):
            self._cur_size += 1
            return index_2

        random_index = random.choice((index_1, index_2))

        for swap in range(self._num_swaps):
            finger = self.table[random_index].swap_fingerprints(finger)

            random_index = random_index ^ self.obtain_index_from_hash(finger)
            random_index = random_index % self._filter_capacity

            if self.table[random_index].insert(finger):
                self._cur_size += 1
                return random_index

        raise RuntimeError("We're full")

    def remove(self, item_to_remove):
        index_1, index_2, finger = self.get_indices_and_finger(item_to_remove)

        if self.table[index_1].remove(finger):
            self._cur_size -= 1
            return True

        if self.table[index_2].remove(finger):
            self.cuckoo_size -= 1
            return True

        return False

    def __contains__(self, item_to_test):
        index_1, index_2, finger = self.get_indices_and_finger(item_to_test)
        return finger in self.table[index_1] or finger in self.table[index_2]

    def get_load(self):
        return self._cur_size / (self._filter_capacity * self._bucket_size)
