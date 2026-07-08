from uuid import uuid4
import json
from kademlia.storage import ForgetfulStorage


class ForgetfulStorageTest:
    def test_storing(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        assert storage["one"] == "two"

    def test_forgetting(self):
        storage = ForgetfulStorage(0)
        storage["one"] = "two"
        assert storage.get("one") is None

    def test_iter(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        for key, value in storage:
            assert key == "one"
            assert value == "two"

    def test_iter_old(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        for key, value in storage.iter_older_than(0):
            assert key == "one"
            assert value == "two"


# My custom tests

def test_register():
    storage = ForgetfulStorage()
    newId = uuid4().hex
    newRegister = {"newId": newId}
    storage.__setitem__(newId, json.dumps(newRegister))
    print(storage.get(newId))

    # Now set the same ID again - this time it should return an error
    storage[newId] = json.dumps(newRegister)

    # Print all entries in our storage
    for i in storage:
        print(i)

        
def test_append_data():
    storage = ForgetfulStorage()
    newId = uuid4().hex
    newRegister = {"newId": newId}
    storage.__setitem__(newId, json.dumps(newRegister))
    
    data = {"abc": 123, "foo": "bar"}
    new_event = {"id": newId, "data": json.dumps(data), "root": "0xabc"}
    storage.__setitem__(newId, json.dumps(new_event))

    # Append more data
    data_2 = {"abc": 456, "foo": "baz"}
    new_event_2 = {"id": newId, "data": json.dumps(data_2)}
    storage.__setitem__(newId, json.dumps(new_event_2))
    print(storage.data.values()) 
    # for i in storage:
    #     print(f"Storage: {i}")

    # print(f"Root: {storage.data_root}")
        
if __name__ == "__main__":
    test_register()
    # test_append_data()
    