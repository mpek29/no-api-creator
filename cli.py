"""Check that the Calculator API gives the right answers.

First start the server in one terminal:

    uvicorn api:app

Then run this in another:

    python cli.py

Every line it prints is one question asked to the API, and whether the
answer was the expected one.
"""

import sys

import requests

ADDRESS = "http://127.0.0.1:8000"

# Counters, so we can print a summary at the end.
passed = 0
failed = 0


def check(path, expected, method="GET"):
    """Ask the API one question and say whether the answer was right.

    path     the part of the address after the port, like "/add?a=2&b=3"
    expected the number we should get back
    """
    global passed, failed

    answer = requests.request(method, ADDRESS + path, timeout=60).json()

    # Successful answers look like {"result": 5.0} or {"memory": 10.0}.
    # Failed ones look like {"detail": "..."}.
    got = answer.get("result", answer.get("memory", answer.get("detail")))

    if got == expected:
        passed += 1
        print("  ok    %-28s = %s" % (path, got))
    else:
        failed += 1
        print("  FAIL  %-28s = %s   (expected %s)" % (path, got, expected))


def check_code(path, expected_code, method="GET"):
    """Check the API answers with the right code, not just any code.

    It matters which refusal you get. 404 means "there is no such thing",
    while 400 means "it exists but not right now". A client can retry the
    second one after storing a number; there is no point retrying the first.

    200 the request worked
    400 the Calculator cannot do that, or the button is greyed out
    404 there is no button with that name
    422 what you sent was not a number
    """
    global passed, failed

    response = requests.request(method, ADDRESS + path, timeout=60)
    detail = response.json().get("detail", "") if response.status_code >= 400 else ""

    if response.status_code == expected_code:
        passed += 1
        print("  ok    %-28s %s %s" % (path, expected_code, detail))
    else:
        failed += 1
        print("  FAIL  %-28s answered %s, expected %s"
              % (path, response.status_code, expected_code))


print("Asking the Calculator API at", ADDRESS)
print()

print("Adding and subtracting")
check("/add?a=2&b=3", 5.0)
check("/add?a=15.5&b=0.25", 15.75)
check("/add?a=-42&b=2", -40.0)
check("/add?a=1234567&b=1", 1234568.0)
check("/subtract?a=8&b=3", 5.0)

print()
print("Multiplying and dividing")
check("/multiply?a=7&b=6", 42.0)
check("/divide?a=9&b=4", 2.25)

print()
print("The other keys")
check("/square?a=12", 144.0)
check("/square_root?a=81", 9.0)
check("/reciprocal?a=8", 0.125)
check("/percent?a=200&b=50", 100.0)

print()
print("Memory, which the Calculator keeps between requests")
check("/memory/store?value=10", 10.0, method="POST")
check("/memory/add?value=5", 15.0, method="POST")
check("/memory/subtract?value=3", 12.0, method="POST")
check("/memory", 12.0)
check("/memory/clear", None, method="POST")

print()
print("Saying no, with the right kind of no")
check_code("/divide?a=1&b=0", 400)                      # the Calculator refuses
check_code("/memory", 400)                              # memory is empty, MR greyed out
check_code("/add?a=hello&b=3", 422)                     # that is not a number
check_code("/press/nopeButton", 404, "POST")            # no button by that name

# These last two are the same button, one press apart. The first works, the
# second is refused because pressing MC greys it out again. They must not
# give the same code, and they must not both be 404: the button plainly
# exists, so "not found" would send a client looking for the wrong problem.
check_code("/press/ClearMemoryButton", 400, "POST")     # exists, but greyed out
check_code("/press/num7Button", 200, "POST")            # exists and works

print()
print("%d passed, %d failed" % (passed, failed))

# Exit with an error if anything failed, so this can be used in a CI later.
if failed:
    sys.exit(1)
