"""Fetch an explicitly approved media ZIP into ignored staging; never publish it.

Only config/publication.json grants approval. The media manifest remains a record
of what was prepared privately. No credentials, SDK or application approval are
used by this promotional-media preparation step.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import shutil
import socket
import ssl
import stat
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
import zipfile

HASH = re.compile(r"[a-f0-9]{64}\Z")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:webp|png|jpg|mp4|vtt|txt|md)\Z")
MAX_ARCHIVE = 8 * 1024 * 1024
MAX_EXPANDED = 20 * 1024 * 1024
MAX_FILE = 10 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def public_https_url(value, resolve_dns=False):
    require(isinstance(value, str) and not re.search(r"[\s\\]", value), "A public HTTPS bundle URL is required")
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
            and not parsed.fragment and parsed.port in {None, 443}, "Bundle URL must use HTTPS without credentials, fragment or custom port")
    host = parsed.hostname.lower()
    require("." in host and not host.endswith((".localhost", ".local")) and host != "localhost",
            "Bundle URL must identify a public host")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP literal bundle hosts are not allowed")
    require(not any(key.lower() in {"token", "access_token", "api_key", "authorization", "password", "secret"}
                    for key, _ in parse_qsl(parsed.query)), "Credentials cannot be supplied in bundle URLs")
    if resolve_dns:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        require(addresses and all(ipaddress.ip_address(item[4][0]).is_global for item in addresses),
                "Bundle host resolved to a non-public address")
    return value


def approved_manifest(root):
    policy = json.loads((root / "config/publication.json").read_text(encoding="utf-8"))
    payload = (root / "docs/media/manifest.json").read_bytes()
    manifest = json.loads(payload)
    media = policy.get("media", {})
    require(media.get("approved") is True and isinstance(media.get("approval_reference"), str)
            and media["approval_reference"].strip(), "Promotional media approval and its owner reference are required")
    require(media.get("manifest_sha256") == sha(payload), "Approval does not name the exact media manifest")
    public_https_url(media.get("bundle_url"))
    require(isinstance(media.get("bundle_sha256"), str) and HASH.fullmatch(media["bundle_sha256"])
            and media["bundle_sha256"] == manifest.get("bundle", {}).get("sha256"),
            "Approved bundle SHA-256 must match the committed manifest")
    expected_bytes = manifest["bundle"].get("bytes")
    require(isinstance(expected_bytes, int) and 0 < expected_bytes <= MAX_ARCHIVE, "Invalid or oversized bundle")
    rows = manifest.get("assets")
    require(isinstance(rows, list) and 0 < len(rows) <= 64, "Invalid media asset list")
    assets = {}
    names = set()
    for row in rows:
        name = row.get("path")
        require(isinstance(name, str) and NAME.fullmatch(name) and ".." not in name
                and name.lower() not in names, "Media assets require unique flat filenames")
        require(isinstance(row.get("bytes"), int) and 0 < row["bytes"] <= MAX_FILE
                and isinstance(row.get("sha256"), str) and HASH.fullmatch(row["sha256"]), "Invalid media size/hash")
        names.add(name.lower())
        assets[name] = row
    require(sum(row["bytes"] for row in assets.values()) <= MAX_EXPANDED, "Media exceeds the expanded size limit")
    return media, manifest, assets


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def download(url, destination, expected_bytes):
    # Ignore environment proxies and never send authorization/cookie headers.
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    started = time.monotonic()
    for attempt in range(4):
        public_https_url(url, resolve_dns=True)
        try:
            response = opener.open(Request(url, headers={"Accept": "application/zip", "User-Agent": "GlassPlay-media-verifier/1"}), timeout=10)
        except HTTPError as error:
            if error.code in {301, 302, 303, 307, 308} and attempt < 3:
                location = error.headers.get("Location")
                require(location, "Bundle redirect has no target")
                url = urljoin(url, location)
                error.close()
                continue
            raise ValueError(f"Bundle download failed with HTTP {error.code}") from None
        with response:
            require(response.status == 200, "Bundle server did not return a file")
            if response.headers.get("Content-Length") is not None:
                require(int(response.headers["Content-Length"]) == expected_bytes, "Bundle download size differs from manifest")
            received = 0
            with destination.open("xb") as output:
                while chunk := response.read(64 * 1024):
                    received += len(chunk)
                    require(received <= expected_bytes and time.monotonic() - started <= 40,
                            "Bundle exceeded its download size/time limit")
                    output.write(chunk)
            require(received == expected_bytes, "Bundle download was incomplete")
            return
    raise ValueError("Too many bundle redirects")


def verify_bundle(archive_path, media, manifest, assets):
    require(archive_path.is_file() and archive_path.stat().st_size == manifest["bundle"]["bytes"], "Bundle size mismatch")
    with archive_path.open("rb") as source:
        require(hashlib.file_digest(source, "sha256").hexdigest() == media["bundle_sha256"], "Bundle SHA-256 mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        require(len(infos) == len(assets) and {info.filename for info in infos} == set(assets),
                "Bundle has missing, duplicate or unapproved files")
        for info in infos:
            require(info.filename in assets and NAME.fullmatch(info.filename) and ".." not in info.filename,
                    "Unsafe bundle filename")
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(not info.is_dir() and mode in {0, stat.S_IFREG} and not info.flag_bits & 1
                    and info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}, "Indirect, encrypted or unsupported ZIP entry")
            row = assets[info.filename]
            require(info.file_size == row["bytes"], "ZIP expanded size differs from manifest")
            with archive.open(info) as source:
                payload = source.read(row["bytes"] + 1)
            require(len(payload) == row["bytes"] and sha(payload) == row["sha256"], "ZIP media payload hash mismatch")


def verify_staging(destination, assets):
    require(destination.is_dir() and not destination.is_symlink(), "Media staging must be a real directory")
    require({p.name for p in destination.iterdir()} == set(assets), "Staged media has missing or extra files")
    for name, row in assets.items():
        source = destination / name
        require(source.is_file() and not source.is_symlink() and source.stat().st_size == row["bytes"]
                and sha(source.read_bytes()) == row["sha256"], "Staged media differs from approval")


def prepare(root, fetch=download):
    root = root.resolve()
    media, manifest, assets = approved_manifest(root)
    private = root / ".private"
    staging = private / "approved-media"
    for folder in (private, staging):
        require(not folder.is_symlink(), "Staging parent must not be a symlink")
        folder.mkdir(exist_ok=True)
        require(folder.resolve().is_relative_to(root), "Staging escaped the workspace")
    destination = staging / media["manifest_sha256"]
    if destination.exists():
        verify_staging(destination, assets)
        return destination, len(assets), "verified_cache"
    # Work inside ignored staging, then rename only a completely verified folder.
    with tempfile.TemporaryDirectory(prefix="verify-", dir=staging) as temporary:
        work = Path(temporary)
        archive_path = work / "bundle.zip"
        fetch(media["bundle_url"], archive_path, manifest["bundle"]["bytes"])
        verify_bundle(archive_path, media, manifest, assets)
        extracted = work / "files"
        extracted.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for name in assets:
                # Flat, validated names only; never call extract/extractall.
                with archive.open(name) as source, (extracted / name).open("xb") as output:
                    shutil.copyfileobj(source, output, length=64 * 1024)
        verify_staging(extracted, assets)
        extracted.rename(destination)
    return destination, len(assets), "downloaded_and_verified"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        destination, count, result = prepare(Path(__file__).resolve().parents[1])
        print(json.dumps({"result": result, "directory": str(destination), "assets": count, "published": False}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(json.dumps({"result": "HELD", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
