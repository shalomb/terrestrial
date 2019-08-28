#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import json, make_response
from flask_restplus import Api, Resource

from http import HTTPStatus

from .v1.api  import api as api_v1
from .v2.api  import api as api_v2
from .health  import api as api_health

api = Api()

api.add_namespace(api_v1)
api.add_namespace(api_v2)
api.add_namespace(api_health)

@api.route('/swagger')
class Swagger(Resource):
  @api.doc(
    id='Get swagger JSON',
    responses={200: 'OK'},
    description='''
    Retrieve the swagger JSON object
    '''
  )
  def get(self):
    r = json.dumps(api.__schema__, indent=2)
    r = make_response( r, HTTPStatus.OK )
    r.headers['Content-Type'] = 'application/json'
    return r

@api.route('/postman')
class Swagger(Resource):
  @api.doc(
    id='Get Postman representation',
    responses={200: 'OK'},
    description='''
    Retrieve the Postman JSON object
    '''
  )
  def get(self):
    data = api.as_postman(urlvars=True, swagger=True)
    r = json.dumps(data, indent=2)
    r = make_response( r, HTTPStatus.OK )
    r.headers['Content-Type'] = 'application/json'
    return r

