import operator
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from itertools import takewhile
from json import loads, JSONDecodeError
import time

class IStorage(ABC):
    """
    Local storage for this node.
    IStorage implementations of get must return the same type as put in by set
    """

    @abstractmethod
    def __setitem__(self, key, value):
        """
        Set a key to the given value.
        """

    @abstractmethod
    def __getitem__(self, key):
        """
        Get the given key.  If item doesn't exist, raises C{KeyError}
        """

    @abstractmethod
    def get(self, key, default=None):
        """
        Get given key.  If not found, return default.
        """

    @abstractmethod
    def iter_older_than(self, seconds_old):
        """
        Return the an iterator over (key, value) tuples for items older
        than the given secondsOld.
        """

    @abstractmethod
    def __iter__(self):
        """
        Get the iterator for this storage, should yield tuple of (key, value)
        """


class ForgetfulStorage(IStorage):
    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl
        # Store our merkle root for individual profiles - use Orderedict since we are using this already
        self.data_root = OrderedDict()

    def __setitem__(self, key, value):
        # This implementation by default overwrites existing entries
        # if key in self.data:
        #     del self.data[key]
        # self.data[key] = (time.monotonic(), value)

        try:
            value_json = loads(value)
            prefix = next(iter(value_json)) 
            if prefix == "newId":
                if value_json["newId"] in self.data:
                    print("ID already exists!")
                    pass
                else:
                    # Create and use set to prevent duplicates - add time so we can do conflict resolution
                    # key -> (time_created, list_of_events)
                    # Also add artificial delay to prevent race conditions - we keep this small for now to prove the point
                    time.sleep(0.01)
                    self.data[key] = (time.monotonic(), set())
                    self.data_root[key] = (time.monotonic(), set())

            # Append new events and root to existing record
            elif prefix == "id":
                self.data[key][1].add(value_json["data"])
                self.data_root[key][1].add(value_json["root"])

        except JSONDecodeError:
            print("Not Valid JSON!")
            pass

        self.cull()

    def cull(self):
        for _, _ in self.iter_older_than(self.ttl):
            self.data.popitem(last=False)

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def iter_older_than(self, seconds_old):
        min_birthday = time.monotonic() - seconds_old
        zipped = self._triple_iter()
        matches = takewhile(lambda r: min_birthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _triple_iter(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)

    def __iter__(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
