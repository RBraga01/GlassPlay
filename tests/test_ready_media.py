"""Approved bundle preparation verifies boundaries before writing any public file."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import zipfile

SPEC = importlib.util.spec_from_file_location("ready_media", Path(__file__).resolve().parents[1] / "scripts/ready-media.py")
READY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READY)


class ReadyMediaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "config").mkdir()
        (self.root / "docs/media").mkdir(parents=True)
        self.archive = self.root / "fixture.zip"
        self.payload = b"approved promotional video"
        self.row = {"path": "promo.mp4", "bytes": len(self.payload), "sha256": READY.sha(self.payload)}
        self.make_archive([("promo.mp4", self.payload)])

    def make_archive(self, entries):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, payload in entries:
                archive.writestr(name, payload)
        self.manifest = {"assets": [self.row], "bundle": {"sha256": READY.sha(self.archive.read_bytes()), "bytes": self.archive.stat().st_size}}
        self.policy = {"site": {"approved": False}, "application": {"approved": False}, "media": {
            "approved": True, "approval_reference": "owner/media-only", "manifest_sha256": None,
            "bundle_url": "https://example.com/media.zip", "bundle_sha256": self.manifest["bundle"]["sha256"]}}
        self.save()

    def save(self):
        payload = json.dumps(self.manifest).encode()
        (self.root / "docs/media/manifest.json").write_bytes(payload)
        self.policy["media"]["manifest_sha256"] = READY.sha(payload)
        (self.root / "config/publication.json").write_text(json.dumps(self.policy))

    def fetch(self, url, destination, count):
        shutil.copyfile(self.archive, destination)

    def test_media_only_approval_stages_exact_assets_without_public_output(self):
        destination, count, state = READY.prepare(self.root, self.fetch)
        self.assertEqual(count, 1)
        self.assertEqual(state, "downloaded_and_verified")
        self.assertEqual(destination.parent, self.root / ".private/approved-media")
        self.assertEqual((destination / "promo.mp4").read_bytes(), self.payload)
        self.assertFalse((self.root / "dist").exists())
        self.assertFalse((self.root / "public").exists())
        self.assertEqual(READY.prepare(self.root, lambda *_: self.fail("Verified cache must not download"))[2], "verified_cache")

    def test_approval_in_wrong_scope_never_fetches(self):
        self.policy["site"]["approved"] = True
        self.policy["media"]["approved"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "Promotional media approval"):
            READY.prepare(self.root, lambda *_: self.fail("Unapproved network request"))

    def test_manifest_hash_must_be_the_approved_exact_bytes(self):
        with (self.root / "docs/media/manifest.json").open("ab") as output:
            output.write(b"\n")
        with self.assertRaisesRegex(ValueError, "exact media manifest"):
            READY.prepare(self.root, self.fetch)

    def test_bundle_hash_mismatch_blocks_staging(self):
        with self.archive.open("r+b") as file:
            file.seek(0); file.write(b"XX")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            READY.prepare(self.root, self.fetch)

    def test_media_payload_hash_is_verified_after_archive_hash(self):
        self.make_archive([("promo.mp4", b"x" * len(self.payload))])
        with self.assertRaisesRegex(ValueError, "payload hash mismatch"):
            READY.prepare(self.root, self.fetch)

    def test_extra_and_traversal_zip_entries_are_rejected(self):
        for entry in ("secret.env", "../outside.mp4"):
            with self.subTest(entry=entry):
                self.make_archive([("promo.mp4", self.payload), (entry, b"private")])
                with self.assertRaisesRegex(ValueError, "unapproved files"):
                    READY.prepare(self.root, self.fetch)

    def test_symlink_zip_entry_is_rejected(self):
        link = zipfile.ZipInfo("promo.mp4")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make_archive([(link, self.payload)])
        with self.assertRaisesRegex(ValueError, "Indirect"):
            READY.prepare(self.root, self.fetch)

    def test_oversized_manifest_blocks_fetch(self):
        self.manifest["assets"][0]["bytes"] = 100 * 1024 * 1024
        self.save()
        with self.assertRaisesRegex(ValueError, "size/hash"):
            READY.prepare(self.root, lambda *_: self.fail("Oversized fetch"))

    def test_mutated_cache_is_rejected(self):
        destination, _, _ = READY.prepare(self.root, self.fetch)
        (destination / "promo.mp4").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "differs from approval"):
            READY.prepare(self.root, self.fetch)

    def test_unsafe_protocol_and_credentials_are_rejected(self):
        for value in ("file:///a.zip", "http://example.com/a.zip", "https://127.0.0.1/a.zip", "https://user:password@example.com/a.zip", "https://example.com/a.zip?token=secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                READY.public_https_url(value)

    def test_https_redirect_cannot_downgrade_to_http(self):
        class Opener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                raise HTTPError(request.full_url, 302, "redirect", {"Location": "http://example.com/unsafe.zip"}, None)
        opener = Opener()
        with patch.object(READY, "build_opener", return_value=opener), patch.object(READY.socket, "getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                READY.download("https://example.com/a.zip", self.root / "download.zip", 10)
        self.assertEqual(opener.calls, 1)


if __name__ == "__main__":
    unittest.main()
