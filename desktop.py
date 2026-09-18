"""Control any Windows program from Python.

This file knows nothing about any particular application. It can open a
program, find things inside its window, press them, read them, and move the
window out of sight. That is everything the rest of the project needs.

To drive a new program, you do not change this file. You write a small one
of your own, like calculator.py, that says which buttons to press.

Things are found by their "automation id". That is the name Windows gives a
control internally, the same one a screen reader uses. It stays in English
even when the program is displayed in another language, so it is safe to
write these ids in your code.
"""

import subprocess

import uiautomation

# The window we are controlling.
# start() puts the window here, and every other function uses it.
window = None

# How deep to look inside the window when searching for something.
SEARCH_DEPTH = 12

# How long to pause after pressing something, in seconds. The library we use
# waits half a second by default, which is comfortable for a human watching
# but very slow when a program presses hundreds of buttons. A short pause
# still leaves the program time to update its screen.
PAUSE_AFTER_PRESS = 0.05


def start(launch_command, identifying_element, ready_element=None):
    """Open a program and get it ready. Call this first.

    launch_command       what to run if the program is not open yet,
                         for example "myapp.exe"
    identifying_element  the automation id of something only this program
                         has. We look for that instead of the window title,
                         because titles are translated from one language to
                         the next while automation ids are not.
    ready_element        something to wait for before saying we are ready.
                         Just after opening, Windows sometimes replaces a
                         window with the real one, and without this we would
                         hand back a window that is about to disappear.
    """
    global window

    marker = uiautomation.Control(searchDepth=10, AutomationId=identifying_element)

    # Only open the program if it is not already running. Windows lets you
    # have several copies of some programs at once, so asking twice without
    # looking first opens two windows.
    if not marker.Exists(maxSearchSeconds=0):
        subprocess.Popen(launch_command, shell=True)
        if not marker.Exists(maxSearchSeconds=20):
            raise RuntimeError("This program did not open: " + launch_command)

    window = marker.GetTopLevelControl()

    if ready_element is not None:
        ready = window.Control(searchDepth=SEARCH_DEPTH, AutomationId=ready_element)
        if not ready.Exists(maxSearchSeconds=10):
            raise RuntimeError("The program opened but is not ready.")

    return window


def find(element_id):
    """Find one thing inside the window, by its automation id."""
    if window is None:
        raise RuntimeError("Call start() first.")

    element = window.Control(searchDepth=SEARCH_DEPTH, AutomationId=element_id)
    if not element.Exists(maxSearchSeconds=5):
        raise RuntimeError("There is nothing called " + element_id)

    return element


def press(element_id):
    """Press one thing, using its automation id.

    This does not move the mouse. It asks Windows to press the control
    directly, so you can keep using your computer while it runs.
    """
    element = find(element_id)

    # A greyed out control cannot be pressed. The Calculator's memory
    # buttons are greyed out until a number has been stored, for example.
    if not element.IsEnabled:
        raise RuntimeError("The button " + element_id + " is greyed out.")

    pattern = element.GetPattern(uiautomation.PatternId.InvokePattern)
    pattern.Invoke(waitTime=PAUSE_AFTER_PRESS)


def read(element_id):
    """Read the text shown by one thing in the window."""
    return find(element_id).Name


def hide():
    """Move the window off the screen so you cannot see it.

    The program keeps running and still answers. We move it away instead of
    minimizing it, because Windows pauses some minimized programs and then
    nothing inside them can be found any more.
    """
    if window is None:
        raise RuntimeError("Call start() first.")

    # Put the window far to the left of the screen, where nobody can see it.
    # The screen starts at 0, so -3000 is well outside it.
    size = window.BoundingRectangle
    window.MoveWindow(-3000, -3000, size.width(), size.height())


def show():
    """Bring the window back onto the screen, to watch what is happening."""
    if window is None:
        raise RuntimeError("Call start() first.")

    size = window.BoundingRectangle
    window.MoveWindow(100, 100, size.width(), size.height())
