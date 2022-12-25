import sys
import pathlib

sys.path.extend([str(pathlib.Path(__file__).parent.parent)])
from habits.models import db, BaseModel
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create', action='store_true')
    parser.add_argument('-d', '--drop', action='store_true')
    args = parser.parse_args()
    if not args and not args.drop:
        raise argparse.ArgumentTypeError('must specify --create or --drop')

    return args


def main():
    args = parse_args()

    if args.drop:
        drop_tables()

    if args.create:
        create_tables()


def drop_tables():
    with db:
        db.drop_tables(BaseModel.__subclasses__())


def create_tables():
    with db:
        db.create_tables(BaseModel.__subclasses__())


if __name__ == '__main__':
    main()
