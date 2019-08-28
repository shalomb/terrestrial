#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from billiard import current_process
from celery.exceptions import SoftTimeLimitExceeded, Ignore
from celery import Celery, current_app, Task
from celery.signals import after_task_publish, task_revoked

import os

from utils.handlers import utcnow
from utils.logger   import setup_logger
from utils.redisdb  import RedisDB

from .terraform import Terraform
from .ansible_playbook import PlaybookRunner
from .workspace import IsolatedWorkspace

celery = Celery('tasks')
celery.config_from_object('celeryconfig')
# celery.register_task(HelloWorld())

log = setup_logger(__name__)

@after_task_publish.connect
def set_task_default_state(sender=None, headers=None, body=None, **kwargs):
  '''
  Set the default status of a task to ACCEPTED instead of PENDING.
  This is so we can discern non-existent tasks when looking them up by id.
  https://stackoverflow.com/a/10089358/742600
  '''
  task_id = headers['id']
  # the task may not exist if sent using `send_task` which sends task by name.
  task = current_app.tasks.get(task_id)
  if current_app.AsyncResult(task_id).state == 'PENDING':
    backend = task.backend if task else current_app.backend
    backend.store_result(task_id, None, 'ACCEPTED')

@task_revoked.connect
def set_task_revoked_state(sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs):
  '''
  Set the default status of a revoked task to REVOKED instead of ACCEPTED.
  '''
  task_id = request.id
  # the task may not exist if sent using `send_task` which sends task by name.
  task = current_app.tasks.get(task_id)
  backend = task.backend if task else current_app.backend
  backend.store_result(task_id, None, 'REVOKED')

repo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workspace') # TODO, Move into config

class BaseTask(Task):
  ignore_result = False

  def __init__(self):
    self.db = RedisDB( url=celery.backend.url, db=0 )

  @property
  def name(self):
    return '.'.join([self.__module__, self.__name__])

  def on_failure(self, exc, task_id, args, kwargs, einfo):
    print('Error: {0!r} failed: {1!r}'.format(task_id, exc))

class LoadBalancerStack(BaseTask):

  request_id = None

  def do(self, func, *args, **kwargs):
    fname  = func.__qualname__
    status = f'{self.request_id} {fname} {args} {kwargs}'
    log.info(status)
    self.update_state(state=status)
    return func(*args, **kwargs)

  def run(self, request_id, *args, **kwargs):
    # TODO
    # Handle exceptions (throws=(FooException))

    # Workaround for celery unable to spawn new processes required by ansible
    # to run tasks
    #    [2019-07-26 23:56:10,451: WARNING/ForkPoolWorker-1]
    #    31531 1564178170.45125: got an error while queuing:
    #    daemonic processes are not allowed to have children
    # See https://github.com/celery/celery/issues/1709#issuecomment-324802431
    current_process()._config['daemon'] = False

    self.request_id = request_id

    payload = self.db.get(f'request/{request_id}/payload')
    openrc = payload['openstack_auth']

    job_id = self.request.id # yes, celery calls this a request
    payload = self.db.get(f'request/{request_id}/payload')

    env = {'ANSIBLE_DEBUG':'true'}
    with IsolatedWorkspace(parent=repo_directory, env=env) as instance_dir:
      try:
        # TODO Workspace setup
        # Validate passing of envvars

        tf = Terraform()
        apbr = PlaybookRunner(
          playbook_files    = ['./site.yml'],
          inventory_sources = ['./hosts.sh']
        )

        self.do(tf.setup, openrc=openrc)
        self.do(tf.init)
        self.do(tf.validate)
        self.do(tf.plan)
        self.do(tf.apply)
        self.do(tf.output)
        # self.do(tf.destroy)

        self.do(apbr.run)

        result = [ *tf.results, *apbr.results_callback.results ]
        return result
      except SoftTimeLimitExceeded as e:
        # TODO
        # Task has been revoked (SIGUSR1) or has timed out.
        # Perform cleanup actions here.
        #  - Backup terraform state
        #  - Remove child processes, sockets, files
        # NOTE
        # Igore() prevents celery from overriding our custom task status
        raise Ignore()

# Register all tasks defined in this module into our celery app
import sys, inspect
cur_classes = [
  cls[1].__name__ for cls in
  inspect.getmembers(sys.modules[__name__], inspect.isclass)
  if cls[1].__module__ == sys.modules[__name__].__name__
]

import importlib
def str_to_class(module_name, class_name):
  """Return a class instance from a string reference"""
  try:
    module_ = importlib.import_module(module_name)
    try:
      class_ = getattr(module_, class_name)()
    except AttributeError:
      logging.error('Class does not exist')
  except ImportError:
    logging.error('Module does not exist')
  return class_ or None

for name in cur_classes:
  cls = str_to_class(sys.modules[__name__].__name__, name)
  # cls.bind(celery)
  celery.register_task(cls)


