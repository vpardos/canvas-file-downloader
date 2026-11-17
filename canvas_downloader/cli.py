import argparse
import getpass
import io
import os
import sys
from urllib.parse import urlparse

import requests

from . import __version__, canvas, clone, config, credentials


def cmd_token_set(args):
    token = getpass.getpass("Canvas API token: ").strip()
    if not token:
        print("No token entered, nothing was saved")
        return
    where = credentials.save_token(token)
    print(f"Token saved to {where}")


def cmd_token_delete(args):
    removed = credentials.delete_token()
    if not removed:
        print("No saved token found")
    for place in removed:
        print(f"Token deleted from {place}")


def cmd_domain_set(args):
    domain = args.domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain  # accept "yourschool.instructure.com" without the https://

    # keep only "https://host", so pasting a full Canvas link (".../courses/123") also works
    parts = urlparse(domain)
    if "." not in parts.netloc or " " in parts.netloc:
        raise SystemExit(f"'{args.domain}' doesn't look like a web address, e.g. https://yourschool.instructure.com")
    domain = f"{parts.scheme}://{parts.netloc}"
    config.save_domain(domain)
    print(f"Canvas domain set to {config.load_domain()}")


def cmd_show_courses(args):
    courses = canvas.get_courses()

    # --semester: keep only courses from the given semester IDs
    if args.semester:
        courses = [c for c in courses if (c.get("term") or {}).get("id") in args.semester]

    if not courses:
        print("No courses found")
        return

    # group courses by semester: {(term_id, term_name): [course, ...]}
    by_semester = {}
    for course in courses:
        term = course.get("term") or {"id": 0, "name": "No semester"}
        by_semester.setdefault((term["id"], term["name"]), []).append(course)

    for (term_id, term_name), term_courses in sorted(by_semester.items(), reverse=True):
        print(f"\n{term_name} (semester ID {term_id})")
        for course in sorted(term_courses, key=lambda c: c.get("course_code", "")):
            print(f"  {course['id']:>6}  {course.get('course_code', '')}  {course.get('name', '')}")


def cmd_show_semesters(args):
    semesters = canvas.get_semesters()
    if not semesters:
        print("No semesters found")
        return
    for semester in semesters:
        print(f"{semester['id']:>6}  {semester['name']}")


def cmd_clone(args):
    # argparse can't require "at least one of -s / -c", so check it here (no default on purpose)
    if not args.semester and not args.course:
        args.parser.error("nothing to clone, use -s SEMESTER_ID and/or -c COURSE_ID")
    try:
        clone.clone(semester_ids=args.semester or [], course_ids=args.course or [])
    except clone.CloneError as e:
        raise SystemExit(str(e))  # print the reason and exit with code 1


def build_parser():
    parser = argparse.ArgumentParser(prog="canvasdl")
    commands = parser.add_subparsers(dest="command", required=True)

    # general
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # token
    token = commands.add_parser("token", help="manage Canvas API token")
    token_actions = token.add_subparsers(dest="action", required=True)
    # -
    token_set_parser = token_actions.add_parser("set", help="save API token")
    token_set_parser.set_defaults(func=cmd_token_set)

    token_delete_parser = token_actions.add_parser("delete", help="delete saved API token")
    token_delete_parser.set_defaults(func=cmd_token_delete)

    # domain
    domain = commands.add_parser("domain", help="manage Canvas domain")
    domain_actions = domain.add_subparsers(dest="action", required=True)
    # -
    domain_set_parser = domain_actions.add_parser("set", help="save Canvas domain")
    domain_set_parser.add_argument("domain", help="e.g. https://yourschool.instructure.com")
    domain_set_parser.set_defaults(func=cmd_domain_set)

    # show
    show = commands.add_parser("show", help="show information from Canvas")
    show_actions = show.add_subparsers(dest="action", required=True)
    # -
    show_courses_parser = show_actions.add_parser("courses", help="list your courses grouped by semester")
    show_courses_parser.add_argument(
        "-s", "--semester", type=int, nargs="+", metavar="ID",
        help="only show courses from these semester IDs (see: canvasdl show semesters)",
    )
    show_courses_parser.set_defaults(func=cmd_show_courses)

    show_semesters_parser = show_actions.add_parser("semesters", help="list your semesters and their IDs")
    show_semesters_parser.set_defaults(func=cmd_show_semesters)

    # clone
    clone_parser = commands.add_parser("clone", help="download semesters and/or courses into the current folder")
    clone_parser.add_argument(
        "-s", "--semester", type=int, nargs="+", metavar="ID",
        help="semester IDs to clone, each into its own folder (see: canvasdl show semesters)",
    )
    clone_parser.add_argument(
        "-c", "--course", type=int, nargs="+", metavar="ID",
        help="course IDs to clone into the current folder (see: canvasdl show courses)",
    )
    # parser=... lets cmd_clone show this command's usage when neither -s nor -c is given
    clone_parser.set_defaults(func=cmd_clone, parser=clone_parser)

    return parser


def main():
    # never crash on a character the terminal can't show (e.g. Windows output redirected to a file)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(errors="replace")

    args = build_parser().parse_args()
    try:
        args.func(args)
        sys.stdout.flush()  # write buffered output now, so a broken pipe is caught below
    except (KeyboardInterrupt, EOFError):  # Ctrl + C
        print("\nCancelled.")
        sys.exit(130)
    except BrokenPipeError:  # output piped into a command that stopped reading, e.g. "| head"
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())  # silence the final flush
        sys.exit(1)
    except requests.RequestException as e:  # no internet, wrong token or domain, Canvas errors
        sys.exit(canvas.error_message(e))
    except OSError as e:  # files and folders: permission denied, disk full, ...
        sys.exit(f"File error: {e}")
