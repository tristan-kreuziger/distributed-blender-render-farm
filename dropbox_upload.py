import dropbox
import dropbox.exceptions
import dropbox.files
import logging
import ntpath


def get_base_filename(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def upload_file(token, file, app_name):
    upload_files(token, [file], app_name)


def upload_files(token, files, app_name, project_name):
    try:
        dbx = dropbox.Dropbox(token)

        for file in files:
            with open(file, 'rb') as f:
                dbx.files_upload(f.read(), '/' + app_name + '/' + project_name + '/' + get_base_filename(file),
                                 dropbox.files.WriteMode.overwrite)

        return True
    except dropbox.exceptions.ApiError as e:
        logging.critical('Dropbox produced an API error: ' + str(e))
        return False
