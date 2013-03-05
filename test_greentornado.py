import pytest
import greentornado


def test_greenify_a_functions():
    """@greenify should succefully imitates the decorated function."""
    @greentornado.greenify
    def job():
        """Do something with eventlet"""
        pass
    assert job.__name__ == 'job'
    assert job.__module__ == __name__
    assert job.__doc__ == 'Do something with eventlet'
    assert job.original != job

    def work():
        """Work with eventlet"""
        pass
    work_g = greentornado.greenify(work)
    assert work_g.original == work
    assert work_g.__name__ == work.__name__
    assert work_g.__module__ == work.__module__
    assert work_g.__doc__ == work.__doc__


def test_call_later():
    class MockTimer(object):
        def __init__(self, *args, **kwargs):
            pass

    with pytest.raises(AssertionError):
        greentornado.call_later(MockTimer, 12, 'function')
    with pytest.raises(TypeError):
        greentornado.call_later(MockTimer, '0.2 seconds', lambda: None)
    with pytest.raises(AssertionError):
        greentornado.call_later(MockTimer, -1, lambda: None)

    t = greentornado.call_later(MockTimer, 3, lambda: None)
    assert isinstance(t, MockTimer)
