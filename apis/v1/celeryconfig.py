#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# https://docs.celeryproject.org/en/latest/userguide/configuration.html

broker_url     = 'redis://localhost/0'
result_backend = 'redis://localhost/0'
result_persistent = False

enable_utc = True
timezone   = 'Europe/Bratislava'

task_serializer='json'
accept_content = ['application/json']

result_serializer='json'
result_accept_content = ['application/json']

event_serializer = 'json'

task_track_started = True
task_ignore_result = False
task_store_errors_even_if_ignored = True
task_reject_on_worker_lost = True
task_soft_time_limit = 3600
# TODO - Enable when the payload is sizeable
# task_compression = True

def task_failure_handler(self, exc, task_id, args, kwargs, einfo):
  print('Task failed: {0!r}'.format(exc))

task_annotations = {
  '*': {
    'on_failure': task_failure_handler,
    'rate_limit': '10/s'
  }
}

