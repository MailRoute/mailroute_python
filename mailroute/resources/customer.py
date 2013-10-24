# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['Customer',]

class Customer(QuerySet):
    class CustomerEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'customer'

        name = SmartField(required=True)
        allow_branding = SmartField()
        branding_info = OneToOne(to_collection='resources.branding_info.Branding')
        is_full_user_list = SmartField()
        reported_user_count = SmartField()
        reseller = ForeignField(to_collection='resources.reseller.Reseller', related_name='customers')
        contacts = OneToMany(to_collection='resources.contacts.ContactCustomer')
        domains = OneToMany(to_collection='resources.domain.Domain')
        admins = OneToMany(to_collection='resources.admins.Admin')

    def create_admin(self, email, send_welcome):
        return self.admins.create(email=email, send_welcome=send_welcome)

    def delete_admin(self, email):
        return admin_obj.delete()

    def create_contact(self, params):
        return self.contacts.create(reseller=self, **params)

    def create_domain(self, params):
        return self.customers.create(reseller=self, **params)
