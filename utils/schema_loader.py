#! /usr/bin/env python

# -*- coding: python -*-
# -*- coding: utf-8 -*-

import copy
import json
import jsonref
import yaml

import os.path

def dirname(file):
  return os.path.dirname(os.path.realpath(file))

def cwd(file=__file__):
  return dirname(file)

class SchemaLoader():
  '''
  Helper to load (json) schema files represented as
  YAML from the caller's current directory
  '''
  def __init__(self, api, dir):
    self.api = api
    self.dir = dir

  def load(self, data, title=None):
    obj = yaml.load(data, Loader=yaml.SafeLoader)
    title = obj['title'] = obj.get('title', title if title else 'NoneSchema')
    res_obj = jsonref.loads(json.dumps(obj))
    return self.api.schema_model(title, copy.deepcopy(res_obj))

  def load_from_file(self, file, title=None):
    file = os.path.join(self.dir, file)
    with open(file) as fp:
      return self.load( data=fp.read(), title=title )
