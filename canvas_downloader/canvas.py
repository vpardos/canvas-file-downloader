import requests

from . import config, credentials

def _auth():
    token = credentials.load_token()
    domain = config.load_domain()
    if not token:
        raise SystemExit("No token saved.\nPlease run: canvasdl token set")
    if not domain:
        raise SystemExit("No Canvas domain configured.\nPlease run: canvasdl domain set")
    return domain, {"Authorization": f"Bearer {token}"}


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


def get_courses():
    # /courses hides most past courses, so start from enrollments instead
    enrollments = _get_all("/users/self/enrollments", {"state[]": "current_and_concluded"})
    course_ids = sorted({e["course_id"] for e in enrollments})
    return [_get(f"/courses/{cid}", {"include[]": "term"}) for cid in course_ids]


def get_semesters():  # called by cli
    courses = get_courses()
    semesters = {}
    for course in courses:
        term = course.get("term")
        if term:
            semesters[term["id"]] = {"id": term["id"], "name": term["name"]}
    return sorted(semesters.values(), key=lambda s: s["id"], reverse=True)
