"""
This module initializes the FastAPI router for the example endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/example", tags=["example"])

# The reason we're doing additional imports all the way down here is because router needs to be defined first.
# This helps us avoid circular imports by abusing Python's order-of-execution semantics; making our lives considerably
# easier in the process.  This is going to make isort mad if we ever decide to adopt it.
from . import hello
from . import ping
from . import error
from . import echo
