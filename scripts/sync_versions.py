"""Sync the version tags in README.md with each project's latest GitHub release.

A project line ends with its version, such as `v1.2`. The tag is vX.Y when the
patch is 0, and the full tag otherwise. A tag that is already shown in full,
such as `v1.1.0`, stays in full. Projects with no release are left alone.

Usage, from the repository root:

    python3 scripts/sync_versions.py

Set GITHUB_TOKEN to raise the API rate limit. Only the Python standard
library is needed. It prints each change and writes README.md in place.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
OWNER = "Stiven-Gjekaj"

LINE = re.compile(rf"^- \*\*.*?\[(?P<name>[^\]]+)\]\(https://github\.com/{OWNER}/(?P<slug>[^)/]+)\)\*\*.*$")
TAG = re.compile(r" `(v\d+(?:\.\d+)*)`$")
VERSION = re.compile(r"^v?(\d+(?:\.\d+)+)$")


def latest(slug):
    """The tag of the latest release, or None if there is none."""
    req = urllib.request.Request(f"https://api.github.com/repos/{OWNER}/{slug}/releases/latest",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "sync_versions"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["tag_name"]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 3:
                raise
        except OSError:
            if attempt == 3:
                raise
        time.sleep(2 * (attempt + 1))


def numbers(tag):
    parts = [int(p) for p in tag.lstrip("v").split(".")]
    while len(parts) > 2 and parts[-1] == 0:
        parts.pop()
    return parts


def shown(release, current):
    """How the release tag is written, given the tag shown now (or None)."""
    parts = VERSION.match(release).group(1).split(".")
    full = current is not None and current.count(".") >= 2
    if not full and all(p == "0" for p in parts[2:]):
        parts = parts[:2]
    return "v" + ".".join(parts)


def main():
    lines = README.read_text().split("\n")
    changed = False
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if not m:
            continue
        release = latest(m["slug"])
        if not release or not VERSION.match(release):
            continue
        t = TAG.search(line)
        current = t.group(1) if t else None
        if current and numbers(current) == numbers(release):
            continue
        new = shown(release, current)
        lines[i] = (line[:t.start()] if t else line) + f" `{new}`"
        print(f"{m['name']}: {current or 'no tag'} -> {new}")
        changed = True
    if changed:
        README.write_text("\n".join(lines))
    else:
        print("All versions are up to date.")


if __name__ == "__main__":
    main()
