import argparse
import getpass
import sys

from . import credentials


def cmd_save_token(args):
    token = getpass.getpass("Canvas API token: ").strip()
    if not token:
        print("No token entered, nothing was saved")
        return
    where = credentials.save_token(token)
    print(f"Token saved to {where}")


def build_parser():
    parser = argparse.ArgumentParser(prog="canvasdl")
    commands = parser.add_subparsers(dest="command", required=True)

    token = commands.add_parser("token", help="save your Canvas API token")
    token.set_defaults(func=cmd_save_token)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (KeyboardInterrupt, EOFError):  # Ctrl + C
        print("\nCancelled.")
        sys.exit(130)
