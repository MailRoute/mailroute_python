# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['Admins',]

class Admins(VirtualQuerySet):
    class AdminsEntity(VirtualDocument):
        class Meta:
            entity_name = 'admins'
            # TODO: it's not really fully ignored fields, rename this property according to the real meaning
            ignored = ('reseller', 'customer')

        date_joined = SmartField()
        email = SmartField()
        is_active = SmartField()
        last_login = SmartField()
        send_welcome = SmartField()
        username = SmartField()
        reseller = ForeignField(to_collection='resources.reseller.Reseller', back_to='admins')
        customer = ForeignField(to_collection='resources.customer.Customer', back_to='admins')

    Entity = AdminsEntity
