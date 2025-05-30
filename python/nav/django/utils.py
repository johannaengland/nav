# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011, 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Utility methods for django used in NAV"""

from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse
from django.utils.http import urlencode

from nav.models.profiles import Account, AccountGroup


def reverse_with_query(viewname, **kwargs):
    """Wrapper for django.urls.reverse, but will adapt query arguments from kwargs"""
    baseurl = reverse(viewname)
    getargs = urlencode(kwargs)
    return "{}?{}".format(baseurl, getargs)


def default_account():
    return Account.objects.get(id=Account.DEFAULT_ACCOUNT)


def get_account(request):
    """Returns the account associated with the request"""
    try:
        return request.account
    except AttributeError:
        return default_account()


def is_admin(account):
    """Check if user is a member of the administrator group"""
    return account.groups.filter(pk=AccountGroup.ADMIN_GROUP).count() > 0


def get_verbose_name(model, lookup):
    """Verbose name introspection of ORM models.
    Parameters:
      - model: the django model
      - lookup: name of the field to find verbose name of.

    Foreign key lookups is supported, ie. "othermodel__otherfield"
    """
    if '__' not in lookup:
        return model._meta.get_field(lookup).verbose_name

    foreign_key, lookup = lookup.split('__', 1)
    try:
        foreign_model = model._meta.get_field(foreign_key).remote_field.model
        return get_verbose_name(foreign_model, lookup)
    except FieldDoesNotExist:
        pass

    related = get_all_related_objects(model)
    related += get_all_related_many_to_many_objects(model)
    for obj in related:
        if obj.get_accessor_name() == foreign_key:
            return get_verbose_name(obj.model, lookup)

    raise FieldDoesNotExist


#
# Django version differentiated helper functions:
#
def get_model_and_name(rel):
    """Gets model and name based on django version

    rel in 1.8 is either ManyToOneRel or OneToOneRel
    """
    return rel.related_model, rel.name


def get_all_related_objects(model):
    """Gets all related objects based on django version"""
    return [
        f
        for f in model._meta.get_fields()
        if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
    ]


def get_all_related_many_to_many_objects(model):
    """Gets all related many-to-many objects based on django version"""
    return [
        f
        for f in model._meta.get_fields(include_hidden=True)
        if f.many_to_many and f.auto_created
    ]
