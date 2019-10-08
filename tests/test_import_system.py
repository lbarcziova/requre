import os
import sys
import unittest

from requre.helpers.tempfile import TempFile
from requre.import_system import ReplaceType, upgrade_import_system
from requre.utils import STORAGE

SELECTOR = os.path.basename(__file__).rsplit(".", 1)[0]


class TestUpgradeImportSystem(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        if "tempfile" in sys.modules:
            del sys.modules["tempfile"]
        super().tearDown()

    def testImport(self):
        """
        Test improving of import system with import statement
        Check also debug file output if it contains proper debug data
        """
        debug_file = "__modules.log"
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": "test_import_system"},
                {"mktemp": [ReplaceType.REPLACE, lambda: "a"]},
            )
        ]
        upgrade_import_system(filters=HANDLE_MODULE_LIST, debug_file=debug_file)
        import tempfile

        self.assertNotIn("/tmp", tempfile.mktemp())
        self.assertIn("a", tempfile.mktemp())
        with open(debug_file, "r") as fd:
            output = fd.read()
            self.assertIn(SELECTOR, output)
            self.assertIn("replacing mktemp by function", output)
        os.remove(debug_file)

    def testImportFrom(self):
        """
        Test if it able to patch also from statement
        """
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {"mktemp": [ReplaceType.REPLACE, lambda: "b"]},
            )
        ]
        upgrade_import_system(filters=HANDLE_MODULE_LIST)
        from tempfile import mktemp

        self.assertNotIn("/tmp", mktemp())
        self.assertIn("b", mktemp())

    def testImportDecorator(self):
        """
        Test patching by decorator_all_keys, not replacing whole function
        """
        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {
                    "mktemp": [
                        ReplaceType.DECORATOR,
                        lambda x: lambda: f"decorated {x()}",
                    ]
                },
            )
        ]
        upgrade_import_system(filters=HANDLE_MODULE_LIST)
        import tempfile

        self.assertIn("decorated", tempfile.mktemp())
        self.assertIn("/tmp", tempfile.mktemp())

    def testImportReplaceModule(self):
        """
        Test if it is able to replace whole module by own implemetation
        Test also own implementation of static tempfile module via class
        """

        HANDLE_MODULE_LIST = [
            (
                "^tempfile$",
                {"who_name": SELECTOR},
                {"": [ReplaceType.REPLACE_MODULE, TempFile]},
            )
        ]
        upgrade_import_system(filters=HANDLE_MODULE_LIST)
        import tempfile

        tmpfile = tempfile.mktemp()
        tmpdir = tempfile.mkdtemp()
        self.assertIn(
            f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp", tmpfile
        )
        self.assertIn(
            f"/tmp/{os.path.basename(STORAGE.storage_file)}/static_tmp", tmpdir
        )
        self.assertFalse(os.path.exists(tmpfile))
        self.assertTrue(os.path.exists(tmpdir))
        self.assertTrue(os.path.isdir(tmpdir))
        os.removedirs(tmpdir)
