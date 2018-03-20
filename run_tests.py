__author__ = 'welwu'


from cli import parser
from context import CIContext


def main():
    args = parser.parse_args()
    with CIContext(args) as test:
        test.execute()


if __name__ == '__main__':
    main()

