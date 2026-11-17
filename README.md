# Spredin Pro plugin for Claude

The plugin for Anthropic's plugin directory and for Claude Code: Spredin Pro's
skill and Spredin Pro's tools in one folder. The plugin is
[`plugins/spredin-pro`](plugins/spredin-pro); its README is what people read
before they install it.

This repository is also a marketplace (`.claude-plugin/marketplace.json`), so
the plugin can be added by the repository's name before, or without, a
directory listing:

```text
/plugin install spredin-pro --marketplace GGHomology/Spredin-plugin
```

## Where its parts come from

The plugin is made of two other repositories. Nothing in its `skills/` and
`server/` folders is edited here:

| In the plugin | From | Path there |
|---|---|---|
| `skills/spredin-pro/` | [Spredin-skill](https://github.com/GGHomology/Spredin-skill) | `skills/spredin-pro/` |
| `server/index.js`, `server/connector.js`, `server/tools.json` | [Spredin-connector](https://github.com/GGHomology/Spredin-connector) | `server/` |
| `package.json` | Spredin-connector | `package.json`, without `scripts` |

The rest of the plugin (`.claude-plugin/plugin.json`, `.mcp.json`,
`README.md`, `LICENSE`, `assets/icon.png`) is written here. `SOURCES.json`
records the commit each copy came from.

The server is the same program as the Claude Desktop extension (the `.mcpb`).
The plugin's `.mcp.json` starts it with `SPREDIN_CONNECTOR_HOST=plugin`,
which changes only how it tells the user to update it.

## Update the plugin

1. Commit the change in the skill's or the connector's repository, with their
   tests passing.
2. Here, run `python3 tools/sync.py`. It copies what those commits hold (it
   refuses a source with changes not committed), removes files the sources no
   longer have, and rewrites `SOURCES.json`. The source checkouts default to
   `../spredin-skill` and `../spredin-connector`; `--skill` and `--connector`
   name others.
3. Raise `version` in `plugins/spredin-pro/.claude-plugin/plugin.json`. The
   directory takes a new version only when it changes.
4. Run the tests and `claude plugin validate .`, then commit.

## Test

```text
python3 -m unittest discover -s tests -v
```

`tests/test_plugin.py` checks the plugin against Anthropic's pre-submission
checklist (read 2026-11-18): the manifest and its name, the README's length
and the licence, the icon, file names, sizes and kinds, no links, lockfiles
or package sources, the MCP server started as `node` on a file in the plugin,
the server importing only Node's own modules and its own files and running
nothing but `lsof`, no private paths or key-like text, and that the copies
are what the two sources make (when they are checked out beside this one).
It also starts the plugin's own copy of the server, as `.mcp.json` says, on
empty random ports with a pairing file in a temporary folder: it must list
the tools with titles and annotations, and say how to reach Spredin Pro.
Set `SPREDIN_PLUGIN_DENYLIST` to a file of private words (one a line) to
check that none appears.

Claude Code's own check:

```text
claude plugin validate .
claude plugin validate ./plugins/spredin-pro
```

## Licence

MIT: see `LICENSE`.
