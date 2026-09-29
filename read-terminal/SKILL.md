---
name: read-terminal
description: Read the scrollback of another iTerm2 tab on macOS — a running dev server, a watcher, a build, or whatever the user has open. Use when the user asks you to check a terminal tab, look at logs or output of a process running in their terminal, or says "read-terminal".
---

# Read terminal

Another iTerm2 tab's output lives only in iTerm's memory, so read it through iTerm's scripting API with `read-terminal.sh`, which sits next to this file.

```sh
<skill-dir>/read-terminal.sh                   # list every tab: tty + name
<skill-dir>/read-terminal.sh "<match>" [lines] # last [lines] of one tab (default 200, 0 = whole scrollback)
```

1. **List the tabs** unless the user named one precisely. A tab's name is its running command plus working directory, e.g. `vpr devserver ~/g/g/m/mastery-track (node)`, or the agent's title for agent tabs.
2. **Read the one tab.** `<match>` is a case-insensitive substring of the name or tty. When several tabs match, the script exits 1 and lists them; pick a more specific match — a tty like `ttys007` is always unique. Watch for prefix collisions: `devserver` also matches `devserverpeecho`, so match `"vpr devserver ~"`.
3. **Widen as needed.** Start with the default 200 lines; when the cause of an error sits further up, re-read with a larger count or `0` and search the output, instead of guessing from the tail.

The first run may trigger a macOS prompt asking to let the calling terminal control iTerm; the user must allow it. The scrollback is a snapshot — re-run the script to see new output.
