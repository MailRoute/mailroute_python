# -*- coding: utf-8 -*-
from connection import configure, get_default_connection
from connection import CanNotInitSchema, UnsupportedVersion, AuthorizationError
from resources import *
from queryset import OperationError, DeleteError, NotUniqueError
