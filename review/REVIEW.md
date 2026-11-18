# For Anthropic's reviewers

How to try the Spredin Pro plugin. It is a skill, Markdown only: it teaches
Claude how Spredin Pro works (the app, its formulas, its files and its Python
panel). It runs nothing and connects to nothing. Its README
(`plugins/spredin-pro/README.md`) is the listing text.

## What you need

- **Claude with code execution on** (Settings → Capabilities), in chat, Cowork
  or Claude Code.
- **The sample files** in this folder:
  - [`sample-sales.csv`](sample-sales.csv): 24 orders (Month, Region,
    Customer, Units, Price);
  - [`sample-sales.sprd`](sample-sales.sprd): the same orders as a Spredin
    workbook, with a Revenue column of formulas (`=D2*E2` …), a Total row, a
    second sheet "Rates" and a defined name `GST`.
- **Optional, for the prompts that use the app:** a Mac with Spredin Pro 1.0.4
  or later from the Mac App Store. It is a paid app; we give reviewers App
  Store promo codes. Ask through <https://spredin.com/support> or in the
  submission's review, and we send them there.

## Prompts to try, and what to expect

1. **Attach `sample-sales.sprd`, then: "What is in this Spredin workbook, and
   which formulas does it have?"**
   - Claude reads the file with Python's `gzip` and `json` (the skill explains
     the format) and reports two sheets: Sales, A1:F26, with 24 Revenue
     formulas `=D2*E2` … `=D25*E25` and two totals `=SUM(D2:D25)` and
     `=SUM(F2:F25)`; Rates, with the name GST pointing at `Rates!$B$2`.
   - It says the file holds formulas, not their results: Spredin Pro works them
     out when it opens the file.
2. **Attach `sample-sales.csv`, then: "Make a workbook from this that opens in
   Spredin Pro, with Revenue (Units × Price) as formulas and a total row."**
   - Claude writes an `.xlsx` (openpyxl) or a `.csv`, with formulas such as
     `=D2*E2`. Opened in Spredin Pro, the Revenue total is 8,539.15.
3. **"Write a script for Spredin Pro's Python panel that adds a Revenue column
   to the active sheet (Units × Price) as formulas, with a total under it."**
   - Claude writes a script using Spredin's API (`sheet.set_cell`,
     `sheet.fill_down`, `sheet.style`), with formulas rather than computed
     numbers. Pasted into Spredin Pro's Python panel and run on the CSV's sheet,
     it adds the column; the total is 8,539.15.
4. **"In Spredin Pro, how do I freeze the header row, and what does ⌘K do?"**
   - Rows/Cols → Freeze Top Row (or ⌘K, then "freeze top row"); ⌘K opens the
     command palette, which runs any command by name.
5. **"Why does Spredin Pro keep `007` and a 19-digit account number as text
   when Excel turns them into numbers?"**
   - Claude explains Spredin Pro's rule: a digit string with leading zeros, or
     more than 15 digits, stays text so no digit is lost; Excel turns them into
     numbers (`7`, and a number rounded to 15 digits).

## What the skill does not do

- It has no programs, server, hooks or settings, and makes no network calls.
- Spredin Pro's tools (reading and changing the workbooks open in the app)
  are not part of this plugin. They come separately: the Spredin Pro
  extension for Claude Desktop, and the Spredin Pro Tools plugin for Claude
  Code in this repository's own marketplace. The skill uses them when they are
  there.

Privacy policy: <https://spredin.com/privacy>. Support:
<https://spredin.com/support>.
