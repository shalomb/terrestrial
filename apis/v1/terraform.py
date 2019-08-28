#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import json

from utils.command_runner import run

class Terraform(object):

  def __init__(self):
    self.stack = 'Some Stack'
    self.results = []
    self.cwd = os.getcwd()
    self.tfplan = 'tfplan'
    # NOTE TF_CLI_ARGS cannot be used as it breaks provisioners
    # https://github.com/hashicorp/terraform/issues/14847#issuecomment-412957421
    self.env = {
      'TF_CLI_ARGS_apply': '-no-color',
      'TF_CLI_ARGS_destroy': '-no-color',
      'TF_CLI_ARGS_init': '-no-color',
      'TF_CLI_ARGS_output': '-no-color',
      'TF_CLI_ARGS_plan': '-no-color',
      'TF_CLI_ARGS_state': '-no-color',
      'TF_CLI_CONFIG_FILE': './terraformrc',
      'TF_IN_AUTOMATION': 'yes',
      'TF_INPUT': '0',
      'TF_LOG': 'TRACE', # TRACE, DEBUG, INFO, WARN, ERROR
      'TF_LOG_PATH': './terraform.log',
    }
    # TF_LOG=DEBUG # {INFO,WARNING,DEBUG,TRACE}
    # TF_LOG_PATH="terraform.log"

  def terraform(self, *args, **kwargs):
    cmd = ['terraform', *(x for list in map(str.split, args) for x in list)]
    r = run(cmd=cmd, cwd=self.cwd, env=self.env)
    if kwargs.pop('json_output', None):
      if r['exit_status'] == 0 and r['stdout']:
        r['stdout'] = json.loads(''.join(r['stdout']))
    self.results.append({' '.join(cmd): r})
    return r

  def setup(self, *args, **kwargs):
    self.version()
    openrc = kwargs.get('openrc')
    # print(f'openrc: {openrc}')
    # with open('openrc.tfvars.json', 'w') as f:
    #   f.write( json.dumps(openrc) )
    return {}

  def version(self):
    return self.terraform('version')

  def init(self):
    r = self.terraform('init -reconfigure -lock=true -verify-plugins=true -get-plugins=true -backend=true')
    self.providers_schema()
    return r

  def validate(self):
    return self.terraform('validate -json', json_output=True)

  def providers_schema(self):
    return self.terraform('providers schema -json', json_output=True)

  def plan(self):
    plan = self.terraform(f'plan -lock=true -out={self.tfplan} -refresh=true')
    self.show_plan()
    self.state_pull()
    return plan

  def show_plan(self):
    return self.terraform(f'show -json {self.tfplan}', json_output=True)

  def apply(self):
    return self.terraform(f'apply -lock=true {self.tfplan}')

  def output(self):
    return self.terraform('output -json', json_output=True)

  def state_pull(self):
    return self.terraform('state pull', json_output=True)

  def destroy(self):
    plan = self.terraform(f'plan -destroy -lock=true -out={self.tfplan} -refresh=true')
    self.show_plan()
    self.state_pull()
    destroy = self.terraform('destroy -lock=true -refresh=true -auto-approve')
    return [plan, destroy]

  def collect_logs(self):
    logs = run(cmd=['cat', 'terraform.log'], cwd=self.cwd)
    self.results.append({'cat terraform.log': logs})

