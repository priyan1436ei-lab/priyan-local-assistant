"""Prevent two app processes from mutating the same local data directory."""
from pathlib import Path
import os

class InstanceLock:
    def __init__(self,root):
        root=Path(root);root.mkdir(parents=True,exist_ok=True)
        try:
            self.file=(root/'.instance.lock').open('a+b')
            self.file.seek(0)
            if not self.file.read(1):self.file.write(b'0');self.file.flush()
            self.file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            if hasattr(self,'file') and not self.file.closed:
                self.file.close()
            raise ValueError('Another Priyan Local instance is using this data folder. Open its existing window.')
    def close(self):
        if self.file.closed:return
        self.file.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
        self.file.close()
