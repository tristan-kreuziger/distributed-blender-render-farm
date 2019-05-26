import mysql.connector
import config
import os


def connect_to_database(cfg):
    return mysql.connector.connect(
        host=cfg['database']['host'],
        user=cfg['database']['user'],
        passwd=cfg['database']['pw'],
        database=cfg['database']['db']
    )


def setup_database(config_filename):
    cfg = config.load_config(config_filename)
    db = connect_to_database(cfg)

    cursor = db.cursor(buffered=True)

    cursor.execute('USE {};'.format(cfg['database']['db']))

    cursor.execute('SHOW TABLES;')
    for x in cursor:
        table_name = x[0].decode('utf-8')
        cursor.execute('DROP TABLE {};'.format(table_name))

    with open(os.path.join(os.getcwd(), 'database', 'setup.sql'), 'r') as f:
        cursor.execute(' '.join(f.readlines()), multi=True)

    cursor.close()
    db.close()
