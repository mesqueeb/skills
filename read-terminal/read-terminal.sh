#!/bin/sh
# usage: read-terminal.sh                 list every iTerm2 tab (tty + name)
#        read-terminal.sh <match> [lines] print the last [lines] (default 200, 0 = all) of the one tab
#                                         whose name or tty contains <match>, case-insensitive
set -eu

if [ $# -eq 0 ]; then
  exec osascript - <<'APPLESCRIPT'
set out to ""
tell application "iTerm2"
  repeat with w in windows
    repeat with t in tabs of w
      repeat with s in sessions of t
        set out to out & (tty of s) & "  " & (name of s) & linefeed
      end repeat
    end repeat
  end repeat
end tell
return out
APPLESCRIPT
fi

match=$1
lines=${2:-200}

contents=$(osascript - "$match" <<'APPLESCRIPT'
on run argv
  set needle to item 1 of argv
  set found to {}
  tell application "iTerm2"
    repeat with w in windows
      repeat with t in tabs of w
        repeat with s in sessions of t
          if (name of s) contains needle or (tty of s) contains needle then set end of found to s
        end repeat
      end repeat
    end repeat
    if (count of found) is 1 then return contents of item 1 of found
    if (count of found) is 0 then return "ERROR: no tab matches \"" & needle & "\"; run read-terminal.sh without arguments to list tabs"
    set msg to "ERROR: " & (count of found) & " tabs match \"" & needle & "\"; use a more specific match:" & linefeed
    repeat with s in found
      set msg to msg & (tty of s) & "  " & (name of s) & linefeed
    end repeat
    return msg
  end tell
end run
APPLESCRIPT
)

case $contents in
  "ERROR: "*) printf '%s\n' "$contents" >&2; exit 1 ;;
esac

# iTerm pads every line with a trailing space and includes the empty screen rows below the cursor
trimmed=$(printf '%s\n' "$contents" | sed 's/ *$//')
if [ "$lines" -eq 0 ]; then
  printf '%s\n' "$trimmed"
else
  printf '%s\n' "$trimmed" | tail -n "$lines"
fi
