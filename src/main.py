import sys
from src.interfaces.cli import app as cli_app

if __name__ == "__main__":
    cli_app(prog_name="qbr-pipeline", args=sys.argv[1:])
