#!/usr/bin/env python
from flask import Blueprint

game = Blueprint('game', __name__)

from . import views
