"""Regression checks for release archive boundaries and honest verification scope."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_verifier", ROOT / "scripts/verify-release.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReleaseVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "candidate.zip"
        self.payload = b"approved runtime bytes"
        self.row = {"path": "main.py", "bytes": len(self.payload),
                    "sha256": hashlib.sha256(self.payload).hexdigest()}
        self.manifest = {"source_commit": "1" * 40, "version": "1.0.0-rc.1",
                         "physical_device": "DEVICE-UNVERIFIED", "catalogue": {}, "files": [self.row]}

    def archive(self, entries=None, manifest=None):
        manifest_bytes = json.dumps(manifest or self.manifest).encode()
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("Nevermore/RELEASE_MANIFEST.json", manifest_bytes)
            for name, payload in entries or [("Nevermore/main.py", self.payload)]:
                archive.writestr(name, payload)
        return {"source_commit": "1" * 40, "sha256": VERIFY.digest_archive(self.path),
                "bytes": self.path.stat().st_size,
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "files": [self.row]}

    def test_valid_archive_is_verified_without_extraction(self):
        artifact = self.archive()
        result = VERIFY.verify_archive(self.path, artifact, {})
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_mutated_payload_is_rejected_even_with_current_archive_hash(self):
        artifact = self.archive([("Nevermore/main.py", b"corrupt runtime bytes")])
        with self.assertRaisesRegex(VERIFY.VerificationError, "Payload"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_extra_file_cannot_hide_outside_manifest(self):
        artifact = self.archive([("Nevermore/main.py", self.payload), ("Nevermore/.env", b"secret")])
        with self.assertRaisesRegex(VERIFY.VerificationError, "Unexpected/missing"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_duplicate_archive_entries_are_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            artifact = self.archive([("Nevermore/main.py", self.payload)] * 2)
        with self.assertRaisesRegex(VERIFY.VerificationError, "Duplicate ZIP"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_symlink_archive_entry_is_rejected(self):
        link = zipfile.ZipInfo("Nevermore/main.py")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        artifact = self.archive([(link, self.payload)])
        with self.assertRaisesRegex(VERIFY.VerificationError, "Indirect ZIP"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_manifest_revision_cannot_replace_pinned_revision(self):
        artifact = self.archive(manifest={**self.manifest, "source_commit": "2" * 40})
        with self.assertRaisesRegex(VERIFY.VerificationError, "source revision"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_wrong_archive_hash_is_rejected_first(self):
        artifact = self.archive()
        artifact["sha256"] = "0" * 64
        with self.assertRaisesRegex(VERIFY.VerificationError, "Archive SHA-256"):
            VERIFY.verify_archive(self.path, artifact, {})

    def test_windows_and_posix_traversal_paths_are_rejected(self):
        for path in ("../secret", "/absolute", "C:/secret", "a\\..\\secret", "a/../secret", "a//b", "./a"):
            with self.subTest(path=path), self.assertRaises(VERIFY.VerificationError):
                VERIFY.safe_relative(path)

    def test_duplicate_manifest_paths_are_rejected(self):
        with self.assertRaisesRegex(VERIFY.VerificationError, "Duplicate"):
            VERIFY.rows_by_path([self.row, self.row], "test")

    def test_optimized_python_does_not_disable_checks(self):
        # Production validation deliberately uses explicit errors, never Python assert.
        import subprocess
        import sys
        code = ("import runpy; m=runpy.run_path(" + repr(str(ROOT / "scripts/verify-release.py"))
                + "); m['safe_relative']('../escape')")
        result = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Unsafe relative path", result.stderr)


if __name__ == "__main__":
    unittest.main()
