# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['NotificationAccountTask', 'NotificationDomainTask',]

class NotificationAccountTask(QuerySet):
    class NotificationAccountTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_account_task'

        email_account = OneToOne(to_collection='resources.email_account.EmailAccount')
        enabled = SmartField()
        priority = SmartField()

    Entity = NotificationAccountTaskEntity

class NotificationDomainTask(QuerySet):
    class NotificationDomainTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_domain_task'

        domain = OneToOne(to_collection='resources.domain.Domain')
        enabled = SmartField()
        priority = SmartField()

    Entity = NotificationDomainTaskEntity
