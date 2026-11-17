import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import canvas


def safe_name(name):
    # replace characters Windows doesn't allow in file/folder names, and trailing dots/spaces
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(".")
    return name or "_"


def _status(error):
    # HTTPError.response is typed "Response | None"; raise_for_status() always sets it,
    # but checking keeps the type checker happy and avoids a crash if it's ever missing
    return error.response.status_code if error.response is not None else "unknown"


def folder_paths(folders):
    # turn Canvas folders into relative paths: {folder_id: Path("Lectures/Week 1")}
    # the root folder ("course files") becomes Path(), i.e. the course folder itself
    by_id = {f["id"]: f for f in folders}
    paths = {}

    def path_of(folder_id):
        if folder_id not in paths:
            folder = by_id[folder_id]
            parent_id = folder.get("parent_folder_id")
            if parent_id is None:
                paths[folder_id] = Path()
            elif parent_id in by_id:
                paths[folder_id] = path_of(parent_id) / safe_name(folder["name"])
            else:  # parent not visible to you: put it at the top level
                paths[folder_id] = Path(safe_name(folder["name"]))
        return paths[folder_id]

    for folder_id in by_id:
        path_of(folder_id)
    return paths


class CloneError(Exception):
    # a course can't be cloned (not found, files closed, ...); the message explains why
    pass


@dataclass
class CoursePlan:
    # everything needed to download one course, plus its counters
    code: str
    name: str
    dest: Path
    label: str  # dest relative to the current folder, e.g. "Fall_2026/CS201-1"
    downloads: list = field(default_factory=list)  # (url, full path, relative path)
    up_to_date: int = 0
    locked: int = 0
    downloaded: int = 0
    failed: int = 0

    def summary(self):
        return (
            f"{self.downloaded} downloaded, {self.up_to_date} already up to date, "
            f"{self.locked} locked, {self.failed} failed"
        )


def _plan_course(course_id, parent):
    # get a course's folders and files, recreate the folders, and decide which files to download
    # the course folder goes inside "parent" (the current folder, or a semester folder)
    try:
        course = canvas.get_course(course_id)
    except requests.HTTPError as e:
        if _status(e) == 401:
            raise  # wrong token: stop everything, cli explains how to fix it
        raise CloneError(f"Course {course_id} not found or not accessible (HTTP {_status(e)})")

    try:
        folders = canvas.get_folders(course_id)
        files = canvas.get_files(course_id)
    except requests.HTTPError as e:
        raise CloneError(
            f"Canvas doesn't allow access to the files of {course.get('course_code', course_id)} "
            f"(HTTP {_status(e)})"
        )

    # the course gets its own folder, like "git clone"
    code = safe_name(course.get("course_code") or str(course_id))
    dest = parent / code
    label = dest.relative_to(Path.cwd()).as_posix()
    plan = CoursePlan(code=code, name=course.get("name", code), dest=dest, label=label)
    paths = folder_paths(folders)

    # recreate every folder, even empty ones (parents=True also creates the semester folder)
    try:
        plan.dest.mkdir(parents=True, exist_ok=True)
        for path in paths.values():
            (plan.dest / path).mkdir(parents=True, exist_ok=True)
    except OSError as e:  # no permission, a file with the same name as a folder, ...
        raise CloneError(f"Couldn't create the folders of {plan.label}: {e}")

    # decide which files to download
    for file in files:
        if file.get("locked_for_user") or not file.get("url"):
            plan.locked += 1
            continue
        relative = paths.get(file["folder_id"], Path()) / safe_name(file["display_name"])
        target = plan.dest / relative
        if target.exists() and target.stat().st_size == file.get("size"):
            plan.up_to_date += 1  # already downloaded on a previous run
            continue
        plan.downloads.append((file["url"], target, relative))
    return plan


def _download(plans):
    # download the files of every plan through ONE shared pool, so there are never
    # more than MAX_WORKERS downloads at once, no matter how many courses
    pool = ThreadPoolExecutor(max_workers=canvas.MAX_WORKERS)
    jobs = {}  # {job: (plan, relative path)}
    try:
        for plan in plans:
            for url, target, relative in plan.downloads:
                jobs[pool.submit(canvas.download_file, url, target)] = (plan, relative)
        for job in as_completed(jobs):
            plan, relative = jobs[job]
            shown = f"{plan.label}/{relative.as_posix()}"  # full path from the current folder
            try:
                job.result()
                plan.downloaded += 1
                print(f"  {shown}")
            except Exception as e:
                plan.failed += 1
                print(f"  FAILED {shown}: {e}")
    finally:
        # on Ctrl+C: drop the downloads that haven't started yet, wait for the running ones
        for job in jobs:
            job.cancel()
        pool.shutdown(wait=True)


def semester_folder_name(term):
    # "Fall 2026" -> "Fall_2026"
    return safe_name(term["name"]).replace(" ", "_")


def clone(semester_ids, course_ids):  # called by cli
    # what to clone: (course ID, folder to put the course in, name to show if it's skipped)
    targets = []

    # -s: every course of each semester, inside a folder for that semester
    if semester_ids:
        all_courses = canvas.get_courses()
        unknown = []
        for semester_id in dict.fromkeys(semester_ids):  # removes repeated IDs, keeps the order
            courses = [c for c in all_courses if (c.get("term") or {}).get("id") == semester_id]
            if not courses:
                unknown.append(str(semester_id))
                continue
            folder = Path.cwd() / semester_folder_name(courses[0]["term"])
            for course in sorted(courses, key=lambda c: c.get("course_code", "")):
                code = safe_name(str(course.get("course_code") or course["id"]))
                targets.append((course["id"], folder, f"{folder.name}/{code}"))
        # a typo stops everything before anything is downloaded
        if unknown:
            raise CloneError(f"No courses found for semester {', '.join(unknown)} (see: canvasdl show semesters)")

    # -c: single courses, right in the current folder
    for course_id in dict.fromkeys(course_ids):
        targets.append((course_id, Path.cwd(), str(course_id)))

    # 1. get every course's folders and file list at the same time; a course that fails is skipped
    plans, skipped = [], []
    with ThreadPoolExecutor(max_workers=canvas.MAX_WORKERS) as pool:
        futures = [(name, pool.submit(_plan_course, course_id, folder)) for course_id, folder, name in targets]
        for name, future in futures:
            try:
                plans.append(future.result())
            except CloneError as e:
                skipped.append((name, str(e)))

    if not plans:  # nothing can be cloned: show why and exit with an error
        raise CloneError("\n".join(reason for _, reason in skipped))

    for plan in plans:
        print(f"Cloning {plan.name} into {plan.label}")
    for _, reason in skipped:
        print(f"Skipped: {reason}")
    print()

    # 2. download the files of all courses together
    _download(plans)

    print("\nDone:")
    for plan in plans:
        print(f"  {plan.label}: {plan.summary()}")
    print(f"\n{len(plans)} of {len(targets)} courses cloned")
    if skipped:
        print(f"Skipped: {', '.join(name for name, _ in skipped)}")
