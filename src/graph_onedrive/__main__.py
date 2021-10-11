"""Entrypoint module redirects to command line interface, in case of use of `python -m graphonedrive`.
"""
import sys

from graph_onedrive._cli import main

if __name__ == "__main__":
    sys.exit(main())
