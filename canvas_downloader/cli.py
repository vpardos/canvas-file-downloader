import argparse
import getpass
import sys

from . import __version__, canvas, config, credentials


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
        domain = "https://" + domain  # accept "cursos.canvas.uc.cl" without the https://
    config.save_domain(domain)
    print(f"Canvas domain set to {config.load_domain()}")


def cmd_show_courses(args):
    courses = canvas.get_courses()
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
    domain_set_parser.add_argument("domain", help="e.g. https://cursos.canvas.uc.cl")
    domain_set_parser.set_defaults(func=cmd_domain_set)

    # show
    show = commands.add_parser("show", help="show information from Canvas")
    show_actions = show.add_subparsers(dest="action", required=True)
    # -
    show_courses_parser = show_actions.add_parser("courses", help="list your courses grouped by semester")
    show_courses_parser.set_defaults(func=cmd_show_courses)

    show_semesters_parser = show_actions.add_parser("semesters", help="list your semesters and their IDs")
    show_semesters_parser.set_defaults(func=cmd_show_semesters)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (KeyboardInterrupt, EOFError):  # Ctrl + C
        print("\nCancelled.")
        sys.exit(130)
