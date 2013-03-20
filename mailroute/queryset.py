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


class QuerySet(object):

    def __init__(self, filters={}):
        self._filters = filters
        self._cached = None

    @classmethod
    def get(cls, id):
        # TODO: refactor this
        import connection
        c = connection._default_connection
        o = cls.Entity()
        o._fill(c._grab(c._object_id(cls.Entity.Meta.entity_name, id)))
        return o

    @classmethod
    def create(cls, initial=None):
        if not initial:
            initial = {}
        o = cls.Entity()
        o._fill(initial)
        return o

    def bulk_create(self):
        pass

    @classmethod
    def all(cls):
        return cls()

    @classmethod
    def filter(cls, **options):
        return cls(filters=options)

    @classmethod
    def delete(cls, resources):
        import connection
        c = connection._default_connection
        for entity in resources:
            if isinstance(entity, (basestring, int)):
                oid = str(entity)
                c._remove(c._object_id(cls.Entity.Meta.entity_name, oid))
            else:
                entity.delete()

    # DON'T MAKE THIS METHODS (limit & offset) as classmethods
    def limit(self, num):
        f = dict(self._filters)
        f['limit'] = num
        return self.__class__(filters=f)

    def offset(self, num):
        f = dict(self._filters)
        f['offset'] = num
        return self.__class__(filters=f)

    def order_by(self, rule):
        f = dict(self._filters)
        f['order_by'] = rule
        return self.__class__(filters=f)

    def fetch(self):
        return list(self)

    def __bool__(self):
        return len(self) > 0

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        if self._cached is not None:
            return len(self._cached['objects'])
        else:
            return sum(1 for _ in self)

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            if self._cached is not None:
                return self._cached['objects'][ind]
            else:
                return self.fetch()[ind]
        else:
            return super(QuerySet, self).__getitem__(ind)

    def __iter__(self):
        if self._cached is None:
            import connection
            c = connection._default_connection
            self._cached = ans = c._grab(c._objects(self.__class__.Entity.Meta.entity_name, **self._filters))
        else:
            ans = self._cached

        for info in ans['objects']:
            o = self.__class__.Entity()
            o._fill(info)
            yield o
