# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField

__all__ = ['NotificationAccountTask', 'NotificationDomainTask',]

class NotificationAccountTask(QuerySet):
    class NotificationAccountTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_account_task'

        email_account = ForeignField(to_collection='resources.email_account.EmailAccount', related_name='notification_tasks')
        enabled = SmartField()
        priority = SmartField()

class NotificationDomainTask(QuerySet):
    class NotificationDomainTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_domain_task'

        domain = ForeignField(to_collection='resources.domain.Domain', related_name='notification_tasks')
        enabled = SmartField()
        priority = SmartField()
