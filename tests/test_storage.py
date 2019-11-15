import os
import time

from requre.constants import VERSION_REQURE_FILE
from requre.exceptions import PersistentStorageException
from requre.helpers.simple_object import Simple
from requre.storage import (
    DataMiner,
    DataTypes,
    StorageKeysInspectDefault,
    StorageKeysInspectSimple,
    StorageKeysInspect,
    PersistentObjectStorage,
)
from requre.utils import StorageMode
from tests.testbase import BaseClass


class Base(BaseClass):
    keys = ["a", "b"]

    def setUp(self) -> None:
        super().setUp()
        PersistentObjectStorage().dump_after_store = False

    def store_keys_example(self):
        PersistentObjectStorage().store(self.keys, values="c", metadata={})
        PersistentObjectStorage().store(self.keys, values="d", metadata={})

    def test_simple(self):
        self.store_keys_example()
        self.assertEqual("c", PersistentObjectStorage()[self.keys])
        self.assertEqual("d", PersistentObjectStorage()[self.keys])

    def test_exception(self):
        self.test_simple()
        self.assertRaises(
            PersistentStorageException, PersistentObjectStorage().read, self.keys
        )

    def test_write(self):
        self.store_keys_example()
        self.assertFalse(os.path.exists(self.response_file))
        PersistentObjectStorage().dump()
        self.assertTrue(os.path.exists(self.response_file))


class Versioning(BaseClass):
    def setUp(self) -> None:
        super().setUp()
        PersistentObjectStorage().dump_after_store = False

    def test_no_version(self):
        """
        Check if storage is able to read and write version to persistent storage file
        """
        self.assertEqual({}, PersistentObjectStorage().metadata)
        self.assertEqual(0, PersistentObjectStorage().storage_file_version)
        self.assertEqual(
            None,
            PersistentObjectStorage().metadata.get(
                PersistentObjectStorage().version_key
            ),
        )
        self.assertFalse(os.path.exists(self.response_file))

    def test_no_version_after_dump(self):
        PersistentObjectStorage().dump()
        PersistentObjectStorage().storage_object = {}
        self.assertEqual({}, PersistentObjectStorage().metadata)
        self.assertEqual(0, PersistentObjectStorage().storage_file_version)

    def test_current_version(self):
        PersistentObjectStorage().dump()
        self.assertTrue(os.path.exists(self.response_file))
        self.assertEqual(
            VERSION_REQURE_FILE, PersistentObjectStorage().storage_file_version
        )
        self.assertNotEqual({}, PersistentObjectStorage().metadata)

    def test_current_version_after_load(self):
        PersistentObjectStorage().dump()
        PersistentObjectStorage().load()
        self.assertEqual(
            VERSION_REQURE_FILE, PersistentObjectStorage().storage_file_version
        )
        self.assertNotEqual({}, PersistentObjectStorage().metadata)
        self.assertIn("version_storage_file", PersistentObjectStorage().metadata)


class TestStoreTypes(BaseClass):
    keys = ["a", "b"]

    def tearDown(self):
        DataMiner().data_type = DataTypes.List

    def test_default(self):
        self.assertEqual(DataTypes.List, DataMiner().data_type)

    def test_list_data(self):
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(PersistentObjectStorage().storage_object["a"]["b"]))
        self.assertEqual("x", PersistentObjectStorage()[self.keys])
        self.assertEqual(1, len(PersistentObjectStorage().storage_object["a"]["b"]))
        self.assertEqual("y", PersistentObjectStorage()[self.keys])
        self.assertEqual(0, len(PersistentObjectStorage().storage_object["a"]["b"]))

    def test_value_data(self):
        DataMiner().data_type = DataTypes.Value
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})
        self.assertEqual(2, len(PersistentObjectStorage().storage_object["a"]["b"]))
        self.assertEqual("y", PersistentObjectStorage()[self.keys])
        self.assertEqual(2, len(PersistentObjectStorage().storage_object["a"]["b"]))
        self.assertEqual("y", PersistentObjectStorage()[self.keys])
        self.assertEqual(2, len(PersistentObjectStorage().storage_object["a"]["b"]))

    def test_dict_data(self):
        DataMiner().data_type = DataTypes.Dict
        DataMiner().key = "first-key"
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        DataMiner().key = "second-key"
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})

        self.assertIn("first-key", PersistentObjectStorage().storage_object["a"]["b"])
        self.assertIn("second-key", PersistentObjectStorage().storage_object["a"]["b"])

        self.assertEqual("y", PersistentObjectStorage()[self.keys])
        DataMiner().key = "first-key"
        self.assertEqual("x", PersistentObjectStorage()[self.keys])


class Metadata(BaseClass):
    keys = ["a", "b"]

    @staticmethod
    @Simple.decorator_plain
    def simple_return(value):
        return value

    def setUp(self):
        super().setUp()
        DataMiner().current_time = time.time()

    def test_latency(self):
        delta = 0.05

        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        self.assertAlmostEqual(
            0, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # Try to set some custom metadata
        DataMiner().data.metadata = {"random": "data"}

        time.sleep(0.1)
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.1, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time.sleep(0.2)
        PersistentObjectStorage().store(keys=self.keys, values="z", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        self.assertIn(self.keys, PersistentObjectStorage())
        self.assertAlmostEqual(
            0, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # check custom metadata
        self.assertEqual("data", DataMiner().metadata["random"])

        self.assertIn(self.keys, PersistentObjectStorage())
        self.assertAlmostEqual(
            0.1, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )
        # check if custom metadata are not everywhere
        self.assertNotIn("random", DataMiner().metadata)
        self.assertIn("latency", DataMiner().metadata)
        self.assertIn(self.keys, PersistentObjectStorage())
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

    def test_generic(self):
        PersistentObjectStorage().store(
            keys=self.keys, values="x", metadata={"test_meta": "yes"}
        )
        PersistentObjectStorage().metadata = {"rpms": ["package1", "package2"]}
        PersistentObjectStorage().dump()
        PersistentObjectStorage().storage_object = {}
        PersistentObjectStorage().load()
        self.assertIn(self.keys, PersistentObjectStorage())
        self.assertEqual(DataMiner().metadata["test_meta"], "yes")
        self.assertEqual(
            PersistentObjectStorage().metadata.get(
                PersistentObjectStorage().key_inspect_strategy_key
            ),
            StorageKeysInspectDefault.__name__,
        )
        self.assertEqual(
            PersistentObjectStorage().metadata.get("rpms"), ["package1", "package2"]
        )

    def test_strategy(self):
        DataMiner().key_stategy_cls = StorageKeysInspectSimple
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        self.simple_return("ahoj")
        self.simple_return([1, 2, 3])

        PersistentObjectStorage().dump()
        PersistentObjectStorage().storage_object = {}
        DataMiner().key_stategy_cls = StorageKeysInspectDefault
        PersistentObjectStorage().mode = StorageMode.read
        PersistentObjectStorage().load()
        self.assertEqual("x", PersistentObjectStorage()[self.keys])
        self.assertEqual(
            PersistentObjectStorage().metadata.get(
                PersistentObjectStorage().key_inspect_strategy_key
            ),
            StorageKeysInspectSimple.__name__,
        )
        self.assertEqual(StorageKeysInspectSimple, DataMiner().key_stategy_cls)

    def test_strategy_proper(self):
        self.test_strategy()
        PersistentObjectStorage().load()
        print(PersistentObjectStorage().storage_object)
        self.assertEqual("ahoj", self.simple_return("nonsense"))
        self.assertEqual([1, 2, 3], self.simple_return("nonsense"))

    def test_strategy_API_cls(self):
        self.test_strategy()
        PersistentObjectStorage().load()
        DataMiner().key_stategy_cls = StorageKeysInspect
        self.assertRaises(NotImplementedError, self.simple_return, "nonsense")

    def test_strategy_default_cls(self):
        self.test_strategy()
        PersistentObjectStorage().load()
        DataMiner().key_stategy_cls = StorageKeysInspectDefault
        self.assertRaises(PersistentStorageException, self.simple_return, "nonsense")


class Latency(BaseClass):
    keys = ["a", "b"]

    def setUp(self):
        super().setUp()
        DataMiner().current_time = time.time()
        DataMiner().use_latency = True

    def tearDown(self):
        DataMiner().use_latency = False

    def test_not_applied(self):
        DataMiner().use_latency = False
        delta = 0.05
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time_begin = time.time()
        self.assertIn(self.keys, PersistentObjectStorage())
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        self.assertIn(self.keys, PersistentObjectStorage())
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

    def test_applied(self):
        delta = 0.05
        PersistentObjectStorage().store(keys=self.keys, values="x", metadata={})
        time.sleep(0.2)
        PersistentObjectStorage().store(keys=self.keys, values="y", metadata={})
        self.assertAlmostEqual(
            0.2, DataMiner().metadata[DataMiner.LATENCY_KEY], delta=delta
        )

        time_begin = time.time()
        self.assertIn(self.keys, PersistentObjectStorage())
        time_end = time.time()
        self.assertAlmostEqual(0, time_end - time_begin, delta=delta)

        time_begin = time.time()
        self.assertIn(self.keys, PersistentObjectStorage())
        time_end = time.time()
        self.assertAlmostEqual(0.2, time_end - time_begin, delta=delta)
