import json
import os
import logging


def get_default_config():
    return {
        'general': {
            'machine_name': 'computer',
            'input_path': '',
            'output_path': 'render_images',
            'output_prefix': '',
            'blender_path': ''
        },
        'database': {
            'host': '',
            'port': '',
            'user': '',
            'pw': '',
            'db': ''
        },
        'dropbox': {
            'access_token': '',
            'folder_name': ''
        },
        'render': {
            'frames_per_task': 5
        }
    }


def create_default_config(config_filename):
    with open(config_filename, 'w', encoding='utf8') as f:
        json.dump(get_default_config(), f, indent=4)

    logging.info('Created new default config file at "{}".'.format(config_filename))


def create_config_interactively(config_filename):
    # TODO
    raise NotImplementedError('Interactive config file creation not supported yet, upcoming feature in v.0.1.0')


def load_config(config_filename):
    try:
        with open(config_filename, 'r', encoding='utf8') as f:
            return json.load(f)
    except Exception as e:
        logging.critical('Exception occured ({}), run validate-config'.format(e))


def validate_config(config_filename):
    if not os.path.exists(config_filename):
        logging.error('The given config file ("{}") does not exist.'.format(config_filename))
        return False

    try:
        with open(config_filename, 'r') as f:
            config = json.load(f)
    except IOError as e:
        logging.critical('The config file ("{}") could not be loaded: {}'.format(config_filename, e))
        return False
    except Exception as e:
        logging.critical('An error occurred during the reading of the config file: {}'.format(e))
        return False

    if 'general' not in config:
        logging.error('General configuration is missing.')
        return False

    for param in ['machine_name', 'input_path', 'output_path', 'output_prefix', 'blender_path']:
        if param not in config['general']:
            logging.error('General parameter "{}" is missing.'.format(param))
            return False

    if 'database' not in config:
        logging.error('Database configuration is missing.')
        return False

    for param in ['host', 'port', 'user', 'pw', 'port']:
        if param not in config['database']:
            logging.error('Database parameter "{}" is missing.'.format(param))
            return False

    if 'dropbox' not in config:
        logging.error('Dropbox configuration is missing.')
        return False

    for param in ['access_token', 'folder_name']:
        if param not in config['dropbox']:
            logging.error('Dropbox parameter "{}" is missing.'.format(param))
            return False

    if 'render' not in config:
        logging.error('Render configuration is missing.')
        return False

    for param in ['frames_per_task']:
        if param not in config['render']:
            logging.error('Render parameter "{}" is missing.'.format(param))
            return False
