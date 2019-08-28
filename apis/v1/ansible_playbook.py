#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from ansible import context, utils
from ansible.context import CLIARGS
from ansible.executor.playbook_executor  import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.module_utils import basic
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from os import environ, getcwd
import ansible.constants as C
import jinja2
import json
import shutil
import sys

def warn(*args, **kwargs):
  print( args, 'yellow', file=sys.stderr )

class ResultsCallback(CallbackBase):
  """A sample callback plugin used for performing an action as results come in
  If you want to collect all results into a single object for processing at
  the end of the execution, look into utilizing the ``json`` callback plugin
  or writing your own custom callback plugin
  """

  CALLBACK_VERSION = 0.1
  CALLBACK_TYPE    = 'aggregate'
  CALLBACK_NAME    = 'custom'

  # See ansible/ansible/lib/ansible/plugins/callback/__init__.py
  # for a reference on available callbacks

  def __init__(self, *args, **kwargs):
    self.num_tasks = 0
    self.cur_task_no = 0
    self.results = []

    super().__init__(*args, **kwargs)
    parent_class = CallbackBase()
    parent_methods = [
      attr for attr in dir(parent_class) if
        type( getattr(parent_class, attr) ).__name__ == 'method' and
        attr != '__init__'
    ]

    for fn in parent_methods:
      def delegate(self, *args, fn=fn, **kwargs):
        warn('-'*80)
        warn('delegate: {}({}, {})'.format(fn, args, kwargs))
        for arg in args:
          warn(' arg: ', arg, type(arg), dir(type(arg)))
        for k in kwargs.keys():
          warn(" kwarg: {{ '{}': {} }}".format(k, kwargs[k]))
        warn('')

      exists = getattr(self.__class__, fn)
      # TODO Hook up 'exists' to log sink
      if exists and exists.__module__ == sys.modules[__name__].__name__:
        setattr(self.__class__, fn, exists)
      else:
        if environ.get('DEBUG', False):
          setattr(self.__class__, fn, delegate)

  def report(self, data, err=False):
    self.results.append(data)
    r = json.dumps(data, indent=2)
    # warn(r) if err else print(r)

  def v2_playbook_on_no_hosts_matched(self, *args, **kwargs):
    r = {
      'v2_playbook_on_no_hosts_matched': {
        'msg': 'No hosts matched'
      }
    }
    self.report(r)

  def v2_playbook_on_start(self, result, *args, **kwargs):
    files = [ x for x in result._loader._FILE_CACHE.keys() ]
    tasks_files = [ x for x in files if str(x).find('tasks') >= 1 ]
    tasks = []
    for f in tasks_files:
      t = result._loader._FILE_CACHE.get(f)
      if t:
        for i in t:
          tasks.append(i)

    self.num_tasks = len(tasks)

    r = {
      'v2_playbook_on_start': {
        '_ds': result._ds if hasattr(result, '_ds') else None,
        'basedir': result._basedir,
        'cwd': getcwd(),
        'play_file': result._file_name,
        'tasks_files': tasks_files,
        'tasks': tasks,
        'number_of_tasks': self.num_tasks
      }
    }
    self.report(r)

  def v2_playbook_on_task_start(self, task, is_conditional):
    self.cur_task_no = self.cur_task_no + 1
    r = {
      'v2_playbook_on_task_start': {
        'task_no': self.cur_task_no,
        'progress': '{}/{}'.format(self.cur_task_no, self.num_tasks),
        'role': str(task._role),
        'action': str(task._attributes['action']),
        '_ds': task._ds if hasattr(task, '_ds') else None,
        'is_conditional': is_conditional
      }
    }
    self.report(r)

  def v2_runner_on_failed(self, result, ignore_errors=False):
    r = {
      'v2_runner_on_failed': {
        'host': str(result._host),
        'task': str(result._task),
        'msg':  str(result._result['msg']),
        'action': str(result._task_fields['action']),
        'name': str(result._task_fields['name']),
        'tags': result._task_fields['tags']
      }
    }
    warn('Failed: {}, {} -- {}'.format(result._host, result._task, result._result['msg']))
    self.report(r, err=True)

  def v2_runner_on_ok(self, result, **kwargs):
    """Print a json representation of the result
    This method could store the result in an instance attribute for retrieval later
    """
    r = {
      'v2_runner_on_ok': {
        'host':     str(result._host),
        'hostname': str(result._host.name),
        'result':   result._result
      }
    }
    self.report(r)

  def v2_runner_on_start(self, host, task):
    r = {
    'v2_runner_on_start': {
       'host':   str(host.name),
       'role':   str(task._role),
       'action': str(task._attributes['action']),
       'name':   str(task._attributes['name']),
       'args':   str(task._attributes['args']),
       'tags':   str(task._attributes['tags']),
        '_ds':   task._ds if hasattr(task, '_ds') else None,
       'keys':   [ str(x) for x in task._ds.keys() ] if hasattr(task, '_ds') else None
      }
    }
    self.report(r)

  def v2_runner_on_unreachable(self, result):
    host = result._host.get_name()
    r = {
      'v2_runner_on_unreachable': {
        'host': result._host.get_name(),
        'task':   str(result._task),
        'role':   result._task._role,
        'action': result._task._attributes['action'],
        'name': result._task._attributes['name'],
        'args': result._task._attributes['args'],
        'connection': result._task._attributes['connection'],
        'port': result._task._attributes['port'],
        'remote_user': result._task._attributes['remote_user'],
      }
    }
    self.report(r)

  def v2_playbook_on_stats(self, stats, *args, **kwargs):
    host_stats = []
    for host in sorted(stats.processed.keys()):
      host_stats.append({
        host: stats.summarize(host)
      })
    r = {
      'v2_playbook_on_stats': {
        'stats': host_stats
      }
    }
    self.report(r)

context.CLIARGS = ImmutableDict(
  become_method=None,
  become=None,
  become_user=None,
  check=False,
  connection='local',  # local, smart
  diff=False,
  forks=10,
  timeout=10,
  module_path=['/to/mymodules'],
  nocolor=True,
  start_at_task=None,
  syntax=False,
  verbosity=environ.get('ANSIBLE_VERBOSITY', 6),
)

class PlaybookRunner():

  def __init__(self,
      playbook_files=['./site.yml'],
      inventory_sources=['hosts.sh'],
      vault_password=None,
    ):
    self.playbook_files = playbook_files
    self.inventory_sources = inventory_sources
    self.vault_password = vault_password
    self.loader = DataLoader()
    self.inventory = InventoryManager(loader=self.loader, sources=self.inventory_sources)
    self.results_callback = ResultsCallback()
    self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

  def run(self):
    try:
      pbex = PlaybookExecutor(
        inventory=self.inventory,
        loader=self.loader,
        passwords={ 'vault_password': self.vault_password },
        playbooks=self.playbook_files,
        variable_manager=self.variable_manager,
      )

      tqm = pbex._tqm
      tqm._stdout_callback = self.results_callback

      pbex.run()

      # if tqm and hasattr(tqm, 'send_callback'):
      #   tqm.send_callback('playbook_on_exception', exception=e)

    finally:

      # if hasattr(self.results_callback, 'results'):
      #   print(json.dumps({
      #     'results': self.results_callback.results
      #   }, indent=2))

      if tqm is not None:
        tqm.cleanup()

      if self.loader is not None:
        self.loader.cleanup_all_tmp_files()

      shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

if __name__ == '__main__':
  runner = PlaybookRunner()
  runner.run()
  print(json.dumps(runner.results_callback.results, indent=2))

