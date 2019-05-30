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

    logging.info('Created new default config file at "{}".'.format(os.path.join(os.getcwd(), config_filename)))


def create_config_interactively(config_filename):
    config = get_default_config()

    try:
        print('Choose the values for all parameters of the configuration.')
        for top_level_key in config:
            print('Category {}: '.format(top_level_key))

            for low_level_key in config[top_level_key]:
                print('\t{}: '.format(low_level_key), end='')
                config[top_level_key][low_level_key] = input()

        with open(config_filename, 'w', encoding='utf8') as f:
            json.dump(config, f, indent=4)
    except KeyboardInterrupt:
        logging.info('Cancelled')

    logging.info('Created new config file at "{}".'.format(os.path.join(os.getcwd(), config_filename)))


def load_config(config_filename):
    try:
        with open(config_filename, 'r', encoding='utf8') as f:
            return json.load(f)
    except Exception as e:
        logging.critical('Exception occurred ({}), run validate-config'.format(e))


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
