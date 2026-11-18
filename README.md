# Spredin Pro plugins for Claude

Two plugins for [Spredin Pro](https://spredin.com), the Excel-compatible
spreadsheet app. This repository is also a marketplace that lists both.

| Plugin | What it is | Where |
|---|---|---|
| [`plugins/spredin-pro`](plugins/spredin-pro) | The Spredin Pro skill: how the app, its formulas, its files and its Python panel work. Markdown only. | Anthropic's plugin directory, and this marketplace |
| [`plugins/spredin-pro-tools`](plugins/spredin-pro-tools) | Spredin Pro's tools for Claude Code: read and change the workbooks open in Spredin Pro, each change asking you there first. A local server. | This marketplace only |

```text
/plugin install spredin-pro --marketplace GGHomology/Spredin-plugin
/plugin install spredin-pro-tools --marketplace GGHomology/Spredin-plugin
```

Anthropic's directory takes no local servers or scripts from an organization
it has not verified, so the tools are a plugin of their own, and the
directory's copy of the skill leaves out `scripts/sprd.py` (the skill says what
to do without it). In Claude Desktop's chat, the tools come from the Spredin
Pro extension: <https://github.com/GGHomology/Spredin-connector/releases/latest>.
Add the skill from the directory or from here, not both.

## Where their parts come from

Nothing in the plugins' `skills/` and `server/` folders is edited here:

| In | From | Path there |
|---|---|---|
| `plugins/spredin-pro/skills/spredin-pro/` | [Spredin-skill](https://github.com/GGHomology/Spredin-skill) | `skills/spredin-pro/`, without `scripts/` |
| `plugins/spredin-pro-tools/server/` | [Spredin-connector](https://github.com/GGHomology/Spredin-connector) | `server/index.js`, `connector.js`, `tools.json` |
| `plugins/spredin-pro-tools/package.json` | Spredin-connector | `package.json`, without `scripts` |

The rest (each plugin's `.claude-plugin/plugin.json`, the tools plugin's
`.mcp.json`, the READMEs, licences and icons) is written here. `SOURCES.json`
records, for each source, the commit that last changed what was copied.

The tools plugin's server is the same program as the Claude Desktop
extension. Its `.mcp.json` starts it with `SPREDIN_CONNECTOR_HOST=plugin`,
which changes only how it tells the user to update it. Its version is the
connector's.

`review/` holds the notes and sample files for Anthropic's reviewers.

## Update the plugins

1. Commit the change in the skill's or the connector's repository, with their
   tests passing.
2. Here, run `python3 tools/sync.py`. It copies what those commits hold (it
   refuses a source with changes not committed), removes files the sources no
   longer have, and rewrites `SOURCES.json`. The source checkouts default to
   `../spredin-skill` and `../spredin-connector`; `--skill` and `--connector`
   name others.
3. Raise `version` in the changed plugin's `.claude-plugin/plugin.json`: the
   directory takes a new version only when it changes, and the tools plugin's
   version is the connector's.
4. Run the tests and `claude plugin validate` on each plugin, then commit.

## Test

```text
python3 -m unittest discover -s tests -v
```

`tests/test_plugin.py` checks both plugins against Anthropic's pre-submission
checklist (read 2026-11-18), and the directory plugin also against the rule
the developer portal gave that day for an organization it has not verified:
Markdown, text, JSON, YAML and images only, nothing that starts with `#!`, no
local server, hooks or other commands, no package manager files, and front
matter strict YAML reads. For the tools plugin it checks the server: started
as `node` on a file in the plugin, importing only Node's own modules and its
own files, running nothing but `lsof`, and installing nothing. Across the
repository: no hidden characters or HTML comments, no private paths or
key-like text, and that the copies are what the two sources make (when they
are checked out beside this one). It also starts the tools plugin's server as
`.mcp.json` says, on empty random ports with a pairing file in a temporary
folder. Set `SPREDIN_PLUGIN_DENYLIST` to a file of private words (one a line)
to check that none appears.

## Licence

MIT: see `LICENSE`.
