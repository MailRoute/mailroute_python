# -*- coding: utf-8 -*-

class ResellerMixin(object):

    def create_admin(self, email, send_welcome):
        return self.admins.create(email=email, send_welcome=send_welcome)

    def delete_admin(self, email):
        (admin_obj,) = self.admins.filter(email=email)
        return admin_obj.delete()

    def create_contact(self, params):
        return self.contacts.create(reseller=self, **params)

    def create_customer(self, params):
        return self.customers.create(reseller=self, **params)

class CustomerMixin(object):

    def create_admin(self, email, send_welcome):
        return self.admins.create(email=email, send_welcome=send_welcome)

    def delete_admin(self, email):
        return admin_obj.delete()

    def create_contact(self, params):
        return self.contacts.create(reseller=self, **params)

    def create_domain(self, params):
        return self.customers.create(reseller=self, **params)

class DomainMixin(object):

    def get_quaranine():
        pass

    def move_to_customer(self, target_customer):
        self.customer = target_customer
        self.save()

    def create_contact(self, params):
        return self.contacts.create(domain=self, **params)

    def create_mailserver(self, params):
        return self.mail_servers.create(domain=self, **params)

    def create_outbound_server(self, params_or_ip):
        if isinstance(params_or_ip, basestring):
            ip = params_or_ip
            return self.outbound_servers.create(domain=self, {'server': ip})
        else:
            params = params_or_ip
            return self.mail_servers.create(domain=self, **params)

    def create_email_account(self, params):
        return self.email_accounts.create(domain=self, **params)

    def bulk_create_email_account(self, params_list):
        for params in params_list:
            self.create_email_account(params)

    def create_alias(self, params):
        return self.domain_aliases.create(domain=self, **params)

    def add_to_blacklist(self, email):
        pass

    def add_to_whitelist(self, email):
        pass
