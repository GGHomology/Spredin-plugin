# Spredin Pro for Claude

This plugin helps Claude work in [Spredin Pro](https://spredin.com), the
Excel-compatible spreadsheet app. It has two parts:

- **A skill** that tells Claude how Spredin Pro works: its menus and keyboard
  shortcuts, how its formulas behave, its `.sprd` workbook files, and the
  Python API of its script panel. It includes `sprd.py`, a small script that
  reads and writes `.sprd` files.
- **Spredin Pro's tools**: Claude reads the workbooks you have open in
  Spredin Pro and changes them. Each change asks you in Spredin Pro first,
  unless you turned on applying changes without asking. The tools come from a
  small local server in this plugin that talks only to Spredin Pro on the
  same computer.

## Install

- **Claude Code:**

  ```text
  /plugin install spredin-pro --marketplace GGHomology/Spredin-plugin
  ```

- **The Claude app** (chat and Cowork): Customize → Plugins → Add → Add
  marketplace, enter `GGHomology/Spredin-plugin`, then add Spredin Pro.

## What works where

| Where you use Claude | The skill | Spredin Pro's tools |
|---|---|---|
| Claude Code, on the computer where Spredin Pro runs | Yes | Yes |
| Cowork | Yes | No: a Cowork task runs in a virtual machine, which cannot reach Spredin Pro, and each tool says so |
| Chat (claude.ai, the Claude apps) | Yes | No: chat does not start a plugin's local server. In Claude Desktop, the [Spredin Pro extension](https://github.com/GGHomology/Spredin-connector/releases/latest) gives chat the same tools |

## What you need

- **Spredin Pro 1.0.4 or later.** Today it runs on the Mac: from the Mac App
  Store, on macOS 13 or later.
- For the tools: **Node.js 18 or later** on the same computer, where Claude
  Code can find it as `node`. The server uses only Node's own modules; nothing is
  downloaded or installed.

## First use

1. In Spredin Pro, choose **Settings → Connect AI Apps** and turn on **Allow
   AI apps on this Mac to connect**. It is off until you do.
2. Open a workbook in Spredin Pro.
3. Ask Claude something about it, for example "What are the totals by region
   in my Sales sheet?"
4. The first time, Claude shows a code such as `K7Q-M2X`, and Spredin Pro asks
   **Allow Claude to use Spredin?** with a code too. Click Allow only if the
   two codes are the same. Claude waits for your answer, then carries on.

After that, reading needs no approval: Claude can read every workbook you have
open in Spredin Pro. A change (cells, a script that writes, slides, the
workbook's notes) shows a card in Spredin Pro with Allow and Don't Allow,
unless you turned on **Apply assistant changes without asking**. A change to
the notes always asks, and so does a script that wants the network, a file or
the printer, unless you allowed that too. Each change is one undo step. Settings → Connect AI
Apps lists the apps you allowed, and Disconnect removes one.

## Examples

- "In Spredin, what were the three biggest orders in March, and from which
  customers?"
- "Add a Total column to the Sales table that sums Q1 to Q4, and a total row
  under it."
- "Make a pivot of revenue by region and month on a new sheet, with a chart."
- "Find the rows in my Expenses sheet where the amount is stored as text, and
  fix them."
- "Write a Python script for Spredin's script panel that removes duplicate
  customer IDs and keeps the newest row."
- "Read this .sprd file and tell me which formulas refer to the Rates sheet."

## What it runs, sends and keeps

- **The server** (`server/index.js` and `server/connector.js`) starts when
  Claude Code or Cowork starts the plugin's tools, as `node
  ${CLAUDE_PLUGIN_ROOT}/server/index.js`. It speaks MCP with Claude over
  standard input and output.
- **It connects only to `127.0.0.1`**, ports 41870 to 41877, where Spredin Pro
  listens while Connect AI Apps is on. It sends nothing to the internet and
  fetches nothing. On a system Spredin Pro does not run on (today, anything
  but macOS) it connects to nothing.
- **Before it asks to pair, it runs `/usr/sbin/lsof`** to check that the
  program on Spredin Pro's port runs under your own user account. It runs no
  other program.
- **It keeps one file**, the pairing file, in
  `~/Library/Application Support/Spredin Connector/pairing.json` on macOS
  (readable by your user account only). It holds the token your Allow gave. The token is
  never sent again: each request is signed with a key made from it, and each
  answer must carry Spredin Pro's signature. The Claude Desktop extension uses
  the same file, so a computer with both pairs once.
- **Its log** goes to Claude's MCP log (standard error) and says what happened,
  such as "paired" or an error. It never holds the token, your data or what
  Claude asked for.
- **`sprd.py`** runs only when Claude runs it, on a file you give. It uses
  Python's standard library only, reads the one file named, writes only the
  file named after `write`, opens no network connection and starts no program.
- **What Claude reads** from your workbooks goes to Anthropic as part of your
  conversation, as with anything else you share with Claude. Nothing goes to
  the makers of Spredin Pro. Spredin Pro's privacy policy:
  <https://spredin.com/privacy>.

The full contract between the server and Spredin Pro, and what it does not
protect against, is in the connector's repository:
<https://github.com/GGHomology/Spredin-connector>.

## When something does not work

- **"Spredin Pro is not open, or its connection for AI apps is off"**: open
  Spredin Pro and turn on Settings → Connect AI Apps.
- **"Spredin Pro has no workbook open"**: open a workbook; Spredin Pro asks to
  allow the connection in a workbook's window.
- **"Spredin Pro does not accept this connection"**: you disconnected Claude in
  Spredin Pro, or another program is answering on its port. Ask Claude to
  connect again, and allow it in Spredin Pro if the codes match.
- **"These Spredin Pro tools work only on the computer where Spredin Pro
  runs"**: this session runs somewhere else, as a Cowork task does. Use Claude
  Code on the computer where Spredin Pro runs, or Claude Desktop with the
  extension; the skill still helps with files you give it.
- **The tools do not appear in Claude Code**: run `/mcp` to see the server's
  state. If it failed to start, check that `node --version` prints 18 or
  later.

Support: <https://spredin.com/support>.

## Licence

MIT: see [LICENSE](LICENSE). The skill and the server are built from
<https://github.com/GGHomology/Spredin-skill> and
<https://github.com/GGHomology/Spredin-connector>.
