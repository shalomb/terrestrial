#!/usr/bin/env python3

obj = {
'tatooine': {
  'description': 'group/cluster of hosts that make up tatooine',
  'hosts': [
    'ahsoka',
    'anakin'
    ],
  'vars': {
    'description':  'group_vars that apply to all tatooines',
    'freighter':    'twilight',
    'mission':      'find shmi',
    'ansible_user': 'unop',
    'ansible_ssh_private_key_file': 'id_ed25519',
    'ansible_connection': 'ssh'
    }
  },
'all': {
  'description': 'Special ansible group of all hosts',
  'hosts': [
    'ahsoka',
    'anakin'
    ],
  'vars': {
    'foo': 'foo is a low precedence var',
    'bar': 'is where the beers are at'
    }
  },
'_meta': {
  'hostvars': {
    'ahsoka': {
      'description':  'host_vars for tatooine ahsoka',
      'ansible_host': 'localhost',
      'status':       'master',
      'ansible_user': 'unop',
      'ansible_connection': 'ssh'
      },
    'anakin': {
      'description':  'host_vars for tatooine anakin',
      'ansible_host': 'localhost',
      'status':       'apprentice',
      'ansible_user': 'unop',
      'ansible_connection': 'ssh'
      }
    }
  }
}

import json
print(json.dumps( obj ))
