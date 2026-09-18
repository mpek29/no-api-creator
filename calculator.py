"""Everything this project knows about the Windows Calculator.

This is the example of how to describe one program. It holds the names of
the Calculator's buttons and nothing else: the work of opening a window and
pressing things lives in desktop.py, which knows about no program at all.

    import calculator

    calculator.start()
    calculator.enter_number(2)
    calculator.plus()
    calculator.enter_number(3)
    calculator.equals()
    print(calculator.get_result())      # 5.0

To drive a different program, copy this file and change the names.
"""

import locale

import desktop

# Read the number format of this computer, so get_result() knows whether the
# decimal separator is a dot (English) or a comma (French).
locale.setlocale(locale.LC_ALL, "")

# What to run if the Calculator is not open yet.
LAUNCH_COMMAND = "calc.exe"

# Only the Calculator has a number pad with this name. We look for it instead
# of the window title, because the title is translated: "Calculator" in
# English, but "Calculatrice" in French.
IDENTIFYING_ELEMENT = "NumberPad"

# Something to wait for before saying the Calculator is ready to be used.
READY_ELEMENT = "equalButton"

# The screen, which is a sentence rather than a number.
DISPLAY = "CalculatorResults"
EXPRESSION = "CalculatorExpression"


def start():
    """Open the Calculator and get it ready. Call this first."""
    return desktop.start(LAUNCH_COMMAND, IDENTIFYING_ELEMENT, READY_ELEMENT)


# ---------------------------------------------------------------------------
# Numbers
#
# There is no function per digit. Use enter_number(27), which presses 2 then
# 7 for you, or digit(7) for a single one.
# ---------------------------------------------------------------------------

def decimal_point():
    """Press the decimal point."""
    desktop.press("decimalSeparatorButton")


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def plus():
    """Press +."""
    desktop.press("plusButton")


def minus():
    """Press -."""
    desktop.press("minusButton")


def multiply():
    """Press x."""
    desktop.press("multiplyButton")


def divide():
    """Press /."""
    desktop.press("divideButton")


def equals():
    """Press = to get the answer."""
    desktop.press("equalButton")


def reciprocal():
    """Press 1/x."""
    desktop.press("invertButton")


def square():
    """Press x squared."""
    desktop.press("xpower2Button")


def square_root():
    """Press the square root button."""
    desktop.press("squareRootButton")


def percent():
    """Press %."""
    desktop.press("percentButton")


def negate():
    """Press +/- to switch between positive and negative."""
    desktop.press("negateButton")


# ---------------------------------------------------------------------------
# Erasing
# ---------------------------------------------------------------------------

def clear():
    """Press C to erase everything."""
    desktop.press("clearButton")


def clear_entry():
    """Press CE to erase only the number being typed."""
    desktop.press("clearEntryButton")


def backspace():
    """Erase the last digit typed."""
    desktop.press("backSpaceButton")


# ---------------------------------------------------------------------------
# Memory
#
# These five buttons are spelled differently from all the others: some start
# with a capital letter. The spelling has to match exactly.
# ---------------------------------------------------------------------------

def memory_store():
    """Press MS to save the displayed number."""
    desktop.press("memButton")


def memory_recall():
    """Press MR to bring back the saved number."""
    desktop.press("MemRecall")


def memory_add():
    """Press M+ to add the displayed number to the saved one."""
    desktop.press("MemPlus")


def memory_subtract():
    """Press M- to subtract the displayed number from the saved one."""
    desktop.press("MemMinus")


def memory_clear():
    """Press MC to forget the saved number."""
    desktop.press("ClearMemoryButton")


# ---------------------------------------------------------------------------
# Typing a whole number
#
# There is no button for 27. You press 2, then 7. These two functions do
# that for you.
# ---------------------------------------------------------------------------

def digit(n):
    """Press a single digit, given as a number from 0 to 9."""
    if n < 0 or n > 9:
        raise ValueError("A digit must be between 0 and 9, not " + str(n))

    desktop.press("num" + str(n) + "Button")


def enter_number(value):
    """Press every digit of a number, one after the other."""
    text = str(value)

    # 2.0 and 2 are the same number, so do not waste two button presses on
    # the ".0" at the end.
    if text.endswith(".0"):
        text = text[:-2]

    # lstrip("-") gives the number without its minus sign, if it has one.
    for character in text.lstrip("-"):
        if character == ".":
            decimal_point()
        else:
            digit(int(character))

    # There is no minus key for typing a negative number, so we type the
    # number first and then flip its sign.
    if text.startswith("-"):
        negate()


# ---------------------------------------------------------------------------
# Reading the answer
# ---------------------------------------------------------------------------

def get_result():
    """Return the number currently displayed.

    The Calculator describes its screen with a whole sentence, meant to be
    read aloud to blind users: "Display is 5", or "L'affichage est 5" in
    French. This function pulls the number out of that sentence and returns
    it as a normal number.
    """
    text = desktop.read(DISPLAY)

    # This computer writes decimals with a dot or with a comma, depending on
    # its language settings. Whichever it is, we turn it into a dot, because
    # that is what Python understands.
    separator = locale.localeconv()["decimal_point"]

    # Keep the digits, the minus sign and the decimal separator. Everything
    # else is thrown away: the words of the sentence, and the spaces or
    # commas used to group big numbers like 1 234 567.
    number = ""
    for character in text:
        if character.isdigit() or character == "-":
            number += character
        elif character == separator:
            number += "."

    # Sometimes the screen shows a message instead of a number, for example
    # after dividing by zero. Then there are no digits to return.
    if number.strip("-") == "":
        raise RuntimeError(text)

    return float(number)


def get_expression():
    """Return the calculation in progress, as the Calculator describes it."""
    return desktop.read(EXPRESSION)
