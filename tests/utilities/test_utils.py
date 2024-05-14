import functools
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time
import unittest
import constants

from utilities.utils import run_in_subprocess
from utilities import utils


class TestUtils(unittest.TestCase):
    def test_run_in_subprocess(self):
        def test_func(a: int, b: int):
            return a + b

        partial = functools.partial(test_func, 1, 2)

        result = run_in_subprocess(func=partial, ttl=5)
        self.assertEqual(3, result)

    def test_run_in_subprocess_timeout(self):
        def test_func(a: int, b: int):
            time.sleep(3)
            return a + b

        partial = functools.partial(test_func, 1, 2)

        with self.assertRaises(TimeoutError):
            result = run_in_subprocess(func=partial, ttl=1)

    def test_run_in_subprocess_no_return(self):
        def test_func(a: int, b: int):
            pass

        partial = functools.partial(test_func, 1, 2)

        result = run_in_subprocess(func=partial, ttl=5)
        self.assertIsNone(result)

    def test_run_in_subprocess_tuple_return(self):
        def test_func(a: int, b: int):
            return a, b

        partial = functools.partial(test_func, 1, 2)

        result = run_in_subprocess(func=partial, ttl=5)
        self.assertEqual((1, 2), result)

    def test_run_in_subprocess_exception(self):
        def test_func(a: int, b: int):
            raise ValueError()

        partial = functools.partial(test_func, 1, 2)

        with self.assertRaises(ValueError):
            result = run_in_subprocess(func=partial, ttl=5)

    def test_validate_hf_repo_id_too_long(self):
        with self.assertRaises(ValueError) as ve:
            # Max allowed length is 41 characters
            utils.validate_hf_repo_id("my-org/" + "a" * 40)

        self.assertRegex(
            str(ve.exception),
            "Hugging Face repo id must be between 3 and 41 characters",
        )

    def test_validate_hf_repo_id_incorrect_format(self):
        with self.assertRaises(ValueError) as ve:
            utils.validate_hf_repo_id("my-repo-name-without-a-namespace")

        self.assertRegex(
            str(ve.exception), "must be in the format <org or user name>/<repo_name>"
        )

    def test_validate_hf_repo_id_valid(self):
        namespace, name = utils.validate_hf_repo_id("my-org/my-repo-name")
        self.assertEqual("my-org", namespace)
        self.assertEqual("my-repo-name", name)

    def test_save_and_load_version(self):
        version = constants.__spec_version__
        with NamedTemporaryFile() as f:
            self.assertIsNone(utils.get_version(f.name))

            utils.save_version(f.name, version)
            self.assertEqual(utils.get_version(f.name), version)

    def test_move_if_exists_does_not_move_dst_exists(self):
        with NamedTemporaryFile(mode="w+") as f:
            f.write("test")
            f.flush()

            with NamedTemporaryFile() as f2:
                # Destination file exists. Should not move.
                self.assertFalse(utils.move_file_if_exists(f.name, f2.name))
                self.assertEqual(b"", f2.read())
                f.seek(0)
                self.assertEqual(f.read(), "test")

    def test_move_if_exists_does_not_move_src_missing(self):
        with NamedTemporaryFile(mode="w+") as f:
            f.write("test")
            f.flush()

            self.assertFalse(utils.move_file_if_exists("no_file", f.name))

    def test_move_if_exists(self):
        with TemporaryDirectory() as d:
            with open(os.path.join(d, "src"), "w") as f:
                f.write("test")
                f.flush()

                dst = os.path.join(d, "dst")

                self.assertTrue(utils.move_file_if_exists(f.name, dst))
                self.assertFalse(os.path.exists(f.name))
                self.assertTrue(os.path.exists(dst))
                self.assertEqual(open(dst, "rb").read(), b"test")


if __name__ == "__main__":
    unittest.main()
