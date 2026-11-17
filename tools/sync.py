#!/usr/bin/env python3
"""Copy the skill and the connector's server into the plugin folder.

    python3 tools/sync.py [--skill DIR] [--connector DIR] [--check]

The plugin is made of two other repositories, as their last commits hold
them:

- the skill (GGHomology/Spredin-skill): every file git tracks under
  skills/spredin-pro, copied to plugins/spredin-pro/skills/spredin-pro;
- the connector (GGHomology/Spredin-connector): server/index.js,
  server/connector.js and server/tools.json, copied to
  plugins/spredin-pro/server, and its package.json without "scripts" (which
  name tools the plugin does not carry), copied to plugins/spredin-pro.

The source folders default to ../spredin-skill and ../spredin-connector
beside this repository. Each must be a git checkout whose copied files have
no changes not committed: what is copied is what a commit holds, so
SOURCES.json, which records the two commits, says exactly where every copied
byte came from. Files the copy no longer has are removed from the plugin; the
plugin's own files (its manifest, .mcp.json, README.md, LICENSE) are never
touched.

--check changes nothing and exits 1 when the plugin is not what a sync would
make (the tests run it).

Standard library only. It runs `git` and nothing else.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "spredin-pro")
SOURCES = os.path.join(ROOT, "SOURCES.json")
SKILL_DIR = "skills/spredin-pro"
SERVER_FILES = ["server/index.js", "server/connector.js", "server/tools.json"]
# The folders a sync owns inside the plugin: anything else in them is removed.
OWNED = ["skills", "server"]
REPOS = {
    "skill": "https://github.com/GGHomology/Spredin-skill",
    "connector": "https://github.com/GGHomology/Spredin-connector",
}


class SyncError(Exception):
    pass


def git(repo, *args):
    try:
        return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise SyncError(f"git failed in {repo}: {e}") from e


def tracked(repo, paths):
    """{path: blob} of the plain files git tracks under `paths`."""
    out = {}
    for rec in git(repo, "ls-files", "-s", "-z", "--", *paths).split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, blob, _stage = meta.decode().split()
        path = path.decode("utf-8")
        if mode not in ("100644", "100755"):
            raise SyncError(f"{repo}: {path} is not a plain file (git mode {mode})")
        out[path] = blob
    return out


def refuse_changes(repo, paths):
    status = git(repo, "status", "--porcelain", "-z", "--untracked-files=no", "--", *paths).split(b"\0")
    changed = sorted(r[3:].decode("utf-8", "replace") for r in status if r)
    if changed:
        raise SyncError(f"{repo} has changes not committed; commit them first: " + ", ".join(changed))


def committed(repo, blob):
    return git(repo, "cat-file", "blob", blob)


def head(repo):
    return git(repo, "rev-parse", "HEAD").decode().strip()


def plan(skill_repo, connector_repo):
    """{plugin path: bytes} a sync would write, and the SOURCES.json record."""
    files = {}

    refuse_changes(skill_repo, [SKILL_DIR, "VERSION"])
    skill = tracked(skill_repo, [SKILL_DIR])
    if f"{SKILL_DIR}/SKILL.md" not in skill:
        raise SyncError(f"{skill_repo} has no {SKILL_DIR}/SKILL.md")
    for path, blob in skill.items():
        files[path] = committed(skill_repo, blob)
    version = {}
    for line in committed(skill_repo, tracked(skill_repo, ["VERSION"])["VERSION"]).decode().splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            version[k] = v

    refuse_changes(connector_repo, SERVER_FILES + ["package.json"])
    conn = tracked(connector_repo, SERVER_FILES + ["package.json"])
    for path in SERVER_FILES:
        if path not in conn:
            raise SyncError(f"{connector_repo} has no {path}")
        files[path] = committed(connector_repo, conn[path])
    pkg = json.loads(committed(connector_repo, conn["package.json"]))
    pkg.pop("scripts", None)
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        if pkg.get(key):
            raise SyncError(f"the connector's package.json has {key}; the plugin carries no packages")
    files["package.json"] = (json.dumps(pkg, indent=2, ensure_ascii=False) + "\n").encode()

    sources = {
        "skill": {"repository": REPOS["skill"], "commit": head(skill_repo), "version": version.get("skill", "")},
        "connector": {"repository": REPOS["connector"], "commit": head(connector_repo), "version": pkg.get("version", "")},
    }
    return files, (json.dumps(sources, indent=2) + "\n").encode()


def on_disk():
    """{plugin path: bytes} of the files now in the folders a sync owns, and package.json."""
    out = {}
    for top in OWNED:
        base = os.path.join(PLUGIN, top)
        for d, _dirs, names in os.walk(base):
            for n in names:
                full = os.path.join(d, n)
                with open(full, "rb") as f:
                    out[os.path.relpath(full, PLUGIN).replace(os.sep, "/")] = f.read()
    pkg = os.path.join(PLUGIN, "package.json")
    if os.path.exists(pkg):
        with open(pkg, "rb") as f:
            out["package.json"] = f.read()
    return out


def differences(files, sources):
    now = on_disk()
    diff = sorted(p for p in set(files) | set(now) if files.get(p) != now.get(p))
    try:
        with open(SOURCES, "rb") as f:
            if f.read() != sources:
                diff.append("SOURCES.json")
    except FileNotFoundError:
        diff.append("SOURCES.json")
    return diff


def write(files, sources):
    now = on_disk()
    for path in sorted(set(now) - set(files)):
        os.remove(os.path.join(PLUGIN, path))
    for path, data in sorted(files.items()):
        full = os.path.join(PLUGIN, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if now.get(path) != data:
            with open(full, "wb") as f:
                f.write(data)
    for top in OWNED:  # drop folders the removals left empty
        for d, dirs, names in os.walk(os.path.join(PLUGIN, top), topdown=False):
            if not dirs and not names:
                os.rmdir(d)
    with open(SOURCES, "wb") as f:
        f.write(sources)


def main(argv=None):
    p = argparse.ArgumentParser(prog="sync.py", description="Copy the skill and the connector's server into the plugin.")
    p.add_argument("--skill", default=os.path.join(os.path.dirname(ROOT), "spredin-skill"))
    p.add_argument("--connector", default=os.path.join(os.path.dirname(ROOT), "spredin-connector"))
    p.add_argument("--check", action="store_true", help="change nothing; exit 1 if a sync would change the plugin")
    args = p.parse_args(argv)
    try:
        files, sources = plan(args.skill, args.connector)
    except SyncError as e:
        print(f"sync.py: {e}", file=sys.stderr)
        return 2
    diff = differences(files, sources)
    if args.check:
        if diff:
            print("sync.py: the plugin is not what the sources make; run tools/sync.py:", file=sys.stderr)
            for path in diff:
                print(f"  {path}", file=sys.stderr)
            return 1
        print("sync.py: the plugin matches its sources")
        return 0
    write(files, sources)
    print(f"sync.py: {len(diff)} file(s) changed" if diff else "sync.py: nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
