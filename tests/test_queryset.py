# -*- coding: utf-8 -*-
import sure
import json
import unittest
import mailroute
import httpretty

class TestQueries(unittest.TestCase):

    ACCESS_USER = ('test_python', 'e7b46a7392629c144ee8237454b7888a30f93e69')

    def tearUp(self):
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
        resellers = mailroute.Reseller.filter(name='Testing reseller')
        if not resellers:
            mailroute.Reseller.create(name='Testing reseller')
            resellers = mailroute.Reseller.filter(name='Testing reseller')

        resellers.should_not.be.empty

        person = resellers[0]
        old_id = person.id
        person.delete()
        person.id.should.be.none
        person.delete()
        person.id.should.be.none
        # try to double delete it again
        mailroute.Reseller.delete.when.called_with([old_id]).should.throw('DoesNotExist')

        resellers = mailroute.Reseller.filter(name='Testing reseller')
        resellers.should.be.empty

    def test_mass_deletion(self):
        False.should.be.ok

    def test_create(self):
        N = 10
        resellers = mailroute.Reseller.filter(name__startswith='Testing reseller N')
        if not resellers:
            names = set(entity.name for entity in resellers)

            for i in xrange(N):
                new_name = 'Testing reseller N{0}'.format(i)
                if new_name not in names:
                    new_one = mailroute.Reseller.create(name=new_name)
                    new_one.should.be.a('ResellerEntity')
                    new_one.name.should.be.equal(new_name)
            resellers = mailroute.Reseller.filter(name__startswith='Testing reseller N')
        len(resellers).should.be.equal(N)

    def test_mass_create(self):
        False.should.be.ok

    def test_sorting(self):
        False.should.be.ok


if __name__ == '__main__':
    unittest.main()
