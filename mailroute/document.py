# -*- coding: utf-8 -*-
from queryset import QuerySet, QNode

class BaseDocument(QNode):

    def __init__(self):
        pass

    def __getattribute__(self, name):
        pass
