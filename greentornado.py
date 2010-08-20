from eventlet import getcurrent, greenlet
from eventlet.hubs import _threadlocal, use_hub, timer, get_hub
from eventlet.hubs.hub import READ, WRITE
from tornado import ioloop
import eventlet
import functools
import time
import sys

class Timer(timer.Timer):
    """Fix Eventlet's Timer to work with Tornado's IOLoop."""

    def __init__(self, *args, **kwargs):
        timer.Timer.__init__(self, *args, **kwargs)
        self.schedule()

    def schedule(self):
        """Schedule this timer to run in the IOLoop."""

        self.called = False
        self.scheduled_time = get_hub().io_loop.add_timeout(time.time() + self.seconds, self)
        return self

    def cancel(self):
        """Prevent this timer from being called. If the timer has already
        been called or canceled, has no effect."""

        if not self.called:
            self.called = True
            get_hub().io_loop.remove_timeout(self.scheduled_time)
            try:
                del self.tpl
            except AttributeError:
                pass

class LocalTimer(Timer):
    def __init__(self, *args, **kwargs):
        self.greenlet = greenlet.getcurrent()
        Timer.__init__(self, *args, **kwargs)

    @property
    def pending(self):
        if self.greenlet is None or self.greenlet.dead:
            return False
        return not self.called

    def __call__(self, *args):
        if not self.called:
            self.called = True
            if self.greenlet is not None and self.greenlet.dead:
                return
            callback, args, kwargs = self.tpl
            callback(*args, **kwargs)

    def cancel(self):
        self.greenlet = None
        Timer.cancel(self)

def call_later(cls, seconds, func, *args, **kwargs):
    assert callable(func), '%s is not callable' % func
    if not isinstance(seconds, (int, long, float)):
        raise TypeError('Seconds must be int, long, or float, was ' + type(seconds))
    assert sys.maxint >= seconds >= 0, '%s is not greater than or equal to 0 seconds' % seconds
    return cls(seconds, func, *args, **kwargs)

class TornadoHub(object):
    WRITE = WRITE
    READ = READ

    def __init__(self, mainloop_greenlet, callback=None):
        self.greenlet = mainloop_greenlet
        self.io_loop = ioloop.IOLoop.instance()

        if callback:
            # Spawn the callback after the IOLoop starts.
            self.io_loop.add_callback(functools.partial(eventlet.spawn_n, callback))

    def switch(self):
        assert getcurrent() is not self.greenlet, 'Cannot switch to MAINLOOP from MAINLOOP'

        try:
            getcurrent().parent = self.greenlet
        except ValueError:
            pass

        return self.greenlet.switch()

    def stop(self):
        self.io_loop.stop()

    abort = stop

    def add(self, event, fd, callback):
        if event is READ:
            self.io_loop.add_handler(fd, callback, ioloop.IOLoop.READ)
        elif event is WRITE:
            self.io_loop.add_handler(fd, callback, ioloop.IOLoop.WRITE)

        return fd

    def remove(self, fd):
        self.io_loop.remove_handler(fd)

    def schedule_call_local(self, seconds, func, *args, **kwargs):
        def call_if_greenlet_alive(*args1, **kwargs1):
            if t.greenlet.dead:
                return
            return func(*args1, **kwargs1)
        t = call_later(LocalTimer, seconds, call_if_greenlet_alive, *args, **kwargs)
        return t

    schedule_call = schedule_call_local

    def schedule_call_global(self, seconds, func, *args, **kwargs):
        return call_later(Timer, seconds, func, *args, **kwargs)

    @property
    def running(self):
        return self.ioloop.running

Hub = TornadoHub

def join_ioloop(callback=None):
    """Integrate Eventlet with Tornado's IOLoop."""

    use_hub(TornadoHub)
    assert not hasattr(_threadlocal, 'hub')
    global hub
    hub = _threadlocal.hub = _threadlocal.Hub(greenlet.getcurrent(), callback)

class SpawnFactory(object):
    """Factory that spawns a new greenlet for each incoming connection.

    For an incoming connection a new greenlet is created using the provided
    callback as a function and a connected green transport instance as an
    argument."""

    def __init__(self, handler):
        self.handler = handler

    def __call__(self, *args, **kwargs):
        return eventlet.spawn(self.handler, *args, **kwargs)

def greenify_handler(handler):
    """Similar to SpawnFactory, but used to make a tornado.web.RequestHandler
    execute within a greenlet."""

    execute = handler._execute
    handler._execute = lambda self, *args, **kwargs: eventlet.spawn_n(execute, self, *args, **kwargs)

    return handler

