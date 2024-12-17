"""
Mock redis sessions db
"""

import pytest

session_data = {}


class RedisSessions(object):
    @staticmethod
    def set(
        self,
        name,
        value,
        ex=None,
        px=None,
        nx=False,
        xx=False,
        keepttl=False,
        get=False,
        exat=None,
        pxat=None,
    ):
        session_data[name] = value

    def setex(self, name=None, time=None, value=None):
        session_data[name] = value
        return 1

    @staticmethod
    def setnx(key, val):
        if key in session_data:
            return 0
        else:
            session_data[key] = val
            return 1

    def get(self, key):
        return session_data.get(key)

    def delete(self, *names):
        for name in names:
            if session_data.get(name):
                del session_data[name]


@pytest.fixture()
def mock_redis_sessions(session_mocker):
    session_mocker.patch("redis.Redis.get", RedisSessions.get)
    session_mocker.patch("redis.Redis.set", RedisSessions.set)
    session_mocker.patch("redis.Redis.delete", RedisSessions.delete)
    session_mocker.patch("redis.Redis.setex", RedisSessions.setex)
