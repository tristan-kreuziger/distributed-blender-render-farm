import database
import subprocess
import os
import time
import logging
from prettytable import PrettyTable
import datetime as dt
import dropbox_upload


_VALID_PROJECT_STATUS = ['CREATED', 'RUNNING', 'FINISHED', 'CANCELLED']
_VALID_FRAME_STATUS = ['CREATED', 'RESERVED', 'FINISHED', 'CANCELLED', 'FAILED']


def check_if_project_name_valid(args):
    project_name = args.project_name

    # add more checks if needed later, maybe for special characters
    return project_name != ''


def check_if_project_name_taken(args, db, cursor):
    return len(database.execute_statement(
        db, cursor, 'SELECT * FROM render_project WHERE project_name = %s;',
        (args.project_name,), with_result=True)) > 0


def check_project_status(args, db, cursor):
    sql = '''
    SELECT render_project.id, project_name, filename, number_of_frames,
        status_name, change_date FROM render_project
        JOIN render_project_history 
            ON render_project.id = render_project_id
        JOIN render_project_status 
            ON status = render_project_status.id
        WHERE project_name = %s
        ORDER BY change_date DESC
        LIMIT 1;
    '''

    result = database.execute_statement(db, cursor, sql, (args.project_name,), with_result=True)[0]

    return {
        'project_id': result[0],
        'project_name': result[1],
        'filename': result[2],
        'number_of_frames': result[3],
        'status': result[4],
        'change_date': result[5]
    }


def set_project_status(args, cfg, db, cursor, status):
    if status not in _VALID_PROJECT_STATUS:
        logging.error('Invalid project status ("{}")!'.format(status))
        return

    sql = '''
    INSERT INTO render_project_history
        (render_project_id, change_date, status)
    VALUES
        ((SELECT id FROM render_project WHERE project_name = %s), %s,
        (SELECT id FROM render_project_status WHERE status_name = %s));
    '''
    name = args.project_name
    now = dt.datetime.now(tz=dt.timezone.utc)
    database.execute_statement(db, cursor, sql, (name, now, status), commit=True)

    # TODO from what status
    logging.debug('Project status of "{}" changed to "{}".'.format(name, status))


def is_machine_registered(cfg, db, cursor, name=None):
    if name is None:
        name = cfg['general']['machine_name']
        logging.debug('No machine name given, took name from config.')

    sql = '''
    SELECT COUNT(*) FROM render_machine WHERE machine_name = %s;
    '''

    result = database.execute_statement(db, cursor, sql, (name,), with_result=True)[0][0]

    return result != 0


def register_render_machine(cfg, db, cursor, name=None):
    if name is None:
        name = cfg['general']['machine_name']
        logging.debug('No machine name given, took name from config.')

    sql = '''
    INSERT INTO render_machine
        (machine_name)
    VALUES
        (%s);
    '''
    database.execute_statement(db, cursor, sql, (name,), commit=True)

    logging.info('Render machine "{}" was successfully registered with the server.'.format(name))


def start_project(args, cfg, db, cursor):
    project_name = args.project_name

    sql = '''
    INSERT INTO render_project
        (project_name, filename, number_of_frames)
    VALUES
        (%s, %s, %s);
    '''
    database.execute_statement(db, cursor, sql,
        (project_name, args.filename, args.num_frames), commit=True)

    project_id = cursor.lastrowid
    logging.debug('Project "{}" created with id = {}.'.format(project_name, project_id))

    sql = '''
    INSERT INTO render_project_history(render_project_id, change_date, status)
       VALUES (%s, %s,
       (SELECT id FROM render_project_status WHERE status_name = "CREATED"));
    '''

    now = dt.datetime.now(tz=dt.timezone.utc)
    database.execute_statement(db, cursor, sql, (project_id, now), commit=True)

    sql = '''
    INSERT INTO frame_task_history
        (render_project_id, frame_index, change_date, machine_id, status)
    VALUES
        (%s, %s, %s,
        (SELECT id FROM render_machine WHERE machine_name = "SERVER"),
        (SELECT id FROM frame_task_status WHERE status_name = "CREATED"));
    '''

    for i in range(args.num_frames):
        database.execute_statement(db, cursor, sql, (project_id, i, now), commit=True)

    logging.info('Project "{}" successfully started. '.format(project_name) +
                 'To see info about the project run: python main.py check '
                 '--project_name {}'.format(project_name))


def cancel_project(args, cfg, db, cursor):
    status = check_project_status(args, db, cursor)
    project_name = args.project_name

    if status['status'] == 'FINISHED':
        logging.warning('The project "{}" was finished, you cannot cancel it.'.format(project_name))
        return
    elif status['status'] == 'CANCELLED':
        logging.warning('The project "{}" has already been cancelled.'.format(project_name))
        return

    set_project_status(args, cfg, db, cursor, 'CANCELLED')
    set_all_frame_task_status(args, cfg, db, cursor, 'CANCELLED')

    logging.info('Project "{}" successfully cancelled.'.format(project_name))

    print(get_project_frame_list(args, cfg, db, cursor))


def finish_project(args, cfg, db, cursor):
    status = check_project_status(args, db, cursor)
    name = args.project_name

    if status['status'] == 'FINISHED':
        logging.warning('The project "{}" has already been finished.'.format(name))
        return
    elif status['status'] == 'CANCELLED':
        logging.warning('The project "{}" was cancelled, you cannot finish it.'.format(name))
        return

    if not args.force:
        open_frames = get_number_of_frames_with_status(args, cfg, db, cursor, 'CREATED')
        if open_frames > 0:
            logging.warning('There are still {} open frames. Render them or cancel them with:'.format(open_frames)
                            + '\r\n\t... "cancel --frames --all_frames"'
                            + '\r\n\t... "cancel --frames --by_machine <machine>"')
            return

        reserved_frames = get_number_of_frames_with_status(args, cfg, db, cursor, 'RESERVED')
        if reserved_frames > 0:
            logging.warning('There are still {} reserved frames. Wait for them or cancel them with:'.format(reserved_frames)
                            + '\r\n\t... "cancel --frames --all_frames"'
                            + '\r\n\t... "cancel --frames --by_machine <machine>"')
            return
    else:
        set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CANCELLED', 'CREATED')
        set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CANCELLED', 'RESERVED')

    set_project_status(args, cfg, db, cursor, 'FINISHED')
    status = check_project_status(args, db, cursor)

    logging.info('Project "{}" has been finished.'.format(name))
    print('Frames:')
    print('\tTotal:     {}'.format(status['number_of_frames']))
    print('\tFinished:  {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'FINISHED')))
    print('\tCancelled: {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'CANCELLED')))
    print('\tFailed:    {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'FAILED')))

    print(get_project_frame_list(args, cfg, db, cursor))


def get_project_info(args, cfg, db, cursor):
    status = check_project_status(args, db, cursor)

    print('-' * 20)
    print('Project name:  {} (id={})'.format(status['project_name'], status['project_id']))
    print('Filename:      {}'.format(status['filename']))
    print('Latest Status: {} (changed {:%Y-%m-%d %H:%M:%S})'.format(status['status'], status['change_date']))
    print('')

    print('Frames:')
    print('\tTotal:     {}'.format(status['number_of_frames']))
    print('\tOpen:      {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'CREATED')))
    print('\tReserved:  {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'RESERVED')))
    print('\tFinished:  {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'FINISHED')))
    print('\tCancelled: {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'CANCELLED')))
    print('\tFailed:    {}'.format(get_number_of_frames_with_status(args, cfg, db, cursor, 'FAILED')))


def get_project_frame_list(args, cfg, db, cursor):
    sql = '''
    SELECT frame_task_history.frame_index, status_name, render_machine.machine_name, change_date  FROM frame_task_history
        JOIN render_project
            ON render_project.id = render_project_id
        LEFT JOIN render_machine
            ON render_machine.id = machine_id
        JOIN frame_task_status fts 
            ON frame_task_history.status = fts.id
        JOIN (
            SELECT render_project_id, frame_index, MAX(change_date) as max_date FROM frame_task_history
                JOIN render_project
                    ON render_project.id = render_project_id
                WHERE project_name = %s
                GROUP BY render_project_id, frame_index
        ) sub_table ON sub_table.frame_index = frame_task_history.frame_index AND sub_table.max_date = change_date
        WHERE project_name = %s ORDER BY frame_task_history.frame_index;
    '''

    name = args.project_name
    result = database.execute_statement(db, cursor, sql, (name, name), with_result=True)

    x = PrettyTable()
    x.field_names = ['frame', 'status', 'render machine', 'change date']
    for row in result:
        x.add_row(row)

    return x


def get_number_of_frames_with_status(args, cfg, db, cursor, status):
    name = args.project_name

    sql = '''
    SELECT COUNT(*) FROM frame_task_history
        JOIN frame_task_status
            ON frame_task_history.status = frame_task_status.id
        JOIN render_project rp 
            ON frame_task_history.render_project_id = rp.id
        JOIN (
            SELECT render_project_id, frame_index, MAX(change_date) as max_date FROM frame_task_history
                JOIN render_project
                    ON render_project.id = render_project_id
                WHERE project_name = %s
                GROUP BY render_project_id, frame_index
        ) sub_table ON sub_table.frame_index = frame_task_history.frame_index AND sub_table.max_date = change_date
        WHERE project_name = %s AND frame_task_status.status_name = %s;
    '''
    result = database.execute_statement(db, cursor, sql, (name, name, status), with_result=True)[0][0]

    return result


def has_project_open_frames(args, cfg, db, cursor):
    return get_number_of_frames_with_status(args, cfg, db, cursor, 'CREATED') > 0


def is_frame_status_valid(status):
    if status not in _VALID_FRAME_STATUS:
        logging.error('Invalid frame status ("{}")!'.format(status))
        return False
    else:
        return True


def set_frame_task_status(args, cfg, db, cursor, status, frames):
    if not is_frame_status_valid(status):
        return

    now = dt.datetime.now(tz=dt.timezone.utc)
    sql = '''
    INSERT IGNORE INTO frame_task_history
        (render_project_id, frame_index, change_date, machine_id, status)
    VALUES
        (
            (SELECT id FROM render_project WHERE project_name = %s),
            %s,
            %s,
            (SELECT id FROM render_machine WHERE machine_name = %s),
            (SELECT id FROM frame_task_status WHERE status_name = %s)
        );
    '''
    name = args.project_name

    for i in frames:
        database.execute_statement(db, cursor, sql, (name, i, now, cfg['general']['machine_name'], status), commit=True)

    if len(frames) > 0:
        logging.debug('Render status for project "{}" for the frame(s) {} has been changed to {}'
                      .format(name, ', '.join([str(f) for f in frames]), status))


def set_all_frame_task_status(args, cfg, db, cursor, status):
    if not is_frame_status_valid(status):
        return

    sql = '''
    SELECT frame_index FROM frame_task_history
        JOIN render_project rp 
            ON frame_task_history.render_project_id = rp.id
        WHERE project_name = %s;
    '''
    frames = [row[0] for row in database.execute_statement(db, cursor, sql, (args.project_name,), with_result=True)]

    set_frame_task_status(args, cfg, db, cursor, status, frames)


def set_all_frame_task_status_conditional(args, cfg, db, cursor, new_status, old_status):
    if not is_frame_status_valid(new_status) or not is_frame_status_valid(old_status):
        return

    sql = '''
    SELECT frame_index FROM frame_task_history
        JOIN frame_task_status 
            ON status = frame_task_status.id
        JOIN render_project rp 
            ON frame_task_history.render_project_id = rp.id
        WHERE project_name = %s AND status_name = %s;
    '''
    frames = [row[0] for row in database.execute_statement(db, cursor, sql, (args.project_name, old_status), with_result=True)]

    set_frame_task_status(args, cfg, db, cursor, new_status, frames)


def set_all_frame_task_status_by_machine(args, cfg, db, cursor, machine, status):
    if not is_frame_status_valid(status):
        return

    sql = '''
    SELECT frame_index FROM frame_task_history
        JOIN frame_task_status ON status = frame_task_status.id
        JOIN render_machine ON render_machine.id = machine_id
        WHERE render_project_id = (SELECT id FROM render_project WHERE project_name = %s)
            AND machine_name = %s;
    '''
    frames = [row[0] for row in database.execute_statement(db, cursor, sql, (args.project_name, machine), with_result=True)]

    set_frame_task_status(args, cfg, db, cursor, status, frames)


def request_frames_to_render(args, cfg, db, cursor):
    status = check_project_status(args, db, cursor)

    if status['status'] != 'RUNNING':
        set_project_status(args, cfg, db, cursor, 'RUNNING')

    sql = '''
    SELECT * FROM frame_task_history
        JOIN render_project rp
            ON frame_task_history.render_project_id = rp.id
        JOIN frame_task_status
            ON frame_task_history.status = frame_task_status.id
        JOIN (
            SELECT render_project_id, frame_index, MAX(change_date) as max_date FROM frame_task_history
                JOIN render_project
                    ON render_project.id = render_project_id
                WHERE project_name = %s
                GROUP BY render_project_id, frame_index
        ) sub_table ON sub_table.frame_index = frame_task_history.frame_index AND sub_table.max_date = change_date
        WHERE project_name = %s AND frame_task_status.status_name = 'CREATED'
        ORDER BY frame_task_history.frame_index
        LIMIT %s;
    '''
    name = args.project_name
    result = database.execute_statement(db, cursor, sql, (name, name, cfg['render']['frames_per_task']), with_result=True)

    frames = [row[1] for row in result]

    if len(frames) > 0:
        set_frame_task_status(args, cfg, db, cursor, 'RESERVED', frames)
        logging.info('Got task to render frame(s) {} of project "{}".'.format(name, ', '.join([str(f) for f in frames])))
    else:
        logging.info('No open tasks remaining.')  # TODO check other tasks and offer finish

    return frames


def render_frames(args, cfg, db, cursor):
    frames = request_frames_to_render(args, cfg, db, cursor)

    if len(frames) == 0:
        return

    status = check_project_status(args, db, cursor)

    try:
        start_time = time.time()
        process = subprocess.Popen(
            [cfg['general']['blender_path'], '-b',
             os.path.join('//', cfg['general']['input_path'], status['filename']),
             '-s', str(frames[0]), '-e', str(frames[-1]),
             '-o', os.path.join(
                os.getcwd(), cfg['general']['output_path'], cfg['general']['output_prefix'] + '_frame_#####'),
             '-a'],
            )
        process.wait()

        logging.debug('Blender exit code: ' + str(process.returncode))

        end_time = time.time() - start_time

        logging.info('Finished rendering frames {} for project "{}" ({:0.3f}s).'.format(
            ', '.join([str(f) for f in frames]), args.project_name, end_time))
    except Exception as e:
        logging.critical('During the rendering by Blender an exception occurred: ' + str(e))
        set_frame_task_status(args, cfg, db, cursor, 'FAILED', frames)

    filenames = [os.path.join(os.getcwd(), cfg['general']['output_path'],
                              cfg['general']['output_prefix'] + '_frame_{:05}.png'.format(f))
                 for f in frames]

    if dropbox_upload.upload_files(cfg['dropbox']['access_token'], filenames, cfg['dropbox']['folder_name'],
                                   args.project_name):
        set_frame_task_status(args, cfg, db, cursor, 'FINISHED', frames)
    else:
        set_frame_task_status(args, cfg, db, cursor, 'FAILED', frames)


def cancel_frames(args, cfg, db, cursor):
    if args.all_frames:
        set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CANCELLED', 'CREATED')
        set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CANCELLED', 'RESERVED')

        logging.info('Cancelled all remaining frames of project "{}".'.format(args.project_name))
    elif args.by_machine != 'none':
        if args.by_machine in ['', 'this']:
            args.by_machine = cfg['general']['machine_name']

        if is_machine_registered(cfg, db, cursor, args.by_machine):
            set_all_frame_task_status_by_machine(args, cfg, db, cursor, args.by_machine, 'CANCELLED')

            logging.info('Cancelled all remaining frames of project "{}" by machine "{}".'.format(args.project_name, args.by_machine))
        else:
            logging.error('Machine "{}" is not registered on the server and has therefore no tasks!'.format(args.by_machine))


def free_failed_frames(args, cfg, db, cursor):
    set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CREATED', 'FAILED')
    logging.info('All failed frames have been reset for project "{}".'.format(args.project_name))


def free_waiting_frames(args, cfg, db, cursor):
    logging.warning('Warning: this will reset frames that might be currently worked on by other machines!')
    set_all_frame_task_status_conditional(args, cfg, db, cursor, 'CREATED', 'RESERVED')
    logging.info('All reserved frames have been reset for project "{}".'.format(args.project_name))
