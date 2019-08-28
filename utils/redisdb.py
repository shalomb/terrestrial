#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# TODO
# Support redis sentinel master discovery

import redis
import json

class RedisDB(object):

  def __init__(self, url, db=0):
    self._redis_conn_pool = pool = redis.ConnectionPool().from_url('{}?db={}'.format(url, 0))
    self._redis = redis.Redis(connection_pool=self._redis_conn_pool)
    self.ping = self.redis.echo(1).decode() # Smoke test
    self.db_size = self.redis.dbsize()

  @property
  def redis(self):
    return self._redis

  @redis.setter
  def redis(self, value):
    self._redis = value
    return self._redis

  def get(self, k):
    if self.exists(k):
      return json.loads(self.redis.get(k).decode())
    else:
      raise KeyError('Key {} does not exist'.format(k))

  def set(self, k, v):
    return self.redis.set(k, json.dumps(v))

  def mset(self, d):
    return self.redis.mset(d)

  def exists(self, k):
    return [False, True][self.redis.exists(k)]


