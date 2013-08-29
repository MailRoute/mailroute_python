# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['DomainAlias', 'DomainWithAlias',]

class DomainAlias(QuerySet):
    class DomainAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain_alias'

        active = SmartField()
        domain = ForeignField(to_collection='resources.domain.Domain', back_to='domain_aliases')
        name = SmartField()

    Entity = DomainAliasEntity

class DomainWithAlias(QuerySet):
    class DomainWithAliasEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'domain_with_alias'

        domain = OneToOne(to_collection='resources.domain.Domain')
        name = SmartField()
        type = SmartField()

    Entity = DomainWithAliasEntity
