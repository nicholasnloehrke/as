import argparse
from parser import Parser


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("infile", help="Input file")
    argparser.add_argument("-o", help="Output file")
    args = argparser.parse_args()

    with open(args.infile) as f:
        code = f.read()

    try:
        ast = Parser().parse(code)
        for line in ast:
            print(line)
    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    main()
