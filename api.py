"""A web API for the Windows Calculator.

This turns the Calculator, which has no API at all, into one. Every request
presses the real buttons of the real Calculator and reads the real answer.

Start the server with:

    uvicorn api:app

Then try it in a browser:

    http://127.0.0.1:8000/add?a=2&b=3
    http://127.0.0.1:8000/docs
"""

import fastapi

import calculator
import desktop

app = fastapi.FastAPI(
    title="Calculator API",
    description="A REST API for a program that never had one.",
)

# Open the Calculator once, when the server starts, and move it out of sight.
# It stays open and answers every request.
calculator.start()
desktop.hide()


def answer():
    """Read the number on screen, or explain why there is not one."""
    try:
        return calculator.get_result()
    except RuntimeError as problem:
        # For example after dividing by zero, where the Calculator shows a
        # message instead of a number. 400 means "your request was wrong".
        raise fastapi.HTTPException(status_code=400, detail=str(problem))


def do(action):
    """Press a button, and turn any complaint into a web error.

    A button can refuse to be pressed: the memory buttons are greyed out
    until a number has been stored, for example.
    """
    try:
        action()
    except RuntimeError as problem:
        raise fastapi.HTTPException(status_code=400, detail=str(problem))


def calculate(first, operation, second):
    """Do what a person would do: type a number, press a key, type another."""
    calculator.clear()
    calculator.enter_number(first)
    operation()
    calculator.enter_number(second)
    calculator.equals()
    return answer()


# Every function below is written with "async def" on purpose. It makes the
# server deal with one request at a time, which is what we need: there is only
# one Calculator, and two requests pressing its buttons at once would mix up
# their numbers.


@app.get("/")
async def home():
    """Say what this server can do."""
    return {
        "this is": "a REST API for the Windows Calculator",
        "try": "/add?a=2&b=3",
        "documentation": "/docs",
    }


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

@app.get("/add")
async def add(a: float, b: float):
    """Add two numbers."""
    return {"result": calculate(a, calculator.plus, b)}


@app.get("/subtract")
async def subtract(a: float, b: float):
    """Subtract the second number from the first."""
    return {"result": calculate(a, calculator.minus, b)}


@app.get("/multiply")
async def multiply(a: float, b: float):
    """Multiply two numbers."""
    return {"result": calculate(a, calculator.multiply, b)}


@app.get("/divide")
async def divide(a: float, b: float):
    """Divide the first number by the second."""
    return {"result": calculate(a, calculator.divide, b)}


@app.get("/square")
async def square(a: float):
    """Multiply a number by itself."""
    calculator.clear()
    calculator.enter_number(a)
    calculator.square()
    return {"result": answer()}


@app.get("/square_root")
async def square_root(a: float):
    """Give the square root of a number."""
    calculator.clear()
    calculator.enter_number(a)
    calculator.square_root()
    return {"result": answer()}


@app.get("/reciprocal")
async def reciprocal(a: float):
    """Give one divided by the number."""
    calculator.clear()
    calculator.enter_number(a)
    do(calculator.reciprocal)
    return {"result": answer()}


@app.get("/percent")
async def percent(a: float, b: float):
    """Give b percent of a. For example a=200 and b=50 gives 100."""
    calculator.clear()
    calculator.enter_number(a)
    calculator.multiply()
    calculator.enter_number(b)
    calculator.percent()
    calculator.equals()
    return {"result": answer()}


# ---------------------------------------------------------------------------
# Reading and erasing what is on screen
# ---------------------------------------------------------------------------

@app.get("/result")
async def result():
    """Read whatever the Calculator is showing right now."""
    return {"result": answer()}


@app.get("/expression")
async def expression():
    """Read the calculation in progress, as the Calculator describes it."""
    return {"expression": calculator.get_expression()}


@app.post("/clear")
async def clear():
    """Press C to erase everything."""
    do(calculator.clear)
    return {"result": answer()}


@app.post("/clear_entry")
async def clear_entry():
    """Press CE to erase only the number being typed."""
    do(calculator.clear_entry)
    return {"result": answer()}


@app.post("/backspace")
async def backspace():
    """Erase the last digit typed."""
    do(calculator.backspace)
    return {"result": answer()}


# ---------------------------------------------------------------------------
# Memory
#
# The Calculator remembers one number between requests, all on its own. This
# is the closest it gets to storing something like a real backend would.
# ---------------------------------------------------------------------------

@app.get("/memory")
async def memory_recall():
    """Bring the saved number back onto the screen and return it."""
    do(calculator.memory_recall)
    return {"memory": answer()}


@app.post("/memory/store")
async def memory_store(value: float):
    """Save a number into the memory, replacing what was there."""
    calculator.clear()
    calculator.enter_number(value)
    do(calculator.memory_store)
    return {"memory": value}


@app.post("/memory/add")
async def memory_add(value: float):
    """Add a number to the one already saved."""
    calculator.clear()
    calculator.enter_number(value)
    do(calculator.memory_add)
    calculator.clear()
    do(calculator.memory_recall)
    return {"memory": answer()}


@app.post("/memory/subtract")
async def memory_subtract(value: float):
    """Subtract a number from the one already saved."""
    calculator.clear()
    calculator.enter_number(value)
    do(calculator.memory_subtract)
    calculator.clear()
    do(calculator.memory_recall)
    return {"memory": answer()}


@app.post("/memory/clear")
async def memory_clear():
    """Forget the saved number."""
    do(calculator.memory_clear)
    return {"memory": None}


# ---------------------------------------------------------------------------
# The window itself
#
# There is deliberately no endpoint that closes the Calculator. It would
# leave the server with nothing to press, and every later request would fail.
# ---------------------------------------------------------------------------

@app.post("/window/show")
async def window_show():
    """Put the Calculator back on the screen, to watch it working."""
    do(desktop.show)
    return {"window": "visible"}


@app.post("/window/hide")
async def window_hide():
    """Move the Calculator off the screen again."""
    do(desktop.hide)
    return {"window": "hidden"}


# ---------------------------------------------------------------------------
# Anything else
# ---------------------------------------------------------------------------

@app.post("/press/{button_id}")
async def press(button_id: str):
    """Press any button by its name, for anything the API does not cover.

    For example /press/num7Button presses the 7 key.
    """
    # Look for the button first. If there is no such name, that is a 404:
    # the thing you asked for does not exist.
    try:
        desktop.find(button_id)
    except RuntimeError as problem:
        raise fastapi.HTTPException(status_code=404, detail=str(problem))

    # It exists, so anything that goes wrong now is about its state and not
    # its name. A greyed out button is a 400, like everywhere else.
    do(lambda: desktop.press(button_id))

    return {"pressed": button_id, "showing": desktop.read(calculator.DISPLAY)}
