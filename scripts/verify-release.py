"""Check committed release evidence; optionally verify private source/ZIP inputs.

No network access, extraction, publishing, or third-party packages are required.
An unavailable private input is reported NOT_RUN, never as an artifact PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile


RELEASE_METADATA = "releases/nevermore-rc2.json"
VERSION = "1.0.0-rc.2"
PAYLOAD_FILES = 98


class VerificationError(ValueError):
    """An integrity or release-policy invariant was violated."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def safe_relative(value):
    require(isinstance(value, str) and value, "Missing relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and "\\" not in value and ":" not in value
            and all(part not in {"", ".", ".."} for part in value.split("/")),
            f"Unsafe relative path: {value}")
    return path


def rows_by_path(rows, label):
    result = {}
    for row in rows:
        name = str(safe_relative(row["path"]))
        require(name not in result, f"Duplicate {label} path: {name}")
        require(isinstance(row["bytes"], int) and row["bytes"] >= 0,
                f"Invalid size: {name}")
        require(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
                f"Invalid SHA-256: {name}")
        result[name] = row
    return result


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_object(repo, revision, path):
    safe_relative(path)
    require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None,
            "Source revision must be a full immutable Git SHA")
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{revision}:{path}"])


def expected_catalogue(app):
    result = {}
    for name, prefix in (("trick_or_treat", "assets/trick_or_treat/"),
                         ("production", "assets/")):
        document = load_json(app / "assets" / name / "manifest.json")
        require(document["fps"] == 24 and document["resolution"] == [640, 640],
                f"Unsupported media format: {name}")
        for event, row in document["scenes"].items():
            require(event not in result, f"Duplicate event: {event}")
            result[event] = {"video": prefix + row["video"], "audio": prefix + row["audio"],
                             "frames": row["frame_count"], "fps": document["fps"]}
    return result


def verify_source(root, metadata, source_repo=None):
    folder = root / "experiences/nevermore"
    export = load_json(folder / "export-manifest.json")
    integration = metadata["source_integration"]
    require(export["source"]["commit"] == integration["commit"], "Export revision mismatch")
    require(export["status"] == "source_preview_only" and export["runnable"] is False
            and all(export[key] is False for key in
                    ("media_included", "framework_included", "voice_model_included")),
            "The curated export must remain a source preview")
    hashes = rows_by_path(integration["files"], "source")
    require(len(export["files"]) == len(hashes) == 23, "Expected 23 curated source files")
    expected = {"app/README.md"}
    for row in export["files"]:
        relative = str(safe_relative(row["path"]))
        require(relative.startswith("app/"), f"Source outside app: {relative}")
        path = folder / relative
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(folder.resolve()),
                f"Missing/indirect source: {relative}")
        payload = path.read_bytes()
        blob = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        require(len(payload) == row["bytes"] and blob == row["source_git_blob_sha"],
                f"Curated source differs from upstream Git bytes: {relative}")
        require(relative in hashes and sha256(payload) == hashes[relative]["sha256"]
                and len(payload) == hashes[relative]["bytes"], f"Source SHA-256 mismatch: {relative}")
        if source_repo is not None:
            require(payload == git_object(source_repo, integration["commit"], row["source_path"]),
                    f"Source differs from exact upstream commit: {relative}")
        expected.add(relative)
    actual = {p.relative_to(folder).as_posix() for p in (folder / "app").rglob("*")
              if p.is_file() and "__pycache__" not in p.parts}
    require(actual == expected, f"Unexpected/missing source paths: {sorted(actual ^ expected)}")
    return expected_catalogue(folder / "app")


def verify_metadata(metadata, catalogue, source_repo=None):
    require(metadata["schema_version"] == 1, "Unsupported metadata schema")
    require(metadata["version"] == VERSION, "Unexpected release version")
    require(metadata["publication"]["public_url"] is None
            and metadata["publication"]["authorized"] is False, "Candidate is not public")
    require(metadata["device_validation"]["physical_prism"] == "DEVICE-UNVERIFIED",
            "Physical device validation has no supporting evidence")
    require(metadata["rights"]["meshy"]["status"] == "USER-ATTESTED-MESHY-PAID-ACCOUNT"
            and metadata["rights"]["meshy"]["independently_verified"] is False,
            "Meshy must preserve the exact owner attestation status")
    require(metadata["rights"]["raven_framework"]["bundled"] is False
            and metadata["rights"]["raven_framework"].get("relicensed") is False,
            "Raven Framework must remain external and not relicensed")
    require(metadata["catalogue"] == catalogue and len(catalogue) == 20,
            "Release catalogue differs from approved source manifests")
    media = rows_by_path(metadata["runtime_files"], "runtime")
    required_media = {row[kind] for row in catalogue.values() for kind in ("video", "audio")}
    require(set(media) == required_media and len(media) == 34,
            "Runtime pins must cover exactly 17 unique video/audio pairs for 20 events")
    require(set(metadata["artifacts"]) == {"private_draft", "local_candidate"},
            "Both the original draft and refreshed candidate must be recorded")
    for artifact_id, artifact in metadata["artifacts"].items():
        require(artifact["public_url"] is None, f"Unapproved public artifact URL: {artifact_id}")
        require(re.fullmatch(r"[0-9a-f]{40}", artifact["source_commit"]) is not None,
                f"Invalid artifact revision: {artifact_id}")
        require(re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is not None
                and re.fullmatch(r"[0-9a-f]{64}", artifact["manifest_sha256"]) is not None,
                f"Invalid archive hash: {artifact_id}")
        files = rows_by_path(artifact["files"], f"{artifact_id} payload")
        require(len(files) == artifact["payload_files"] == PAYLOAD_FILES, "Unexpected payload count")
        require(set(metadata["package_source_paths"]) == set(files) - {".gitignore", ".gitattributes", "CREDITS.json"},
                "Every non-generated package payload needs an upstream source path")
        for source_path in metadata["package_source_paths"].values():
            safe_relative(source_path)
        require(set(media).issubset(files), f"Runtime missing from {artifact_id}")
        for path, pin in media.items():
            require(files[path] == pin, f"Runtime differs across candidates: {path}")
        required_docs = {"LICENSE", "ASSET_LICENSES.md", "RAVEN_FRAMEWORK.md", "RIGHTS.md",
                         "THIRD_PARTY_NOTICES.md", "CREDITS.json", "RELEASE_NOTES.md",
                         "docs/installation.md", "assets/voice/LICENSE-APACHE-2.0.txt"}
        require(required_docs.issubset(files), f"Missing release documentation: {artifact_id}")
        for name in files:
            path = PurePosixPath(name)
            require(path.suffix.lower() not in {".blend", ".fbx", ".glb", ".log", ".zip", ".env"}
                    and not any(p.lower() in {".git", "archive", "local-data", "__pycache__", "test-fixtures",
                                              "raven_framework", ".venv", ".env"} for p in path.parts),
                    f"Forbidden release payload: {name}")
    require(metadata["artifacts"]["local_candidate"]["source_commit"]
            == metadata["source_integration"]["commit"], "Local candidate must use the integrated revision")
    if source_repo is not None:
        revision = metadata["source_integration"]["commit"]
        for name, row in media.items():
            payload = git_object(source_repo, revision, name)
            if payload.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                require(f"oid sha256:{row['sha256']}\n".encode() in payload
                        and f"size {row['bytes']}\n".encode() in payload, f"Upstream LFS pin differs: {name}")
            else:
                require(sha256(payload) == row["sha256"] and len(payload) == row["bytes"],
                        f"Upstream runtime blob differs: {name}")
        attestation = json.loads(git_object(source_repo, revision, "assets/production/meshy-owner-attestation.json"))
        require(attestation == metadata["rights"]["meshy"], "Owner attestation differs from upstream")


def verify_archive(path, artifact, catalogue, source_repo=None, source_paths=None):
    require(path.is_file(), f"Archive unavailable: {path}")
    require(path.stat().st_size == artifact["bytes"], "Archive size mismatch")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    require(digest == artifact["sha256"], "Archive SHA-256 mismatch")
    pinned = rows_by_path(artifact["files"], "archive payload")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(set(names)) == len(names), "Duplicate ZIP entries")
        expected = {"Nevermore/" + name for name in pinned} | {"Nevermore/RELEASE_MANIFEST.json"}
        require(set(names) == expected, f"Unexpected/missing ZIP entries: {sorted(set(names) ^ expected)}")
        for info in infos:
            safe_relative(info.filename)
            require(not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16),
                    f"Indirect ZIP entry: {info.filename}")
            require(not info.flag_bits & 1, f"Encrypted ZIP entry: {info.filename}")
        manifest_bytes = archive.read("Nevermore/RELEASE_MANIFEST.json")
        require(sha256(manifest_bytes) == artifact["manifest_sha256"], "Release manifest hash mismatch")
        manifest = json.loads(manifest_bytes)
        require(manifest["source_commit"] == artifact["source_commit"], "Artifact source revision mismatch")
        require(manifest["version"] == VERSION and manifest["physical_device"] == "DEVICE-UNVERIFIED",
                "Unexpected version/device declaration")
        require(manifest["catalogue"] == catalogue, "Artifact catalogue mismatch")
        require(rows_by_path(manifest["files"], "manifest") == pinned, "Payload manifest differs from pinned evidence")
        checked_sources = 0
        normalized_text_files = 0
        for name, row in pinned.items():
            info = archive.getinfo("Nevermore/" + name)
            require(info.file_size == row["bytes"], f"Payload size mismatch: {name}")
            with archive.open(info) as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            require(digest == row["sha256"], f"Payload SHA-256 mismatch: {name}")
            if source_repo is not None and name in source_paths:
                original = git_object(source_repo, artifact["source_commit"], source_paths[name])
                if original.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                    require(f"oid sha256:{row['sha256']}\n".encode() in original
                            and f"size {row['bytes']}\n".encode() in original,
                            f"Package differs from source LFS object: {name}")
                else:
                    payload = archive.read(info)
                    require(payload == original or payload.replace(b"\r\n", b"\n") == original,
                            f"Package differs from source Git object: {name}")
                    normalized_text_files += payload != original
                checked_sources += 1
    return {"result": "PASS", "payload_files": len(pinned), "sha256": artifact["sha256"],
            "upstream_payloads_checked": checked_sources,
            "text_payloads_with_checkout_CRLF": normalized_text_files}


def digest_archive(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, help="Private Nevermore checkout with the pinned Git objects")
    parser.add_argument("--archive", type=Path, help="Private ZIP; checked without extraction")
    parser.add_argument("--artifact", choices=("local_candidate", "private_draft"), default="local_candidate")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        metadata = load_json(root / RELEASE_METADATA)
        catalogue = verify_source(root, metadata, args.source_repo)
        verify_metadata(metadata, catalogue, args.source_repo)
        archive_result = (verify_archive(args.archive, metadata["artifacts"][args.artifact], catalogue,
                                         args.source_repo, metadata["package_source_paths"])
                          if args.archive else {"result": "NOT_RUN", "reason": "No private archive supplied"})
        print(json.dumps({"result": "PASS", "scope": "available integrity checks only",
                          "curated_source_files": 23, "runtime_pins": 34, "events": 20,
                          "upstream_git_objects": "PASS" if args.source_repo else "NOT_RUN",
                          "archive": archive_result, "media_decode": "NOT_RUN: use the package tools/verify_release.py",
                          "physical_device": "DEVICE-UNVERIFIED", "publication_authorized": False}, indent=2))
        return 0
    except (VerificationError, OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError,
            zipfile.BadZipFile) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
