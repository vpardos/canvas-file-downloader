from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests

from . import config, credentials

MAX_WORKERS = 8  # how many requests run at the same time


@lru_cache  # read the token and domain once, then reuse them for every request
def _auth():
    token = credentials.load_token()
    domain = config.load_domain()
    if not token:
        raise SystemExit("No token saved.\nPlease run: canvasdl token set")
    if not domain:
        raise SystemExit("No Canvas domain configured.\nPlease run: canvasdl domain set")
    return domain, {"Authorization": f"Bearer {token}"}


def error_message(error):  # called by cli
    # turn a failed request into a short explanation of what to do
    if isinstance(error, requests.HTTPError) and error.response is not None:
        status = error.response.status_code
        if status == 400:
            # Canvas answers 400 when the token contains invisible characters (e.g. saved by older versions)
            return (
                "Canvas rejected the request (HTTP 400). Your saved token is probably damaged.\n"
                "Run: canvasdl token delete, then: canvasdl token set"
            )
        if status == 401:
            return "Canvas rejected your token (HTTP 401). It may be wrong or expired.\nCreate a new one and run: canvasdl token set"
        if status == 403 and "Rate Limit Exceeded" in error.response.text:
            return "Canvas is limiting your requests (rate limit). Wait a minute and try again."
        if status == 404:
            return f"Not found on Canvas (HTTP 404): {error.response.url}\nCheck your domain: canvasdl domain set"
        if status >= 500:
            return f"Canvas had an internal error (HTTP {status}). Try again later."
        return f"Canvas request failed (HTTP {status}): {error.response.url}"
    if isinstance(error, requests.ConnectionError):
        return "Couldn't connect to Canvas. Check your internet connection and your domain (canvasdl domain set)."
    if isinstance(error, requests.Timeout):
        return "Canvas took too long to answer. Try again later."
    if isinstance(error, requests.exceptions.JSONDecodeError):
        return "Canvas sent an unexpected answer. Check your domain: canvasdl domain set"
    if isinstance(error, (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema)):
        return "Your Canvas domain is not a valid address. Run: canvasdl domain set"
    return f"Canvas request failed: {error}"


def _get(path, params=None):
    # GET a single Canvas object (not a list)
    domain, headers = _auth()
    response = requests.get(f"{domain}/api/v1{path}", headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _get_all(path, params=None):
    # GET every page of a Canvas API list endpoint.
    domain, headers = _auth()

    url = f"{domain}/api/v1{path}"
    params = {"per_page": 100, **(params or {})}
    results = []
    while url:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        results.extend(response.json())
        url = response.links.get("next", {}).get("url")  # next page, if any
        params = None  # the "next" URL already includes the parameters
    return results


def get_courses():  # called by cli
    # /courses hides most past courses, so start from enrollments instead
    enrollments = _get_all("/users/self/enrollments", {"state[]": "current_and_concluded"})
    course_ids = sorted({e["course_id"] for e in enrollments})

    def get_course(cid):
        return _get(f"/courses/{cid}", {"include[]": "term"})

    # fetch the courses in parallel; map() keeps the results in the same order as course_ids
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        return list(pool.map(get_course, course_ids))


def get_semesters():  # called by cli
    courses = get_courses()
    semesters = {}
    for course in courses:
        term = course.get("term")
        if term:
            semesters[term["id"]] = {"id": term["id"], "name": term["name"]}
    return sorted(semesters.values(), key=lambda s: s["id"], reverse=True)


def get_course(course_id):  # called by clone
    return _get(f"/courses/{course_id}")


def get_folders(course_id):  # called by clone
    # every folder in the course (flat list; each one knows its parent_folder_id)
    return _get_all(f"/courses/{course_id}/folders")


def get_files(course_id):  # called by clone
    # every file in the course, from all folders (each one knows its folder_id)
    return _get_all(f"/courses/{course_id}/files")


def download_file(url, path):  # called by clone
    # download to "<name>.part" first, so an interrupted download never looks like a finished file
    _, headers = _auth()
    part = path.with_name(path.name + ".part")
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(part, "wb") as f:
                # writes each 64 KB chunk as it arrives (writelines adds no newlines)
                f.writelines(response.iter_content(chunk_size=64 * 1024))
        part.replace(path)
    finally:
        part.unlink(missing_ok=True)  # only exists if something failed
