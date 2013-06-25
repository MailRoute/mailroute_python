# -*- coding: utf-8 -*-
from mailroute.queryset import QuerySet, VirtualQuerySet
from mailroute.document import BaseDocument, AbstractDocument, BaseCreatableDocument, VirtualDocument
from mailroute.fields import SmartField, OneToMany, OneToOne, ForeignField, VirtualOneToMany

__all__ = ['EmailAccount',]

class EmailAccount(QuerySet):
    class EmailAccountEntity(BaseCreatableDocument):
        class Meta:
            entity_name = 'email_account'

        change_pwd = SmartField()
        confirm_password = SmartField()
        contact = OneToOne(to_collection='resources.contact.Contact')
        create_opt = SmartField()
        domain = ForeignField(to_collection='resources.domain.Domain', back_to='email_accounts')
        localpart = SmartField()
        localpart_aliases = OneToMany(to_collection='resources.localpart_alias.LocalPartAlias')
        notification_tasks = OneToMany(to_collection='resources.notification_task.NotificationAccountTask')
        password = SmartField()
        policy = OneToOne(to_collection='resources.policy.PolicyUser')
        priority = SmartField()
        send_welcome = SmartField()
        wblist = OneToMany(to_collection='resources.wblist.WBList')
        use_domain_notifications = SmartField()

        def add_alias(local_part):
            self.localpart_aliases.create(email_account=self, local_part=local_part)

        def bulk_add_aliases(local_parts):
            mass_add_callback = self._resource_point().call('mass_add_aliases')
            mass_add_aliases.create({'aliases': list(local_parts)})

        def regenerate_api_key(self):
            res = self._resource_point().call('regenerate_api_key').create({})
            return res['api_key']

        def add_to_blacklist(self, address):
            self.wblist.create(wb='b', mail_address=address, email_account=self)

        def add_to_whitelist(self, address):
            self.wblist.create(wb='w', mail_address=address, email_account=self)

        def set_password(self, new_pass):
            self.password = new_pass
            self.save()

    Entity = EmailAccountEntity

    @classmethod
    def create(cls, *args, **initial):
        if len(args) == 1 and isinstance(args[0], basestring):
            localpart, domain_name = args[0].split('@')
            DomainClass = cls.Entity.domain.find_class(cls)
            domains = DomainClass.filter(name=domain_name)
            if not domains:
                raise Exception, 'TODO'
            else:
                (domain,) = domains

            return super(EmailAccount, cls).create(**{
                'localpart': localpart,
                'domain': domain,
                'create_opt': 'generate_pwd',
            })
        else:
            return super(EmailAccount, cls).create(**initial)
