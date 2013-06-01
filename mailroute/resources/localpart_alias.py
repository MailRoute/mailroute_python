# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['LocalPartAlias',]

class LocalPartAlias(QuerySet):
    class LocalPartAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'localpart_alias'

        domain = OneToOne(to_collection='resources.domain.Domain')
        email_account = ForeignField(to_collection='resources.email_account.EmailAccount', back_to='localpart_aliases')
        localpart = SmartField()
        type = SmartField()

    Entity = LocalPartAliasEntity
