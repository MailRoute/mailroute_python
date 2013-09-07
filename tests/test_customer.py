# -*- coding: utf-8 -*-
import sure
import json
import uuid
import unittest
import mailroute
import httpretty
from mailroute.resources import contacts
from tests import queryset

class TestCustomMethods(queryset.TestQueries):

    ResClass = mailroute.Customer

    class Resource(queryset.TestQueries.Resource):

        def generate(self, N, suffix='A'):
            objs = []
            names = []
            for i in xrange(N):
                new_name = '{1} {resname} {2} N{0}'.format(i, self._uniq, suffix,
                                                           resname=self._RClass.__name__)
                new_one = mailroute.Customer.create(name=new_name)
                names.append(new_name)
                objs.append(new_one)
            return objs, names

        def filter_prefixed(self, tail=''):
            if tail:
                tail = ' ' + tail
            query = mailroute.Customer.filter(name__startswith='{0} {resname}{tail}'. \
                format(self._uniq, resname=self._RClass.__name__, tail=tail)).all()
            return query

        def field(self, obj):
            return obj.name

    def test_mass_create(self):
        N = 5
        prefix = uuid.uuid4().hex

        new_names = []
        for i in xrange(N):
            new_names.append('{1} Customer N{0}'.format(i, prefix))

        self.ResClass.bulk_create([{'name': name} for name in new_names])
        customers = self.ResClass.filter(name__startswith='{0} Customer N'.format(prefix))
        len(customers).should.be.equal(N)
        set(obj.name for obj in customers.fetch()).should.be.equal(set(new_names))


if __name__ == '__main__':
    unittest.main()
