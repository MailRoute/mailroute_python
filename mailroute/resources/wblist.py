# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['WBList',]

class WBList(QuerySet):
    class WBListEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'wblist'

        wb = SmartField(required=True)
        mail_address = SmartField(required=True)
        email_account = ForeignField(name='mail_addr', to_collection='resources.email_account.EmailAccount', back_to='wblist')
        domain = ForeignField(to_collection='resources.domain.Domain', back_to='wblist')

    Entity = WBListEntity
