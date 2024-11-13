# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
# ]
# ///

import click


@click.command()
def main():
    print("Hello, world!")


if __name__ == "__main__":
    main()
