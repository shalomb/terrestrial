#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from celery import Celery, Task
from celery.utils.log  import get_task_logger

from celery.signals    import after_task_publish
from celery.exceptions import SoftTimeLimitExceeded

# TODO
# Loggers
# http://docs.celeryproject.org/en/latest/userguide/tasks.html

def setup_celery(app_name, tasks, config=None):
  celery = Celery(app_name, include=[tasks])
  if config:
    celery.config_from_object(config)
  return celery

@after_task_publish.connect
def set_task_default_state(sender=None, headers=None, body=None, **kwargs):
  '''
  Set the default status of a task to ACCEPTED instead of PENDING.
  This is so we can discern non-existent when looking them up by id.
  https://stackoverflow.com/a/10089358/742600
  '''
  task_id = headers['id']
  # the task may not exist if sent using `send_task` which sends task by name.
  task = current_app.tasks.get(task_id)
  if current_app.AsyncResult(task_id).state == 'PENDING':
    backend = task.backend if task else current_app.backend
    backend.store_result(task_id, None, 'ACCEPTED')

class Jobs(object):
  pass
