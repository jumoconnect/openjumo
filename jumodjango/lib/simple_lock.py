import errno, os, socket, sys

class LockError(IOError):
    def __init__(self, errno, strerror, filename):
        IOError.__init__(self, errno, strerror, filename)

class LockHeld(LockError):
    def __init__(self, errno, filename, locker):
        LockError.__init__(self, errno, 'Lock held', filename)
        self.locker = locker

class LockUnavailable(LockError):
    pass


class SimpleLock:
    """Tried to find a simple pid locking mechanism on the web but
       everything was so over architected i did that thing I hate
       and wrote my own and I did it fast.  HATE BEING THAT GUY!"""

    def __init__(self, pid_file):
        self.pid_file = pid_file
        self.hostname = socket.gethostname()
        self.lockname = '%s:%s' % (self.hostname, os.getpid())
        self.lock()

    def lock(self):
        try:
            self.trylock()
            return True
        except LockHeld, err:
            #changed my mind about adding holding counts.
            #leaving this hear for future.
            raise

    def trylock(self):
        try:
            ln = os.symlink(self.lockname, self.pid_file)
        except (OSError, IOError), err:
            if err.errno == errno.EEXIST:
                locker = self.testlock()
                if locker is not None:
                    raise LockHeld(errno.EEXIST, self.pid_file, locker)
            else:
                raise LockUnavailable(err.errno, err.strerror, self.pid_file)


    def testlock(self):
        locker = None
        try:
            locker = os.readlink(self.pid_file)
            host, pid = locker.split(":", 1)
            pid = int(pid)
            if host != self.hostname:
                return locker

            if self.testpid(pid):
                return locker

            #Break lock by created new lock for race
            try:
                l = SimpleLock(self.pid_file + "breaking")
                os.unlink(self.pid_file)
                os.symlink(self.lockname, self.pid_file)
                l.release()
            except LockError:
                return locker
        except ValueError:
            return locker


    def testpid(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError, err:
            return err.errno != errno.ESRCH


    def release(self):
        try:
            os.unlink(self.pid_file)
        except OSError:
            pass
