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


def cmd_delete_token(args):
    removed = credentials.delete_token()
    if not removed:
        print("No saved token found")
    for place in removed:
        print(f"Token deleted from {place}")


def build_parser():
    parser = argparse.ArgumentParser(prog="canvasdl")
    commands = parser.add_subparsers(dest="command", required=True)

    token = commands.add_parser("token", help="manage Canvas API token")
    token_actions = token.add_subparsers(dest="action", required=True)
    # -
    token_set_parser = token_actions.add_parser("set", help="save API token")
    token_set_parser.set_defaults(func=cmd_save_token)

    token_delete_parser = token_actions.add_parser("delete", help="delete saved API token")
    token_delete_parser.set_defaults(func=cmd_delete_token)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (KeyboardInterrupt, EOFError):  # Ctrl + C
        print("\nCancelled.")
        sys.exit(130)
