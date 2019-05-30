import logging

_DEBUG = True

if _DEBUG:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s > %(asctime)s > %(message)s [in %(filename)s at %(lineno)d]',
                        datefmt='%Y-%m-%d %H:%M:%S')
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s > %(asctime)s > %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
