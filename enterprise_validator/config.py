"""Enterprise Validator Configuration"""

BASE_URL = "http://127.0.0.1:8000"

ROUTES = [
    "/",
    "/hotels/",
    "/buses/",
    "/cabs/",
    "/packages/"
]

REQUIRED_HEADER_LINKS = [
    "Hotels",
    "Buses",
    "Cabs",
    "Packages",
    "Flights",
    "Trains",
    "Login",
    "Register"
]

MAX_LOAD_MS = 2000
VISUAL_THRESHOLD = 6
