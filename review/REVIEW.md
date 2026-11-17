# For Anthropic's reviewers

How to try the Spredin Pro plugin end to end. The plugin's own README
(`plugins/spredin-pro/README.md`) says what it runs, sends and keeps.

## What you need

- **A Mac** with macOS 13 or later, and **Spredin Pro 1.0.4 or later** from
  the Mac App Store. Spredin Pro is a paid app; we give reviewers App Store
  promo codes. Ask through <https://spredin.com/support>, or in the
  submission's review thread, and we send them there.
- **Node.js 18 or later** on that Mac, for the plugin's tools.
- **Claude Code**, for the tools. In chat, only the skill loads (chat does not
  start a plugin's local server).
- **The sample data**: [`sample-sales.csv`](sample-sales.csv) in this folder,
  24 orders (Month, Region, Customer, Units, Price).

## Set up

1. Open Spredin Pro. Choose **Settings → Connect AI Apps** and turn on **Allow
   AI apps on this Mac to connect**.
2. In Spredin Pro, choose **File → Open…** and open `sample-sales.csv`.
3. Start Claude Code with the plugin, from a checkout of this repository:

   ```text
   claude --plugin-dir ./plugins/spredin-pro
   ```

   or install it: `/plugin install spredin-pro --marketplace GGHomology/Spredin-plugin`.

## Prompts to try, and what to expect

1. **"What is the revenue (Units × Price) by region in the workbook open in
   Spredin?"**
   - The first time, Claude shows a six-character code, and Spredin Pro asks
     **Allow Claude to use Spredin?** with a code. Click Allow when they match.
     Claude then answers without asking again.
   - Expected: East 2,937.85; South 2,379.95; North 1,614.00; West 1,607.35;
     8,539.15 in all. Reading asks for no approval.
2. **"Which three orders brought in the most, and from which customers?"**
   - Expected: Aster Foods (East, February) 1,115.10; Cedar & Co (South,
     March) 812.70; Blue Harbour (West, February) 684.00.
3. **"Add a Revenue column that multiplies Units by Price, as formulas, with
   a total under it."**
   - Spredin Pro shows a card, **Claude asks to: …**, with Allow and Don't
     Allow. Allow: the column appears as live formulas (`=D2*E2` and so on),
     and its total is 8,539.15. Each change Claude makes is one undo step in
     Spredin Pro (⌘Z).
   - Don't Allow instead: nothing changes, and Claude is told so.
4. **"Make a pivot of units by region and month on a new sheet."**
   - A card first, then a new pivot sheet. East's units: January 75,
     February 91, March 101.
5. **The skill alone** (in a chat, where the tools do not load): **"In
   Spredin Pro, how do I freeze the header row, and what does ⌘K do?"**
   - Claude answers from the skill: Rows/Cols → Freeze Top Row (or ⌘K, then
     "freeze top row"); ⌘K opens the command palette, which runs any command
     by name.

## The edges

- **Disconnect:** in Spredin Pro, Settings → Connect AI Apps lists Claude;
  Disconnect it. The next tool call says Spredin Pro does not accept the
  connection, and Claude does not connect again unless you ask it to
  (it then calls `connect_spredin`, and Spredin Pro asks again).
- **Connect AI Apps off:** every call says Spredin Pro is not open or its
  connection is off, and nothing is read or changed.
- **Cowork:** a Cowork task runs the server in a virtual machine, where
  every call says the tools work only on the computer where Spredin Pro runs,
  and the server connects to nothing (seen 2026-11-18). The skill still loads
  there.

## What the server runs

`node ${CLAUDE_PLUGIN_ROOT}/server/index.js`, which imports
`server/connector.js` (readable source, Node's own modules only, no
dependencies). Before it asks Spredin Pro to pair, it runs `/usr/sbin/lsof`
to check that the program on Spredin Pro's port runs under the same user
account; it runs no other program. It connects only to `127.0.0.1`, ports
41870 to 41877, and keeps one file, its pairing file, in
`~/Library/Application Support/Spredin Connector/`.

Privacy policy: <https://spredin.com/privacy>. Support:
<https://spredin.com/support>.
