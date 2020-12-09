import argparse
import sys

print(sys.argv[1:])


parser = argparse.ArgumentParser()
parser.add_argument("--exit", type=int, default=0)


args, unparsed = parser.parse_known_args()
sys.exit(args.exit)
