
import difflib
import sys


def main() -> None:
    created = sys.argv[1]
    reference = created.replace('.hack', '.orig.hack')
    with open(created, 'r') as f:
        orig = f.readlines()
    with open(reference, 'r') as f:
        ref = f.readlines()

    print(f'file: {created}')
    for line in difflib.unified_diff(orig, ref, 'created', 'reference', '', '', lineterm=''):
        print(line, end='')


if __name__ == '__main__':
    main()

# unified_diff('one two three four'.split(), 'zero one tree four'.split(), 'Original', 'Current', '', '', lineterm='')
# >>> for line in iter:
# ...     print(line)
