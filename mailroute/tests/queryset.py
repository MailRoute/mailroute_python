# -*- coding: utf-8 -*-
import sure
import json
import uuid
import unittest
import mailroute
import httpretty
import contextlib
from mailroute.tests import base

class TestQueries(base.AccessTest):

    ResClass = None

    class Resource(object):
        def __init__(self, RClass, use_prefix=None):
            self._RClass = RClass
            if use_prefix is None:
                self._uniq = uuid.uuid4().hex
            else:
                self._uniq = use_prefix

        @property
        def address(self):
            return 'https://ci.mailroute.net/api/v1/{0}/'.format(self._RClass.Entity.entity_name())

        def generate(self, N, suffix='A'):
            raise NotImplementedError

        def name(self, suffix='A'):
            return '{0} {resname} {1}'.format(self._uniq, suffix,
                                              resname=self._RClass.__name__)

        @contextlib.contextmanager
        def named(self, *args, **kwargs):
            objs, names = self.generate(*args, **kwargs)
            yield objs, names

            for reseller in objs:
                try:
                    reseller.delete()
                except:
                    pass

        @contextlib.contextmanager
        def wrapper(self, *args, **kwargs):
            with self.named(*args, **kwargs) as (objs, names):
                yield objs

        def filter_prefixed(self, tail=''):
            raise NotImplementedError

        def field(self, obj):
            raise NotImplementedError

    def test_limits(self):
        N = 15
        res = self.Resource(self.ResClass)

        with res.wrapper(N):
            query = res.filter_prefixed().all()
            len(query.fetch()).should.be.equal(N)
            resellers = query.limit(1)
            len(resellers).should.be.equal(1)
            resellers = query.limit(N)
            len(resellers).should.be.equal(N)
            resellers = query.limit(2 * N) # there are no more items with such prefix
            len(resellers).should.be.equal(N)

            resellers = query.limit(1).limit(2)
            len(resellers).should.be.equal(1)
            resellers = query.limit(1).offset(1)
            len(resellers).should.be.equal(1)
            resellers = query.limit(1).offset(N)
            len(resellers).should.be.equal(0)
            resellers = query.limit(1).offset(N - 1)
            len(resellers).should.be.equal(1)

    def test_filter(self):
        N = 15

        res = self.Resource(self.ResClass)

        with res.wrapper(N, suffix='A'):
            with res.wrapper(N, suffix='B'):
                resellers = res.filter_prefixed()
                len(resellers).should.be.equal(2 * N)
                resellers = res.filter_prefixed(tail='A')
                len(resellers).should.be.equal(N)
                resellers = res.filter_prefixed(tail='B')
                len(resellers).should.be.equal(N)
                resellers = res.filter_prefixed(tail='B').limit(3)
                len(resellers).should.be.equal(3)
                resellers = res.filter_prefixed(tail='B').limit(3).offset(2)
                len(resellers).should.be.equal(3)

                resellers = res.filter_prefixed(tail='Nothing')
                resellers.should.be.empty

                resellers = res.filter_prefixed(tail='A N0')
                len(resellers).should.be.equal(1)
                res.field(resellers[0]).should.be.equal(res.name(suffix='A N0'))

    @httpretty.httprettified
    def test_all_empty(self):
        res = self.Resource(self.ResClass)
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, res.address,
                                         status=200, body=json.dumps({
                                             'meta': {
                                                 'limit': 20,
                                                 'next': None,
                                                 'offset': 0,
                                                 'previous': None,
                                                 'total_count': 0,
                                                 },
                                             'objects': []
                                             }),
                                         content_type='application/json')
        query = self.ResClass.all()
        query.should.be.empty
        query.fetch().should.be.empty

    def test_all(self):
        ename = self.ResClass.Entity.entity_name()
        res = self.Resource(self.ResClass)
        with open('tests/data/all/{0}.json'.format(ename)) as f:
            answer = json.loads(f.read())

            query = self.ResClass.Entity.is_actual() # force to load schema
            httpretty.HTTPretty.enable()
            httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, res.address,
                                             status=200, body=json.dumps(answer),
                                             content_type='application/json')
            query = self.ResClass.all()
            len(query).should.be.equal(answer['meta']['total_count'])
            httpretty.HTTPretty.disable()

    def test_get(self):
        res = self.Resource(self.ResClass)

        with res.wrapper(1):
            resellers = res.filter_prefixed().limit(20)

            resellers.should_not.be.empty
            resellers.should.have.property('__iter__')

            for person in resellers[:10]:
                person.should.have.property('id')
                pk = person.id
                same_entity = self.ResClass.get(id=pk)
                same_entity.should.be.equal(person)

    def test_delete(self):
        res = self.Resource(self.ResClass)

        with res.wrapper(1):
            resellers = res.filter_prefixed()
            resellers.should_not.be.empty

            (person,) = resellers
            old_id = person.id
            person.delete().should.be.ok
            person.id.should.be.none
            person.delete().should_not.be.ok
            person.id.should.be.none
            # try to double delete it again
            self.ResClass.delete.when.called_with([old_id]).should.throw(mailroute.DeleteError)

            resellers = res.filter_prefixed()
            resellers.should.be.empty
            another_prefix = uuid.uuid4().hex
            res_another = self.Resource(self.ResClass, use_prefix=another_prefix)
            resellers = res_another.filter_prefixed()
            resellers.should.be.empty

    def test_mass_deletion_by_instance(self):
        N = 5
        res = self.Resource(self.ResClass)

        with res.wrapper(N):
            resellers = res.filter_prefixed()
            len(resellers).should.be.equal(N)

            self.ResClass.delete(resellers)

            resellers = res.filter_prefixed()
            resellers.should.be.empty

    def test_mass_deletion_by_pk(self):
        N = 5
        res = self.Resource(self.ResClass)

        with res.wrapper(N):
            resellers = res.filter_prefixed()
            len(resellers).should.be.equal(N)

            self.ResClass.delete([obj.id for obj in resellers])

            resellers = res.filter_prefixed()
            resellers.should.be.empty

    def test_create(self):
        N = 3
        res = self.Resource(self.ResClass)

        with res.named(N) as (resellers, names):
            for new_name, new_one in zip(names, resellers):
                new_one.should.be.a(self.ResClass.Entity)
                res.field(new_one).should.be.equal(new_name)
                new_one.should.be.equal(new_one)
                new_one.should.be.equal(self.ResClass.get(id=new_one.id))
            resellers = res.filter_prefixed()
            len(resellers).should.be.equal(N)

    def test_sorting(self):
        N = 15
        res = self.Resource(self.ResClass)

        with res.wrapper(N, suffix='A'):
            with res.wrapper(N, suffix='B'):
                resellers = res.filter_prefixed().order_by('name')
                list(resellers).should.be.equal(sorted(resellers, key=lambda obj: res.field(obj)))

                resellers = res.filter_prefixed().order_by('-name')
                list(resellers).should.be.equal(sorted(resellers, key=lambda obj: res.field(obj), reverse=True))

                resellers = res.filter_prefixed().order_by('created_at')
                list(resellers).should.be.equal(sorted(resellers, cmp=lambda obj1, obj2: cmp(obj1.created_at, obj2.created_at)))

                res.filter_prefixed().order_by.when.called_with('some_wrong_field'). \
                    should.throw(mailroute.InvalidOrder)
