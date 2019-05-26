import json
import os


def get_default_config():
    return {
        'database': {
            'host': '',
            'port': '',
            'user': '',
            'pw': ''
        }
    }


def create_default_config(config_filename):
    with open(config_filename, 'w') as f:
        json.dump(get_default_config(), f, indent=4)

    print('created new empty config file at "{}"'.format(config_filename))


def create_config_interactively():
    # TODO
    raise NotImplementedError('interactive config file creation not supported yet, upcoming feature in v.0.1')


def load_config(config_filename):
    try:
        with open(config_filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print('Exception occured ({}), run validate-config'.format(e))


def validate_config(config_filename):
    if not os.path.exists(config_filename):
        print('config file does not exist at location: {}'.format(config_filename))
        return False

    try:
        with open(config_filename, 'r') as f:
            config = json.load(f)
    except IOError as e:
        print('the config file could not be loaded: {}'.format(e))
        return False
    except Exception as e:
        print('error occurred during the reading of the config file: {}'.format(e))
        return False

    if 'database' not in config:
        print('database configuration is missing')
        return False

    for param in ['host', 'port', 'user', 'pw']:
        if param not in config['database']:
            print('database parameter "{}" is missing'.format(param))
            return False
