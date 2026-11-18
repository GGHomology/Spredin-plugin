"""The two plugins against Anthropic's plugin checks, and the tools plugin's
server run as Claude Code runs it.

    python3 -m unittest discover -s tests -v

- plugins/spredin-pro is the plugin in Anthropic's directory. Besides the
  pre-submission checklist (read 2026-11-18:
  claude.com/docs/plugins/pre-submission-checklist), it meets the rule the
  developer portal's validation gave the same day for an organization
  Anthropic has not verified: Markdown, text, JSON, YAML and images only; no
  file that starts with "#!"; no local MCP server, hooks, monitors or other
  commands; no package manager files; and front matter that strict YAML reads.
- plugins/spredin-pro-tools is in this repository's own marketplace only: the
  connector's server for Claude Code.

Standard library only. The checks read what git tracks, since that is what
the directory reads. The server tests start the tools plugin's own copy of
the server with the connector's test hooks, on empty random ports and a
pairing file in a temporary folder, so they never touch Spredin Pro or the
real pairing file; the one run without the hooks sends only initialize and
tools/list, which with no pairing file reach no port.
"""
import json
import os
import random
import re
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PLUGIN = "plugins/spredin-pro"
TOOLS_PLUGIN = "plugins/spredin-pro-tools"
RESERVED = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
WINDOWS_DEVICES = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}
SYSTEM_FILES = {".ds_store", "thumbs.db", "desktop.ini"}
IMAGE_MAGIC = {
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".gif": b"GIF8",
    ".webp": b"RIFF",
}
# What an unverified organization's plugin may hold, besides images.
DIRECTORY_TEXT = {".md", ".txt", ".json", ".yaml", ".yml"}
DIRECTORY_PLAIN_NAMES = {"LICENSE", ".gitignore"}
COMMAND_FILES = {".mcp.json", "hooks.json", ".lsp.json", "monitors.json", "settings.json"}
PACKAGE_FILES = {
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "bun.lock", "bun.lockb", "yarn.lock",
    "pnpm-lock.yaml", "pnpm-workspace.yaml", ".npmrc", "bunfig.toml", "uv.toml", ".yarnrc", ".yarnrc.yml",
    "pip.conf", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "uv.lock",
}
LOCKFILES = {"package-lock.json", "npm-shrinkwrap.json", "bun.lock", "bun.lockb", "yarn.lock", "pnpm-lock.yaml"}
REGISTRY_FILES = {".npmrc", "bunfig.toml", "uv.toml", ".yarnrc", ".yarnrc.yml", "pip.conf"}
# Characters that hide text or change its order on screen: zero-width
# characters, bidirectional controls, word joiners, the byte-order mark, the
# soft hyphen and the Unicode tag block. Written as escapes, never as the
# characters themselves.
HIDDEN = re.compile("[\\u00ad\\u200b-\\u200f\\u202a-\\u202e\\u2060-\\u206f\\ufeff\\U000e0000-\\U000e007f]")
PROVENANCE = re.compile(r"\A<!-- Generated from Spredin Pro \d+\.\d+\.\d+ \([^)\n]*\) by tools/gen-refs\.mts\. Do not edit by hand\. -->\n")
# Key shapes, written in pieces so that this file does not match itself.
KEY_SHAPES = re.compile("|".join([
    "sk" + "-ant-", "sk" + "-[A-Za-z0-9]{20,}", "BS" + "A[A-Za-z0-9]{20,}", "tv" + "ly-",
    "-----BEGIN [A-Z ]*PRIV" + "ATE KEY",
]))
LAUNCHERS = re.compile(r"\b(npx|bunx|pnpm\s+dlx|yarn\s+dlx|uvx|pipx\s+run|uv\s+run|npm\s+run)\b")


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], check=True, capture_output=True).stdout


def tracked():
    """{path: (mode, bytes)} of everything git tracks."""
    out = {}
    for rec in git("ls-files", "-s", "-z").split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            mode, blob, _ = meta.decode().split()
            data = git("cat-file", "blob", blob) if mode in ("100644", "100755", "120000") else b""
            out[path.decode("utf-8")] = (mode, data)
    return out


def in_plugin(files, rel):
    pre = rel + "/"
    return {p[len(pre):]: v for p, v in files.items() if p.startswith(pre)}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def words_outside_code(md):
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    return len(re.findall(r"[A-Za-z0-9’'-]+", md))


def yaml_scalar(v):
    """A one-line YAML value as strict YAML reads it, or ValueError: ": " and
    " #" are not allowed in a plain value, so such a value is double-quoted."""
    if v.startswith('"'):
        if not v.endswith('"') or len(v) < 2 or re.search(r'(?<!\\)"', v[1:-1]):
            raise ValueError(f"a double-quoted value YAML cannot read: {v!r}")
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if ": " in v or " #" in v or v[:1] in "'&*!|>%@`[]{},?-#":
        raise ValueError(f"a plain value YAML cannot read: {v!r}")
    return v


class Plugin:
    """Checks every plugin here must pass."""

    REL = ""

    @classmethod
    def setUpClass(cls):
        cls.files = tracked()
        cls.plugin = in_plugin(cls.files, cls.REL)
        if not cls.plugin:
            raise unittest.SkipTest(f"git tracks no files under {cls.REL} yet")

    def manifest(self):
        return json.loads(self.plugin[".claude-plugin/plugin.json"][1])

    def test_manifest(self):
        m = self.manifest()
        name = m["name"]
        self.assertEqual(name, os.path.basename(self.REL))
        self.assertRegex(name, r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
        self.assertNotIn(name, RESERVED)
        self.assertFalse(set(name.split("-")) <= RESERVED, "a name of reserved words only")
        for key in ("description", "author", "version", "displayName", "license"):
            self.assertTrue(m.get(key), key)
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")
        for text in (m["displayName"], m["author"]["name"]):
            text.encode("ascii")  # one writing system, no look-alikes or invisible characters
        self.assertNotIn("experimental", m)
        self.assertNotIn("for the Mac", m["description"], "Spredin Pro comes to Windows later (owner, 2026-11-18)")
        self.assertEqual(set(os.listdir(os.path.join(ROOT, self.REL, ".claude-plugin"))), {"plugin.json"},
                         "only the manifest goes in .claude-plugin")
        icon = m.get("icon")
        self.assertTrue(icon and not icon.startswith(("/", "..")) and icon in self.plugin, "the icon is in the plugin")
        data = self.plugin[icon][1]
        self.assertTrue(data.startswith(IMAGE_MAGIC[".png"]))
        w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        self.assertEqual(w, h, "the icon is square")
        self.assertTrue(512 <= w <= 2048, w)

    def test_readme_and_licence(self):
        self.assertGreaterEqual(words_outside_code(self.plugin["README.md"][1].decode()), 40)
        self.assertIn("MIT License", self.plugin["LICENSE"][1].decode())

    def test_files(self):
        self.assertLessEqual(len(self.plugin), 512)
        lower = {}
        for path, (mode, data) in self.plugin.items():
            self.assertIn(mode, ("100644", "100755"), f"{path}: not a plain file (no links, submodules)")
            self.assertNotIn(b"git-lfs.github.com/spec", data[:200], f"{path}: a Git LFS pointer")
            for part in path.split("/"):
                self.assertNotIn(part.lower(), SYSTEM_FILES, path)
                self.assertNotEqual(part, "__MACOSX", path)
                self.assertNotIn(":", part, path)
                self.assertFalse(part.endswith((".", " ")), path)
                self.assertNotIn(part.lower().split(".")[0], WINDOWS_DEVICES, path)
            for folder in path.split("/")[:-1]:
                self.assertRegex(folder, r"^[A-Za-z0-9._-]+$", path)
            self.assertNotIn(path.lower(), lower, f"{path} and {lower.get(path.lower())} differ only by case")
            lower[path.lower()] = path
            ext = os.path.splitext(path)[1].lower()
            if ext in IMAGE_MAGIC:
                self.assertTrue(data.startswith(IMAGE_MAGIC[ext]), f"{path}: not a complete image")
                continue
            self.assertLess(len(data), 256 * 1024, f"{path} is over 256 KiB")
            self.assertNotIn(b"\0", data, f"{path} holds a NUL byte")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                self.fail(f"{path} is not UTF-8 text")
            self.assertNotIn(os.path.basename(path), LOCKFILES | REGISTRY_FILES, path)
            self.assertFalse(path.startswith("bin/"), "a top-level bin/ stops claude.ai and Cowork installing it")


class DirectoryPlugin(Plugin, unittest.TestCase):
    """plugins/spredin-pro: the skill, as Anthropic's directory takes it."""

    REL = SKILL_PLUGIN

    def test_only_markdown_text_json_yaml_and_images(self):
        for path, (_m, data) in self.plugin.items():
            name = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            self.assertTrue(ext in DIRECTORY_TEXT or ext in IMAGE_MAGIC or name in DIRECTORY_PLAIN_NAMES,
                            f"{path}: not Markdown, text, JSON, YAML or an image")
            self.assertFalse(data.startswith(b"#!"), f"{path} starts with #!")
            self.assertNotIn(name, COMMAND_FILES, f"{path}: a command an unverified organization cannot ship")
            self.assertNotIn(name, PACKAGE_FILES, f"{path}: a package manager file")
            self.assertFalse(path.startswith(("hooks/", "monitors/", "server/", "scripts/", "output-styles/")), path)
            self.assertNotIn("/scripts/", "/" + path, f"{path}: scripts are left out of this plugin")
            self.assertNotIn(".claude/", path)
        m = self.manifest()
        for key in ("mcpServers", "hooks", "lspServers", "monitors", "settings", "commands", "agents", "outputStyles"):
            self.assertNotIn(key, m, f"plugin.json declares {key}")

    def test_the_skill_and_its_front_matter(self):
        skills = sorted({p.split("/")[1] for p in self.plugin if p.startswith("skills/")})
        self.assertEqual(skills, ["spredin-pro"])
        text = self.plugin["skills/spredin-pro/SKILL.md"][1].decode()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(m)
        fields = {}
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            fields[k.strip()] = yaml_scalar(v.strip())
        self.assertEqual(fields["name"], "spredin-pro")
        self.assertIn("Spredin", fields["description"])
        self.assertLessEqual(len(fields["description"]), 200)

    def test_the_skill_says_what_to_do_without_its_script(self):
        text = self.plugin["skills/spredin-pro/SKILL.md"][1].decode()
        self.assertIn("If `scripts/sprd.py` is not here", text)
        self.assertNotIn("skills/spredin-pro/scripts/sprd.py", self.plugin)

    def test_readme_points_to_the_tools_and_says_it_runs_nothing(self):
        r = self.plugin["README.md"][1].decode()
        self.assertIn("/plugin install spredin-pro-tools --marketplace GGHomology/Spredin-plugin", r)
        self.assertIn("runs\nnothing and connects to nothing", r)


class ToolsPlugin(Plugin, unittest.TestCase):
    """plugins/spredin-pro-tools: the connector's server for Claude Code."""

    REL = TOOLS_PLUGIN

    def test_mcp_server_is_a_file_in_the_plugin_run_by_node(self):
        cfg = json.loads(self.plugin[".mcp.json"][1])
        servers = cfg["mcpServers"]
        self.assertEqual(list(servers), ["spredin-pro"])
        s = servers["spredin-pro"]
        self.assertEqual(s["command"], "node")
        self.assertEqual(len(s["args"]), 1, "no --test-hooks, nothing but the file")
        arg = s["args"][0]
        self.assertRegex(arg, r"^\$\{CLAUDE_PLUGIN_ROOT\}/[A-Za-z0-9_./-]+\.js$")
        self.assertNotIn("..", arg)
        self.assertIn(arg.split("}/", 1)[1], self.plugin)
        self.assertEqual(s.get("env"), {"SPREDIN_CONNECTOR_HOST": "plugin"}, "env holds plain values only")
        self.assertNotIn("$", json.dumps(s.get("env")))

    def test_the_server_imports_only_nodes_modules_and_its_own_files(self):
        for path, (_m, data) in self.plugin.items():
            if not path.startswith("server/") or not path.endswith(".js"):
                continue
            src = data.decode()
            for spec in re.findall(r"""^\s*import\s[^'"]*?from\s+['"]([^'"]+)['"]""", src, re.M):
                if spec.startswith("node:"):
                    continue
                self.assertTrue(spec.startswith("./"), f"{path} imports {spec}")
                self.assertIn("server/" + spec[2:], self.plugin, f"{path} imports {spec}, which is not in the plugin")
            self.assertNotRegex(src, r"\brequire\(|\beval\(|new Function\(", path)
            self.assertNotRegex(src, LAUNCHERS, path)
            for prog in re.findall(r"execFile\(\s*([^,]+),", src):
                self.assertIn(prog.strip(), ("this.cfg.lsof",), f"{path} runs {prog}")
            # A regex's .exec( is not a process; child_process's exec is.
            self.assertEqual(re.findall(r"\bspawn\(|(?<![.\w])exec\(|execSync\(|spawnSync\(|\bfork\(", src), [], path)
            want = ["child_process'"] if path == "server/connector.js" else []
            self.assertEqual(re.findall(r"child_process['\"]", src), want, f"{path}: child_process only for lsof")

    def test_package_json_installs_nothing(self):
        pkg = json.loads(self.plugin["package.json"][1])
        self.assertEqual(pkg["type"], "module", "the server is ES modules, for Node 18 too")
        for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies", "scripts",
                    "bin", "bundledDependencies"):
            self.assertNotIn(key, pkg)

    def test_version_is_the_connectors(self):
        sources = json.loads(self.files["SOURCES.json"][1])
        pkg = json.loads(self.plugin["package.json"][1])
        self.assertEqual(pkg["version"], sources["connector"]["version"])
        self.assertEqual(self.manifest()["version"], pkg["version"])


class Repository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = tracked()

    def test_marketplace_lists_both_plugins(self):
        mk = json.loads(self.files[".claude-plugin/marketplace.json"][1])
        self.assertNotIn(mk["name"], RESERVED)
        self.assertEqual([(p["name"], p["source"]) for p in mk["plugins"]],
                         [("spredin-pro", "./" + SKILL_PLUGIN), ("spredin-pro-tools", "./" + TOOLS_PLUGIN)])
        for p in mk["plugins"]:
            m = json.loads(self.files[p["source"][2:] + "/.claude-plugin/plugin.json"][1])
            self.assertEqual(m["name"], p["name"])

    def test_no_gitattributes_that_rewrite(self):
        for path, (_m, data) in self.files.items():
            if os.path.basename(path) == ".gitattributes":
                self.assertNotRegex(data.decode(), r"export-ignore|export-subst|filter=")

    def text_files(self):
        for path, (_m, data) in self.files.items():
            if os.path.splitext(path)[1].lower() in IMAGE_MAGIC or path.endswith(".sprd"):
                continue
            yield path, data.decode("utf-8", "replace")

    def test_no_hidden_characters(self):
        """Nothing a reader cannot see: every instruction is plain text (the
        directory policy, 2G)."""
        for path, text in self.text_files():
            found = sorted({f"U+{ord(c):04X}" for c in HIDDEN.findall(text)})
            self.assertEqual(found, [], path)
            if path.endswith(".md"):
                # An HTML comment is text a reader of the rendered page does not
                # see. The one allowed is the generated files' first line, which
                # says where they came from and tells Claude nothing.
                body = PROVENANCE.sub("", text, count=1)
                self.assertNotIn("<!--", body, f"{path}: an HTML comment")

    def test_no_private_paths_or_keys(self):
        # Private names (folders, files, people) are kept in a list outside
        # this public repository; set SPREDIN_PLUGIN_DENYLIST to check them.
        deny = []
        if os.environ.get("SPREDIN_PLUGIN_DENYLIST"):
            with open(os.environ["SPREDIN_PLUGIN_DENYLIST"], encoding="utf-8") as f:
                deny = [w.strip().lower() for w in f if w.strip()]
        for path, text in self.text_files():
            # "/Users/you/..." in an example is fine; this Mac's own home is not.
            self.assertNotIn(os.path.expanduser("~") + "/", text, path)
            self.assertNotRegex(text, r"/Users/(?!you/)[a-z]|@gmail\.com", path)
            self.assertNotRegex(text, KEY_SHAPES, path)
            for w in deny:
                self.assertNotIn(w, text.lower(), f"{path} holds a word from the private list")

    def test_sources_name_full_commits(self):
        sources = json.loads(self.files["SOURCES.json"][1])
        for k in ("skill", "connector"):
            self.assertRegex(sources[k]["commit"], r"^[0-9a-f]{40}$")

    def test_the_copies_are_what_the_sources_make(self):
        here = os.path.dirname(ROOT)
        if not (os.path.isdir(os.path.join(here, "spredin-skill", ".git"))
                and os.path.isdir(os.path.join(here, "spredin-connector", ".git"))):
            self.skipTest("the two source checkouts are not beside this one")
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "sync.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


def free_base():
    """A block of 8 ports with nothing listening, so the server finds no Spredin."""
    for _ in range(50):
        base = random.randint(46000, 60000)
        busy = False
        for p in range(base, base + 8):
            with socket.socket() as s:
                s.settimeout(0.05)
                if s.connect_ex(("127.0.0.1", p)) == 0:
                    busy = True
                    break
        if not busy:
            return base
    raise RuntimeError("no free port block")


class Server(unittest.TestCase):
    """The tools plugin's own copy of the server, started as .mcp.json says."""

    def run_server(self, messages, extra_env=None, hooks=True):
        """With hooks, also given the test hooks' argument and empty random
        ports, so it never finds Spredin."""
        cfg = json.loads(read(TOOLS_PLUGIN + "/.mcp.json"))["mcpServers"]["spredin-pro"]
        root = os.path.join(ROOT, TOOLS_PLUGIN)
        args = [a.replace("${CLAUDE_PLUGIN_ROOT}", root) for a in cfg["args"]] + (["--test-hooks"] if hooks else [])
        with tempfile.TemporaryDirectory() as home:
            base = free_base()
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": home,
                **cfg.get("env", {}),
                "SPREDIN_CONNECTOR_TEST": "1",
                "SPREDIN_CONNECTOR_PORTS": f"{base}-{base + 7}",
                "SPREDIN_CONNECTOR_PAIRING_FILE": os.path.join(home, "pairing.json"),
                **(extra_env or {}),
            }
            stdin = "".join(json.dumps(m) + "\n" for m in messages)
            r = subprocess.run([cfg["command"], *args], input=stdin, capture_output=True, text=True, env=env,
                               timeout=30, cwd=home)
            self.assertFalse(os.path.exists(os.path.join(home, "pairing.json")), "no pairing was made")
        out = [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
        return {m["id"]: m for m in out if "id" in m}, r.stderr

    HELLO = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "claude-code", "version": "2.1.325"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_workbooks", "arguments": {}}},
    ]

    def test_starts_lists_titled_tools_and_says_how_to_reach_spredin(self):
        got, err = self.run_server(self.HELLO)
        info = got[1]["result"]["serverInfo"]
        pkg = json.loads(read(TOOLS_PLUGIN + "/package.json"))
        self.assertEqual(info, {"name": "spredin-connector", "title": "Spredin Pro", "version": pkg["version"]})
        tools = got[2]["result"]["tools"]
        self.assertGreaterEqual(len(tools), 13)
        for t in tools:
            a = t.get("annotations", {})
            self.assertTrue(t.get("title") and a.get("title"), t["name"])
            self.assertIn("readOnlyHint", a, t["name"])
            self.assertIn("destructiveHint", a, t["name"])
            self.assertLessEqual(len(t["name"]), 64)
        call = got[3]["result"]
        self.assertTrue(call["isError"])
        self.assertIn("Spredin Pro is not open", call["content"][0]["text"])
        self.assertNotIn("Traceback", err)

    def test_where_spredin_does_not_run_it_says_so(self):
        got, _ = self.run_server(self.HELLO, {"SPREDIN_CONNECTOR_PLATFORM": "linux"})
        text = got[3]["result"]["content"][0]["text"]
        self.assertIn("work only on the computer where Spredin Pro runs", text)

    def test_an_environment_alone_cannot_turn_the_test_hooks_on(self):
        """As .mcp.json starts it, with no --test-hooks: SPREDIN_CONNECTOR_TEST=1
        and a hook naming another lsof are ignored. Only initialize and
        tools/list are sent (with no pairing file they reach no port), so a
        Spredin Pro running on this Mac is never asked anything."""
        got, err = self.run_server(self.HELLO[:3], {"SPREDIN_CONNECTOR_LSOF": "/bin/echo"}, hooks=False)
        self.assertIn("result", got[2])
        self.assertNotIn("test mode", err)
        self.assertIn("41870", err, "it would look on Spredin's own ports, not the hook's")


if __name__ == "__main__":
    unittest.main()
