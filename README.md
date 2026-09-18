<div align="center">

<h1>no-api-creator</h1>

<strong>A REST API for desktop software that never shipped one.</strong>

<p>
Plenty of programs have a perfectly good backend and no way to reach it. The
vendor never shipped an API, the integration costs more than the product, or
the thing predates REST entirely. Your only way in is a window someone is
expected to click on.
</p>

<p>
<code>no-api-creator</code> gives that window an HTTP API. It presses the real
buttons of the real program, through the same accessibility layer a screen
reader uses — so the cursor never moves, and the window does not even have to
be visible.
</p>

<p>
<img src="https://img.shields.io/badge/python-3.11%2B-0f766e?style=flat-square" alt="Python 3.11+">
<img src="https://img.shields.io/badge/framework-FastAPI-0f766e?style=flat-square" alt="FastAPI">
<img src="https://img.shields.io/badge/platform-Windows-475569?style=flat-square" alt="Windows">
<img src="https://img.shields.io/badge/status-early-475569?style=flat-square" alt="Early">
</p>

<p>
<a href="#-how-it-works">How it works</a> ·
<a href="#-requirements">Requirements</a> ·
<a href="#-try-the-example">Try the example</a> ·
<a href="#-wrap-your-own-program">Wrap your own program</a> ·
<a href="#-project-structure">Project structure</a> ·
<a href="#-limits">Limits</a>
</p>

</div>

---

## 🧠 How it works

Desktop programs already publish a machine-readable description of themselves:
the one screen readers use. On Windows that is **UI Automation**. Every button
and label in it carries a stable identifier, and it can be pressed directly
rather than aimed at with a mouse.

That has two consequences the whole project rests on.

**It is invisible.** Pressing a button through the accessibility layer does not
touch the mouse or the keyboard queue. Nothing moves on screen, focus is never
stolen, and the window can sit off the edge of the desktop while it works.

**It is only as good as the program's accessibility support.** If a screen
reader can read a program, this can automate it. That covers most business
software. If the program only paints pixels — a game, a custom-drawn chart —
there is nothing to address, and this approach does not apply.

## 🧩 The shape of it

One file knows how to drive **any** program. A second file describes **one**
program. A third turns that into a web API.

```
desktop.py     start, press, read, hide, show      knows about no program at all
calculator.py  the button names of one program     the example
api.py         the endpoints you want to expose    your API
```

`desktop.py` is the whole reusable part, and it is about 120 lines. It has
never heard of a calculator: pointed at Notepad, the same five functions open
it, read its status bar, hide it off screen, and add tabs while it is
invisible.

## 📋 Requirements

- Windows 10 or 11
- Python 3.11 or newer
- `pip install uiautomation fastapi uvicorn requests`

## 🚀 Try the example

The Windows Calculator has no API. This turns it into one.

```powershell
git clone https://github.com/mpek29/no-api-creator.git
cd no-api-creator
pip install uiautomation fastapi uvicorn requests
python -m uvicorn api:app
```

It opens the Calculator and moves it off screen before accepting requests,
which takes a few seconds. Then:

```powershell
curl.exe "http://127.0.0.1:8000/add?a=2&b=3"
```

```json
{ "result": 5.0 }
```

Use `curl.exe` with the extension, or PowerShell substitutes its own `curl`
alias, which takes different arguments. Interactive documentation is generated
from the code at http://127.0.0.1:8000/docs

With the server running, check it from another terminal:

```powershell
python cli.py
```

```
22 passed, 0 failed
```

It tests the answers and the refusals — dividing by zero, recalling an empty
memory, sending a word where a number belongs — and exits with code 1 on
failure, so it drops straight into a CI.

<details>
<summary>The 22 endpoints the example exposes</summary>

| Method | Path | Example |
|---|---|---|
| GET | `/` | what this server can do |
| GET | `/add` | `/add?a=2&b=3` → `5.0` |
| GET | `/subtract` | `/subtract?a=8&b=3` → `5.0` |
| GET | `/multiply` | `/multiply?a=7&b=6` → `42.0` |
| GET | `/divide` | `/divide?a=9&b=4` → `2.25` |
| GET | `/square` | `/square?a=12` → `144.0` |
| GET | `/square_root` | `/square_root?a=81` → `9.0` |
| GET | `/reciprocal` | `/reciprocal?a=8` → `0.125` |
| GET | `/percent` | `/percent?a=200&b=50` → `100.0` |
| GET | `/result` | whatever is on screen now |
| GET | `/expression` | the calculation in progress |
| POST | `/clear` | press C |
| POST | `/clear_entry` | press CE |
| POST | `/backspace` | erase the last digit typed |
| GET | `/memory` | recall the saved number |
| POST | `/memory/store` | `/memory/store?value=10` |
| POST | `/memory/add` | `/memory/add?value=5` |
| POST | `/memory/subtract` | `/memory/subtract?value=3` |
| POST | `/memory/clear` | forget the saved number |
| POST | `/window/show` | put the window back on screen |
| POST | `/window/hide` | move it away again |
| POST | `/press/{button_id}` | `/press/num7Button`, for anything else |

Memory is the interesting one. Store 10, add 5, subtract 3, then recall gives
12 — across four separate requests. That number is held nowhere in this code.
It lives inside the Calculator, which is the whole point.

</details>

## 🔧 Wrap your own program

Three steps, and you never edit `desktop.py`.

**1. Find out what the program exposes.** Open it, then dump its controls:

```powershell
.\tools\probe\uia.ps1 -List                  # every automatable window
.\tools\probe\uia.ps1 -Hwnd <number>         # its whole control tree
```

You are looking for entries with an `automationId`. Those are your handles.
If almost nothing has one, the program is not a good candidate — see
[Limits](#-limits).

**2. Describe the program.** Copy `calculator.py` and change the names:

```python
import desktop

LAUNCH_COMMAND = "myapp.exe"
IDENTIFYING_ELEMENT = "SearchPanel"   # an id only this program has

def start():
    return desktop.start(LAUNCH_COMMAND, IDENTIFYING_ELEMENT)

def search():
    desktop.press("searchButton")

def get_customer_name():
    return desktop.read("customerNameLabel")
```

Look for an identifying element rather than matching the window title.
Titles are translated — `Calculator` in English, `Calculatrice` in French —
while automation ids stay the same everywhere.

**3. Expose what you need.** Copy `api.py` and write the endpoints that make
sense for your program:

```python
@app.get("/customer")
async def customer(id: int):
    myapp.enter_id(id)
    myapp.search()
    return {"name": myapp.get_customer_name()}
```

## 📁 Project structure

```
no-api-creator/
├── desktop.py       drives any program: start, press, read, hide, show
├── calculator.py    the Windows Calculator, as an example of one program
├── api.py           the Calculator's 22 endpoints
├── cli.py           22 checks against a running server
└── tools/probe/     PowerShell scripts for exploring a program's controls
    ├── uia.ps1      list windows, dump the control tree
    ├── act.ps1      invoke a control, read a value
    └── screenshot.ps1
```

`tools/probe/` is not needed at runtime. It is how the button ids were found
in the first place, and how you would explore a program of your own.

## 🚧 Limits

**It is not fast.** In the example, `/add?a=2&b=3` takes 1.3–1.6 s and
`/add?a=1234567&b=1` takes 2.6–3.7 s. Each digit is a separate button press.

**One request at a time.** There is one window, and two requests pressing its
buttons at once would interleave. The endpoints are `async def` so requests
queue instead. That is inherent to driving a single UI, not a choice in the
code.

**One program at a time, per server.** `desktop.py` holds a single window.
Driving two programs at once means two servers, for now.

**It needs a desktop session.** The window is hidden, not headless, and the
program still appears in the taskbar and in Alt+Tab.

**Windows only, for now.** Linux publishes the same kind of description
through AT-SPI, which is the path to running this headless in CI under
`Xvfb`. That driver is not written yet — it would be a second `desktop.py`,
and nothing above it would change.
