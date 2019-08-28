#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from flask import Blueprint, Flask
from flask_restplus import Api, Namespace, Resource, fields

from .. import common

api = Namespace('api/v2', description='API V2 Namespace')

# api_v2 = Blueprint('api', __name__, url_prefix='/api/v2')
# api.register_blueprint(api_v2)

@api.route('/')
class Health(Resource):

  def get(self):
    common.get()
