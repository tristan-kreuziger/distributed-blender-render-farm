import commandline


_AUTHOR = 'Tristan Kreuziger'
_VERSION = '0.0.0'
_LICENSE = 'MIT'


def info():
    print('Distributed Blender render farm utility tool')
    print('-' * 20)
    print('Author: {}'.format(_AUTHOR))
    print('Version: {}'.format(_VERSION))
    print('License: {}'.format(_LICENSE))
    print('-' * 20)
    print('')


def main():
    info()
    commandline.parse_and_execute_actions(commandline.parse_parameters())


if __name__ == '__main__':
    main()
