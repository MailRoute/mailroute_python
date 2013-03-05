# -*- coding: utf-8 -*-

class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class InvalidQueryError(Exception):
    pass


class OperationError(Exception):
    pass


class NotUniqueError(OperationError):
    pass


class QNode(object):
    def get(self):
        pass

    def create(self):
        pass

    def bulk_create(self):
        pass

    def all(self):
        return QuerySet()

    def filter(self, **options):
        return QuerySet(**options)

    def delete(self):
        pass

class QuerySet(QNode):

    def limit(self):
        pass

    def offset(self):
        pass

    def order_by(self):
        pass

