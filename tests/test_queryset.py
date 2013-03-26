# -*- coding: utf-8 -*-
import sure
import json
import uuid
import unittest
import mailroute
import httpretty

class TestQueries(unittest.TestCase):

    ACCESS_USER = ('test_python', 'e7b46a7392629c144ee8237454b7888a30f93e69')

    def setUp(self):
        mailroute.configure(*self.ACCESS_USER, server='https://ci.mailroute.net')

    def test_limits(self):
        N = 15
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller A N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

        query = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)).all()
        len(query.fetch()).should.be.equal(N)
        resellers = query.limit(0)
        len(resellers).should.be.equal(0)
        resellers = query.limit(1)
        len(resellers).should.be.equal(1)
        resellers = query.limit(N)
        len(resellers).should.be.equal(N)
        resellers = query.limit(2 * N)
        len(resellers).should.be.equal(N)

        resellers = query.limit(1).limit(2)
        len(resellers).should.be.equal(1)
        resellers = query.limit(1).offset(1)
        len(resellers).should.be.equal(1)
        resellers = query.limit(1).offset(N)
        len(resellers).should.be.equal(0)
        resellers = query.limit(1).offset(N - 1)
        len(resellers).should.be.equal(1)

        for reseller in query:
            reseller.delete()

    def test_filter(self):
        N = 15
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller A N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)
            new_name = '{1} Reseller B N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix))
        len(resellers).should.be.equal(2 * N)
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller A'.format(prefix))
        len(resellers).should.be.equal(N)
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller B'.format(prefix))
        len(resellers).should.be.equal(N)
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller B'.format(prefix)).limit(3)
        len(resellers).should.be.equal(3)
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller B'.format(prefix)).limit(3).offset(2)
        len(resellers).should.be.equal(3)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Nothing'.format(prefix))
        resellers.should.be.empty

        resellers = mailroute.Reseller.filter(name='{0} Reseller A N0'.format(prefix))
        len(resellers).should.be.equal(1)
        resellers[0].name.should.be.equal('{0} Reseller A N0'.format(prefix))

        mailroute.Reseller.filter.when.called_with(branding_info__color='red').should. \
                                    throw('InvalidFilter')

        for reseller in mailroute.Reseller.filter(name__startswith='{0}'.format(prefix)):
            reseller.delete()

    @httpretty.httprettified
    def test_all_empty(self):
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/reseller/',
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
        query = mailroute.Reseller.all()
        query.should.be.empty
        query.fetch().should.be.empty

    def test_all(self):
        obj = {
            "absolute_url": "/reseller/615/", 
            "allow_branding": False, 
            "allow_customer_branding": False, 
            "branding_info": "/api/v1/brandinginfo/622/", 
            "contacts": [], 
            "created_at": "Fri, 22 Mar 2013 18:39:01 -0700", 
            "customers": [], 
            "id": 615, 
            "name": "095eeef1d4204022a2a4e028de9ef2eb Reseller N0", 
            "resource_uri": "/api/v1/reseller/615/", 
            "updated_at": "Fri, 22 Mar 2013 18:39:01 -0700"
        }

        query = mailroute.Reseller.Entity.is_actual() # force to load schema
        httpretty.HTTPretty.enable()
        PAGE = 20
        httpretty.HTTPretty.register_uri(httpretty.HTTPretty.GET, 'https://ci.mailroute.net/api/v1/reseller/',
                                         status=200, body=json.dumps({
                                            'meta': {
                                                 'limit': PAGE,
                                                 'next': '/api/v1/reseller/?limit=20&offset=20',
                                                 'offset': 0,
                                                 'previous': None,
                                                 'total_count': PAGE * 3,
                                            }, 
                                            'objects': [obj] * PAGE
                                        }),
                                        content_type='application/json')
        query = mailroute.Reseller.all()
        len(query).should.be.equal(PAGE * 3)
        httpretty.HTTPretty.disable()

    def test_get(self):
        resellers = mailroute.Reseller.filter(name__startswith='Testing').limit(20)
        if not resellers:
            mailroute.Reseller.create(name='Testing reseller')
            resellers = mailroute.Reseller.filter(name__startswith='Testing').limit(20)

        resellers.should_not.be.empty
        resellers.should.have.property('__iter__')

        for person in resellers[:10]:
            person.should.have.property('id')
            pk = person.id
            same_entity = mailroute.Reseller.get(id=pk)
            same_entity.should.be.equal(person)

    def test_delete(self):
        prefix = uuid.uuid4().hex

        person = mailroute.Reseller.create(name='{0} Reseller'.format(prefix))

        resellers = mailroute.Reseller.filter(name='{0} Reseller'.format(prefix))
        resellers.should_not.be.empty

        (person,) = resellers
        old_id = person.id
        person.delete()
        person.id.should.be.none
        person.delete()
        person.id.should.be.none
        # try to double delete it again
        mailroute.Reseller.delete.when.called_with([old_id]).should.throw('DoesNotExist')

        resellers = mailroute.Reseller.filter(name='Testing reseller')
        resellers.should.be.empty

    def test_mass_deletion_by_instance(self):
        N = 5
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        len(resellers).should.be.equal(N)

        mailroute.Reseller.delete(resellers)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        resellers.should.be.empty

    def test_mass_deletion_by_pk(self):
        N = 5
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        len(resellers).should.be.equal(N)

        mailroute.Reseller.delete([obj.id for obj in resellers])

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        resellers.should.be.empty

    def test_create(self):
        N = 3
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller N{0}'.format(i, prefix)

            new_one = mailroute.Reseller.create(name=new_name)
            new_one.should.be.a(mailroute.Reseller.ResellerEntity)
            new_one.name.should.be.equal(new_name)
            new_one.should.be.equal(new_one)
            new_one.should.be.equal(mailroute.Reseller.get(id=new_one.id))
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        len(resellers).should.be.equal(N)

        resellers[0].branding_info.should.be.a(mailroute.Branding.BrandingEntity)
        resellers[0].branding_info.reseller.should.be.equal(resellers[0])
        for reseller in resellers:
            reseller.delete()

    def test_mass_create(self):
        N = 5
        prefix = uuid.uuid4().hex

        new_names = []
        for i in xrange(N):
            new_names.append('{1} Reseller N{0}'.format(i, prefix))

        mailroute.Reseller.bulk_create([{'name': name} for name in new_names])
        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller N'.format(prefix))
        len(resellers).should.be.equal(N)
        set(obj.name for obj in resellers.fetch()).should.be.equal(set(new_names))

    def test_sorting(self):
        N = 15
        prefix = uuid.uuid4().hex

        for i in xrange(N):
            new_name = '{1} Reseller A N{0}'.format(i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

            new_name = '{1} Reseller B N{0}'.format(N - i, prefix)
            new_one = mailroute.Reseller.create(name=new_name)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)).order_by('name')
        list(resellers).should.be.equal(sorted(resellers, key=lambda obj: obj.name))

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)).order_by('-name')
        list(resellers).should.be.equal(sorted(resellers, key=lambda obj: obj.name, reverse=True))

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)).order_by('-name', 'created_at')
        list(resellers).should.be.equal(sorted(resellers, cmp=lambda obj1, obj2: \
                                               -cmp(obj1.name, obj2.name) or cmp(obj1.created_at, obj2.created_at)))

        mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)). \
                                                        order_by.when.called_with('some_wrong_field'). \
                                                        should.throw(mailroute.InvalidOrder)

        resellers = mailroute.Reseller.filter(name__startswith='{0} Reseller'.format(prefix)).order_by('todo__todo')

        for reseller in resellers:
            reseller.delete()


if __name__ == '__main__':
    unittest.main()
