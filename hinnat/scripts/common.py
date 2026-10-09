"""What both the launcher and the session-start hook need: where things are,
the organisation key, and the small window that asks for it.

The key comes from, in order: Teams-managed HINNAT_KEY, the plugin's own
setting (CLAUDE_PLUGIN_OPTION_KEY, hooks only), the copy saved in the data
folder. When there is none, or the server refuses the one there is (changed,
organisation closed), a small always-on-top window asks for it — no command
for the user to learn, and the key never passes through the chat.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if not os.path.isdir(os.path.join(ROOT, "lib")):          # run from the repo
    ROOT = os.path.dirname(ROOT)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def setup(data):
    """Point lib/ at the data folder, then make it importable."""
    os.makedirs(data, exist_ok=True)
    os.environ["HINNAT_DATA"] = data
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)



FIRST = "Liitä tähän organisaation avain, jonka sait Pasilta (alkaa hk_)."
CHANGED = ("Avain on vaihtunut tai sitä ei enää hyväksytä. Liitä uusi avain, "
           "jonka sait Pasilta (alkaa hk_).")
WRONG = "Avain ei kelpaa. Tarkista että kopioit koko avaimen (alkaa hk_) ja liitä uudelleen."


# macOS: the system's own dialog. The message goes in as an argument, never
# into the script text, so no quoting can break it. "Myöhemmin" cancels
# (exit 1, nothing printed); after `wait` seconds it gives up the same way.
MAC_DIALOG = """on run argv
activate
set r to display dialog (item 1 of argv) default answer "" with hidden answer with title "Hinnat — organisaation avain" buttons {"Myöhemmin", "OK"} default button "OK" cancel button "Myöhemmin" giving up after (item 2 of argv as integer)
if gave up of r then return ""
return text returned of r
end run"""


# Windows: scripts/avain.ps1, fed on stdin as readable text (07.10.2026; it was
# an -EncodedCommand before, which anti-virus tools treat as a malware sign).
WIN_DIALOG = os.path.join(HERE, "avain.ps1")


def ask_key(message, wait=300):
    """The window. -> pasted text or '' (closed, timed out, no dialog here).
    The key is typed hidden, as dots."""
    env, stdin = None, None
    if sys.platform == "darwin":
        cmd = ["osascript", "-e", MAC_DIALOG, message, str(int(wait))]
    elif os.name == "nt":
        with open(WIN_DIALOG, encoding="ascii") as fh:
            stdin = fh.read()
        env = dict(os.environ, HINNAT_DLG_TITLE="Hinnat — organisaation avain",
                   HINNAT_DLG_MSG=message, HINNAT_DLG_LATER="Myöhemmin",
                   HINNAT_DLG_WAIT=str(int(wait)))
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-STA", "-Command", "-"]
    else:
        return ""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           input=stdin, env=env, timeout=wait + 15)
        return (r.stdout or "").strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def ensure_key(hub, refused=False):
    """A key the server accepts, asking in the window when needed.
    -> (key, organisation name) or ("", reason)."""
    key = "" if refused else hub.key()
    msg = CHANGED if refused else FIRST
    for _ in range(3):
        if not key:
            key = ask_key(msg)
            if not key:
                return "", "avainta ei annettu (ikkuna suljettiin)"
            asked = True
        else:
            asked = False
        try:
            b = hub.request("GET", "/v1/bundle", k=key)
        except hub.HubError as e:
            if e.status == 401:
                if not asked and os.environ.get("HINNAT_KEY") == key:
                    return "", ("organisaation hallinnoima avain ei kelpaa — "
                                "pyydä adminia päivittämään se")
                key, msg = "", (WRONG if asked else CHANGED)
                continue
            return key, ""                      # server down: keep what we have
        if asked:
            hub.save_key(key)
        return key, b["tenant"]["name"]
    return "", "avain ei kelpaa"
