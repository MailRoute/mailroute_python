# -*- coding: utf-8 -*-

class ResellerMixin(object):

    def create_admin(self, email, send_welcome):
        pass

    def delete_admin(self, email):
        pass

    def create_contact(self, params):
        pass

    def create_customer(self, params):
        pass

class CustomerMixin(object):

    def create_admin(self, email, send_welcome):
        pass

    def delete_admin(self, email):
        pass

    def create_contact(self, params):
        pass

    def create_domain(self, params):
        pass

class DomainMixin(object):

    def get_quaranine():
        pass

    def move_to_customer(self, target_customer):
        pass

    def create_contact(self, params):
        pass

    def create_mailserver(self, params):
        pass

    def create_outbound_server(self, params_or_ip):
        if isinstance(params_or_ip, basestring):
            ip = params_or_ip
        else:
            params = params_or_ip

    def create_email_account(self, params):
        pass

    def bulk_create_email_account(self, params_list):
        pass

    def create_alias(self, params):
        pass

    def add_to_blacklist(self, email):
        pass

    def add_to_whitelist(self, email):
        pass
