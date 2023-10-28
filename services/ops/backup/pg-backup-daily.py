import argparse
import datetime
import glob
import os
import subprocess

"""
python3 pg-backup.py mm /home/backup/postgresql 7
python3 pg-backup.py sentry /home/backup/postgresql 7
"""

parser = argparse.ArgumentParser()
parser.add_argument('database', help='Database to be backed up')
parser.add_argument('port', help='Database to be connetted')
parser.add_argument('path_to_backup', help='Path to backup folder')
parser.add_argument('keep_n_backups', type=int, help='Number of backups to keep')
args = parser.parse_args()

print(f'Postgres backup script started with args {args}')
timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
path_to_backup_file = os.path.join(args.path_to_backup, f'{args.database}_{timestamp}.sql')
print('Starting backup')
subprocess.run(
    f'pg_dump -U postgres {args.database} -p {args.port}  > {path_to_backup_file}',
    shell=True, check=True
)
print('Backup done')

backup_files = sorted(glob.glob(os.path.join(args.path_to_backup, f'{args.database}_*.sql')), reverse=True)
if len(backup_files) > args.keep_n_backups:
    print('Deleting outdated backups')
    n_backups_deleted = 0
    for path_to_backup_file in backup_files[args.keep_n_backups:]:
        os.remove(path_to_backup_file)
        n_backups_deleted += 1
    print(f'{n_backups_deleted} outdated backup(s) deleted')

print('Postgres backup script finished')

