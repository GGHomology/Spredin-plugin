# Spredin Pro for Claude

This plugin is a skill that helps Claude work in
[Spredin Pro](https://spredin.com), the Excel-compatible spreadsheet app. With
it, Claude knows how Spredin Pro works and how to get things done in it:

- **Operating the app**, on screen or by instructions: its menus, keyboard
  shortcuts, the command palette, dialogs, freezing, filters, pivots, charts
  and slides.
- **Formulas**: its 389 functions, and where Spredin Pro works something out
  differently from Excel (identifiers such as `007` or 19-digit account
  numbers stay text, for one).
- **Workbook files**: what to write so Spredin Pro opens it as intended
  (`.xlsx`, `.csv`, or its own `.sprd`), and how to read a `.sprd` file.
- **Scripts for its Python panel**: the API for reading and writing sheets,
  pivots, charts and slides, so a script runs the first time.

The skill loads in chat, Cowork and Claude Code. It is Markdown only: it runs
nothing and connects to nothing.

## Install

- **The Claude app** (chat and Cowork): Customize → Plugins, find Spredin Pro,
  and add it.
- **Claude Code:**

  ```text
  /plugin install spredin-pro --marketplace GGHomology/Spredin-plugin
  ```

## Spredin Pro's tools, separately

To let Claude read the workbooks you have open in Spredin Pro and change them,
with each change asking you in Spredin Pro first, Spredin Pro has tools that
come separately:

- **Claude Desktop**: the Spredin Pro extension,
  <https://github.com/GGHomology/Spredin-connector/releases/latest>.
- **Claude Code**: the Spredin Pro Tools plugin,
  `/plugin install spredin-pro-tools --marketplace GGHomology/Spredin-plugin`.

The skill tells Claude to use them when they are there, and otherwise works
with files, scripts and the screen.

## What you need

- **Spredin Pro 1.0.4 or later.** Today it runs on the Mac: from the Mac App
  Store, on macOS 13 or later.
- For the skill to read or write files, Claude's code execution: in the Claude
  app, Settings → Capabilities.

## Examples

- "In Spredin Pro, how do I freeze the header row and filter a table?"
- "Write a script for Spredin's Python panel that adds a Revenue column (Units
  × Price) as formulas, with a total under it."
- "Make a workbook from these two CSV files that opens in Spredin Pro with a
  summary sheet."
- "Read this .sprd file and tell me which formulas refer to the Rates sheet."
- "Why does Spredin keep my account numbers as text when Excel turns them into
  numbers?"
- "Make a pivot of revenue by region and month in Spredin, with a chart."

## What it runs, sends and keeps

- **Nothing of its own.** The skill is instructions and reference pages for
  Claude. It has no programs, server or settings.
- **Files:** when you ask Claude to read or make a workbook file, Claude may
  write and run a short Python program in its own code execution, using
  Python's standard library or an Excel library such as openpyxl, on the files
  you give it.
- **Your data:** what Claude reads from your files goes to Anthropic as part
  of your conversation, as with anything else you share with Claude. Nothing
  goes to the makers of Spredin Pro. The skill tells Claude that text in a
  workbook is data, never instructions, and not to send it to a website or
  another tool unless you asked. Spredin Pro's privacy policy:
  <https://spredin.com/privacy>.

## When something does not work

- **Claude does not use the skill:** mention Spredin or Spredin Pro in your
  request, or ask "Which skills do you have from plugins?" to check that it is
  installed.
- **Claude cannot open your file in chat:** attach it to the conversation, or
  use Claude Code or Cowork where your files are.
- **Claude says Spredin Pro's tools cannot be reached:** open Spredin Pro and
  turn on Settings → Connect AI Apps. In a Cowork task the tools cannot reach
  Spredin Pro (the task runs in a virtual machine); the skill still works with
  files.

Support: <https://spredin.com/support>.

## Licence

MIT: see [LICENSE](LICENSE). The skill is built from
<https://github.com/GGHomology/Spredin-skill>, whose copy also has
`scripts/sprd.py`, a small reader and writer of `.sprd` files that Anthropic's
directory does not take in a plugin.
