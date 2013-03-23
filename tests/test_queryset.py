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
        False.should.be.ok

    def test_filter(self):
        False.should.be.ok

    @httpretty.httprettified
    def test_all_empty(self):
        False.should.be.ok

    @httpretty.httprettified
    def test_all(self):
        False.should.be.ok

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
        False.should.be.ok

    def test_sorting(self):
        False.should.be.ok


if __name__ == '__main__':
    unittest.main()
