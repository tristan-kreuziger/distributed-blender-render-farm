import commandline
import log


_AUTHOR = 'Tristan Kreuziger'
_VERSION = '0.0.0'
_LICENSE = 'MIT'


def info():
    print('Distributed Blender render farm utility tool')
    print('-' * 20)
    print('Author: {}'.format(_AUTHOR))
    print('Version: {}'.format(_VERSION))
    print('License: {}'.format(_LICENSE))
    print('')


def main():
    info()

    args = commandline.parse_parameters()
    if args.version:
        print('Version: {}'.format(_VERSION))
    else:
        commandline.parse_and_execute_actions(args)


if __name__ == '__main__':
    main()
