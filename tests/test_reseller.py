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

    ResClass = mailroute.Reseller

    class Resource(queryset.TestQueries.Resource):

        def generate(self, N, suffix='A'):
            objs = []
            names = []
            for i in xrange(N):
                new_name = '{1} {resname} {2} N{0}'.format(i, self._uniq, suffix,
                                                           resname=self._RClass.__name__)
                new_one = mailroute.Reseller.create(name=new_name)
                names.append(new_name)
                objs.append(new_one)
            return objs, names

        def filter_prefixed(self, tail=''):
            if tail:
                tail = ' ' + tail
            query = mailroute.Reseller.filter(name__startswith='{0} {resname}{tail}'. \
                format(self._uniq, resname=self._RClass.__name__, tail=tail)).all()
            return query

        def field(self, obj):
            return obj.name

    def test_contacts(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)
        max_l = mailroute.ContactCustomer.Entity.MAX_NAME_LENGTH

        too_long_prefix = prefix + ('.' * max(0, max_l - len(prefix) + 1))
        res_obj.create_contact.when.called_with({
            'email': '{0}@test-mail.com'.format(prefix),
            'first_name': prefix
        }).should.throw(contacts.TooLongError)

        cprefix = prefix[:max_l]
        res_obj.create_contact({
            'email': '{0}@test-mail.com'.format(prefix),
            'first_name': cprefix
        })

        (contact1,) = mailroute.ContactReseller.filter(email='{0}@test-mail.com'.format(prefix))
        contact1.first_name.should.be.equal(cprefix)
        (contact2,) = res_obj.contacts

        contact1.should.be.equal(contact2)

        len(res_obj.contacts.filter(email='{0}@Unknown'.format(prefix))).should.be.equal(0)
        res_obj.contacts.filter.when.called_with(first_name='Unknown').should.throw(mailroute.InvalidFilter)
        res_obj.delete()

    def test_fresh_admins(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)
        list(res_obj.admins).should.be.empty
        res_obj.delete()

    def test_new_admin(self):
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        res_obj = mailroute.Reseller.create(name=new_name)

        ad_mail = '{0}@admin-mail.com'.format(prefix)
        new_admin = res_obj.create_admin(ad_mail, send_welcome=True)
        new_admin.email.should.be.equal(ad_mail)
        new_admin.send_welcome.should.be.true
        new_admin.id.should_not.be.none

        (found_admin,) = mailroute.Admins.filter(email=ad_mail).fetch()
        found_admin.should.be.equal(new_admin)

        res_obj.delete_admin(ad_mail)

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

    def test_branding(self):
        False.should.be.ok      # TODO: stack overflow during the test
        prefix = uuid.uuid4().hex
        new_name = '{0} Reseller'.format(prefix)
        new_one = mailroute.Reseller.create(name=new_name)

        new_one.branding_info.should.be.a(mailroute.Branding.Entity)
        new_one.branding_info.reseller.should.be.equal(new_one)

        mailroute.Reseller.filter.when.called_with(branding_info__color='red').should. \
            throw(mailroute.InvalidFilter)
        new_one.delete()


if __name__ == '__main__':
    unittest.main()
