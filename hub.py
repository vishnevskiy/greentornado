from eventlet import getcurrent, greenlet
from eventlet.hubs import _threadlocal, use_hub
from eventlet.hubs.hub import READ, WRITE
from tornado import ioloop
import eventlet
import functools
import time

class TornadoHub(object):
    WRITE = WRITE
    READ = READ

    def __init__(self, mainloop_greenlet):
        self.io_loop = ioloop.IOLoop.instance()
        self.greenlet = mainloop_greenlet

    def switch(self):
        assert getcurrent() is not self.greenlet, 'Cannot switch to MAINLOOP from MAINLOOP'

        try:
            getcurrent().parent = self.greenlet
        except ValueError:
            pass

        return self.greenlet.switch()

    def stop(self):
        self.io_loop.stop()

    def add(self, event, fd, callback):
        if event is READ:
            self.io_loop.add_handler(fd, callback, ioloop.IOLoop.READ)
        if event is WRITE:
            self.io_loop.add_handler(fd, callback, ioloop.IOLoop.WRITE)

        return fd

    def remove(self, fd):
        self.io_loop.remove_handler(fd)

    def schedule_call_local(self, seconds, func, *args, **kwargs):
        g = greenlet.getcurrent()

        def call_if_greenlet_alive(*args1, **kwargs1):
            if g.dead:
                return
            return func(*args1, **kwargs1)

        return self.io_loop.add_timeout(time.time() + seconds, functools.partial(func, *args, **kwargs))

    schedule_call = schedule_call_local

    def schedule_call_global(self, seconds, func, *args, **kwargs):
        if seconds:
            return self.io_loop.add_timeout(time.time() + seconds, functools.partial(func, *args, **kwargs))

        return self.io_loop.add_callback(functools.partial(func, *args, **kwargs))

    def abort(self):
        self.ioloop.stop()

    @property
    def running(self):
        return self.ioloop.running

Hub = TornadoHub

def join_ioloop():
    """Integrate eventlet with Tornado's IOLoop."""

    use_hub(TornadoHub)
    assert not hasattr(_threadlocal, 'hub')
    global hub
    hub = _threadlocal.hub = _threadlocal.Hub(greenlet.getcurrent())

class SpawnFactory(object):
    """Factory that spawns a new greenlet for each incoming connection.

    For an incoming connection a new greenlet is created using the provided
    callback as a function and a connected green transport instance as an
    argument."""

    def __init__(self, handler):
        self.handler = handler

    def __call__(self, *args, **kwargs):
        eventlet.spawn_n(self.handler, *args, **kwargs)

