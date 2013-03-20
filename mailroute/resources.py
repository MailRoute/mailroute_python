# -*- coding: utf-8 -*-
from queryset import QuerySet
from document import BaseDocument, SmartField

class Branding(QuerySet):
    class BrandingEntity(BaseDocument):
        class Meta:
            entity_name = 'brandinginfo'

        color = SmartField()
        customer = SmartField()
        domain = SmartField()
        email_from = SmartField()
        enabled = SmartField()
        favicon = SmartField()
        highlight_color = SmartField()
        logo = SmartField()
        reseller = SmartField(to_collection='Reseller')
        service_name = SmartField()
        ssl_cert_passphrase = SmartField()
        subdomain = SmartField()

    Entity = BrandingEntity


class Reseller(QuerySet):
    class ResellerEntity(BaseDocument):
        class Meta:
            entity_name = 'reseller'

        name = SmartField(required=True)
        allow_customer_branding = SmartField()
        allow_branding = SmartField()
        branding_info = SmartField(to_collection=Branding)
    Entity = ResellerEntity

class Admins(QuerySet):
    class AdminsEntity(BaseDocument):
        class Meta:
            entity_name = 'admins'

    Entity = AdminsEntity

class ContactCustomer(QuerySet):
    class ContactCustomerEntity(BaseDocument):
        class Meta:
            entity_name = 'contact_customer'

    Entity = ContactCustomerEntity

class ContactDomain(QuerySet):
    class ContactDomainEntity(BaseDocument):
        class Meta:
            entity_name = 'contact_domain'

    Entity = ContactDomainEntity

class ContactEmailAccount(QuerySet):
    class ContactEmailAccountEntity(BaseDocument):
        class Meta:
            entity_name = 'contact_email_account'

    Entity = ContactEmailAccountEntity

class ContactReseller(QuerySet):
    class ContactResellerEntity(BaseDocument):
        class Meta:
            entity_name = 'contact_reseller'

    Entity = ContactResellerEntity

class Customer(QuerySet):
    class CustomerEntity(BaseDocument):
        class Meta:
            entity_name = 'customer'

    Entity = CustomerEntity

class Domain(QuerySet):
    class DomainEntity(BaseDocument):
        class Meta:
            entity_name = 'domain'

    Entity = DomainEntity

class DomainAlias(QuerySet):
    class DomainAliasEntity(BaseDocument):
        class Meta:
            entity_name = 'domain_alias'

    Entity = DomainAliasEntity

class DomainWithAlias(QuerySet):
    class DomainWithAliasEntity(BaseDocument):
        class Meta:
            entity_name = 'domain_with_alias'

    Entity = DomainWithAliasEntity

class EmailAccount(QuerySet):
    class EmailAccountEntity(BaseDocument):
        class Meta:
            entity_name = 'email_account'

    Entity = EmailAccountEntity

class LocalPartAlias(QuerySet):
    class LocalPartAliasEntity(BaseDocument):
        class Meta:
            entity_name = 'local_part_alias'

    Entity = LocalPartAliasEntity

class MailServer(QuerySet):
    class MailServerEntity(BaseDocument):
        class Meta:
            entity_name = 'mail_server'

    Entity = MailServerEntity

class NotificationAccountTask(QuerySet):
    class NotificationAccountTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_account_task'

    Entity = NotificationAccountTaskEntity

class NotificationDomainTask(QuerySet):
    class NotificationDomainTaskEntity(BaseDocument):
        class Meta:
            entity_name = 'notification_domain_task'

    Entity = NotificationDomainTaskEntity

class OutboundServer(QuerySet):
    class OutboundServerEntity(BaseDocument):
        class Meta:
            entity_name = 'outboundserver'

    Entity = OutboundServerEntity

class PolicyDomain(QuerySet):
    class PolicyDomainEntity(BaseDocument):
        class Meta:
            entity_name = 'policydomain'

    Entity = PolicyDomainEntity

class PolicyUser(QuerySet):
    class PolicyUserEntity(BaseDocument):
        class Meta:
            entity_name = 'policyuser'

    Entity = PolicyUserEntity

class Quarantine(QuerySet):
    class QuarantineEntity(BaseDocument):
        class Meta:
            entity_name = 'quarantine'

    Entity = QuarantineEntity

class QuarantineMessage(QuerySet):
    class QuarantineMessageEntity(BaseDocument):
        class Meta:
            entity_name = 'quarantine_message'

    Entity = QuarantineMessageEntity

class QuarantineReadonly(QuerySet):
    class QuarantineReadonlyEntity(BaseDocument):
        class Meta:
            entity_name = 'quarantine_readonly'

    Entity = QuarantineReadonlyEntity

class QuarantineReadonlyMessage(QuerySet):
    class QuarantineReadonlyMessageEntity(BaseDocument):
        class Meta:
            entity_name = 'quarantine_readonly_message'

    Entity = QuarantineReadonlyMessageEntity

class WBList(QuerySet):
    class WBListEntity(BaseDocument):
        class Meta:
            entity_name = 'wblist'

    Entity = WBListEntity

#__all__ = []
