import operator
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from itertools import takewhile
from json import loads, JSONDecodeError, dumps
import time

from ellipticcurve.ecdsa import Ecdsa
from ellipticcurve.publicKey import PublicKey
from ellipticcurve.utils.compatibility import toBytes


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
        # self.data_root = OrderedDict()

    def __setitem__(self, key, value):
        try:
            value_json = loads(value)
            prefix = next(iter(value_json))
            # New registration for a product
            if prefix == "newId":
                if value_json["newId"] in self.data:
                    # print(self.data)
                    print("ID already exists!")
                    pass
                else:
                    # Create and use set to prevent duplicates - add time so we can do conflict resolution
                    # key -> (time_created, list_of_events)
                    # Also add artificial delay to prevent race conditions - we keep this small for now to prove the point
                    time.sleep(0.01)
                    creation_time = time.time()
                    self.data[key] = (creation_time, "{}", "{}")
                    # self.data_root[key] = (creation_time, "{}")

            # Append new events and root to existing record
            elif prefix == "id":
                # extract from the tuple
                creation_time_data, data_tup, root_tup = self.data[key]

                data_json = loads(data_tup)
                data_json[time.time()] = value_json["data"]
                data = dumps(data_json)
                self.data[key] = (creation_time_data, data)

                # See if the user has inserted a "root" field
                try:
                    value_json["root"]
                    data_root_json = loads(root_tup)
                    data_root_json[time.time()] = value_json["root"]
                    root_data = dumps(data_root_json)
                    self.data[key] = (creation_time_data, data, root_data)
                
                # If they haven't - put the previous data back in its place 
                except KeyError:
                    self.data[key] = (creation_time_data, data, root_tup)

            # New Registration for an actor (represented by a public key)
            elif prefix == "newPub":
                if value_json["newPub"] in self.data:
                    print("Public key already registered")
                else:
                    new_pub_key = value_json["pub_key"]
                    try:
                        # Check if the key is actually valid
                        _ = PublicKey.fromString(toBytes(new_pub_key))
                    # We are being a bit lazy here - but starkbank has a "strange" exception we cannot define   
                    except:
                        print("Public Key is not valid!")
                        # Do not proceed after this point
                        return
                    
                    user = value_json["user"]
                    creation_time = time.time()
                    self.data[new_pub_key] = (creation_time, user)
            
        except JSONDecodeError:
            print("Not Valid JSON!")
            pass

        self.cull()

    # Our DHT must remain immutable, therefore we remove this function
    def cull(self):
        # for _, _ in self.iter_older_than(self.ttl):
        #     self.data.popitem(last=False)
        pass

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
