import argparse
import config
import database
import project
import logging


def parse_parameters():
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument('--config', '-c', type=str, default='config.json') # TODO add help
        parser.add_argument('--version', '-v', action='store_true',
                            help='The current version of the software')

        parser.add_argument('action', nargs='?', type=str, default='none') # TODO add help

        add_action_parameters(parser)

        return parser.parse_args()
    except Exception as e:
        logging.error('The commandline parameters could not be parsed. Original error: ' + str(e))


def add_action_parameters(parser):
    # for creating configs
    parser.add_argument('--default', action='store_true', help='create the default config file')
    parser.add_argument('--interactive', action='store_true', help='create the config file interactively')

    # for creating projects
    parser.add_argument('--project_name', type=str, default='', help='') # TODO add help
    parser.add_argument('--filename', type=str, help='')  # TODO add help
    parser.add_argument('--num_frames', type=int, help='')  # TODO add help

    # for cancelling
    parser.add_argument('--project', action='store_true', help='')
    parser.add_argument('--frames', action='store_true', help='')
    parser.add_argument('--by_machine', type=str, default='none', help='')
    parser.add_argument('--all_frames', action='store_true', help='')

    # for finishing
    parser.add_argument('--force', action='store_true', help='')

    # for project status
    parser.add_argument('--history', action='store_true', help='') # TODO add help
    parser.add_argument('--frame_list', action='store_true', help='') # TODO add help

    # for freeing
    parser.add_argument('--free_failed', action='store_true', help='')
    parser.add_argument('--free_waiting', action='store_true', help='')

    # for rendering
    parser.add_argument('--one_batch', action='store_true', help='')  # TODO add help
    parser.add_argument('--some_batches', type=int, default=0, help='')  # TODO add help


def parse_and_execute_actions(args):
    if args.action == 'none':
        logging.info('Nothing to do, leaving now...')
        return

    elif args.action == 'create-config':
        if args.default:
            config.create_default_config(args.config)
        elif args.interactive:
            config.create_config_interactively(args.config)
        else:
            logging.warning('No way to create the config file was specified. '
                            'Choose --default or --interactive.')

        return

    config.validate_config(args.config)
    cfg = config.load_config(args.config)

    if args.action == 'setup-database':
        database.setup_database(cfg)
        return

    db, cursor = database.connect_to_database(cfg)

    if not project.is_machine_registered(cfg, db, cursor):
        project.register_render_machine(cfg, db, cursor)

    if args.action == 'start':
        if not project.check_if_project_name_valid(args):
            logging.error('Project name "{}" is not a valid choice!'.format(args.project_name))
        elif project.check_if_project_name_taken(args, db, cursor):
            logging.error('Project name "{}" is already taken!'.format(args.project_name))
        else:
            project.start_project(args, cfg, db, cursor)

    elif args.action == 'cancel':
        # TODO add security check
        if args.project:
            project.cancel_project(args, cfg, db, cursor)
        elif args.frames:
            project.cancel_frames(args, cfg, db, cursor)
        else:
            logging.warning('Missing additional parameter, specify whether the project (--project) or frames '
                            '(--frames <...>) should be deleted.')

    elif args.action == 'finish':
        project.finish_project(args, cfg, db, cursor)

    elif args.action == 'check':    # status report
        if not project.check_if_project_name_valid(args):
            logging.error('Project name "{}" is not a valid choice!'.format(args.project_name))
        elif not project.check_if_project_name_taken(args, db, cursor):
            logging.error('Project name "{}" does not exist!'.format(args.project_name))
        else:
            project.get_project_info(args, cfg, db, cursor)

            if args.history:
                pass

            elif args.frame_list:
                print(project.get_project_frame_list(args, cfg, db, cursor))

    elif args.action == 'render':
        if args.one_batch:
            project.render_frames(args, cfg, db, cursor)
        elif args.some_batches > 0:
            for _ in range(args.some_batches):
                project.render_frames(args, cfg, db, cursor)
        else:
            while project.has_project_open_frames(args, cfg, db, cursor):
                project.render_frames(args, cfg, db, cursor)

    elif args.action == 'free':
        if args.free_failed:
            project.free_failed_frames(args, cfg, db, cursor)
        elif args.free_waiting:
            project.free_waiting_frames(args, cfg, db, cursor)

    database.close_connection(db, cursor)
