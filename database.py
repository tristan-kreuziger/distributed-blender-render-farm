import mysql.connector
import os
import logging


def connect_to_database(cfg):
    try:
        db = mysql.connector.connect(
            host=cfg['database']['host'],
            user=cfg['database']['user'],
            passwd=cfg['database']['pw'],
            port=cfg['database']['port'],
            database=cfg['database']['db']
        )

        return db, db.cursor(buffered=False)
    except Exception as e:
        logging.critical('The database connector produced an error, '
                         'when trying to connect to the database: ' + str(e))


def close_connection(db, cursor):
    try:
        cursor.close()
        db.close()
    except Exception as e:
        logging.critical('The database connector produced an error, '
                         'when trying to close the connection to the database: '
                         + str(e))


def execute_statement(db, cursor, sql, params, with_result=False, multi=False, commit=False):
    try:
        cursor.execute(sql, params, multi=multi)
        if commit:
            db.commit()

        if with_result:
            return cursor.fetchall()

    except Exception as e:
        logging.critical('The statement ("{}") could not be executed: {}'.format(sql, e))


def setup_database(cfg):
    db, cursor = connect_to_database(cfg)

    execute_statement(db, cursor, 'USE {};'.format(cfg['database']['db']), ())
    execute_statement(db, cursor, 'SHOW TABLES;', ())

    tables = cursor

    for table in tables:
        execute_statement(db, cursor, 'DROP TABLE {};'.format(table[0].decode('utf-8')), ())

    with open(os.path.join(os.getcwd(), 'database', 'setup.sql'), 'r') as f:
        execute_statement(db, cursor, ' '.join(f.readlines()), (), multi=True)

    close_connection(db, cursor)

    logging.info('The database was successfully set up.')
