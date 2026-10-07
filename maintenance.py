"""Restore backups into a NEW directory; never overwrite existing data."""
import argparse
from pathlib import Path,PurePosixPath
import shutil
import sqlite3
import stat
import tempfile
import zipfile

def restore(archive,target):
    target=Path(target).resolve()
    if target.exists():raise ValueError('Restore destination must not exist. Choose a new folder.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        staging=Path(temp)/'restored';staging.mkdir()
        with zipfile.ZipFile(archive) as z:
            entries=z.infolist()
            if sum(i.file_size for i in entries)>2*1024**3:raise ValueError('Backup is too large (2 GB limit)')
            for i in entries:
                p=PurePosixPath(i.filename)
                if p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename:
                    raise ValueError('Unsafe backup path')
                if not p.parts or p.parts[0] not in ('assistant.sqlite3','tasks.sqlite3','RESTORE.txt','workspace','backups'):
                    raise ValueError('Unexpected backup entry')
                if stat.S_ISLNK(i.external_attr>>16):raise ValueError('Symlinks are not allowed in backups')
                dest=staging.joinpath(*p.parts)
                if i.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(i) as source,dest.open('wb') as output:shutil.copyfileobj(source,output)
        if not (staging/'assistant.sqlite3').exists():raise ValueError('Assistant database missing')
        for name in ('assistant.sqlite3','tasks.sqlite3'):
            path=staging/name
            if path.exists():
                connection=sqlite3.connect(str(path))
                try:
                    if connection.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
                finally:connection.close()
        staging.rename(target)
    return str(target)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('--to',required=True)
    args=parser.parse_args()
    try:print('Restored to '+restore(args.archive,args.to))
    except Exception as e:raise SystemExit('Restore failed: '+str(e))
