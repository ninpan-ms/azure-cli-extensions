# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._util_enterprise import (is_enterprise_tier, get_client)
from .custom import (certificate_add as custom_certificate_add,
                     certificate_show as custom_certificate_show,
                     certificate_list as custom_certificate_list,
                     certificate_remove as custom_certificate_remove,
                     certificate_list_reference_app as custom_certificate_list_reference_app)
from knack.log import get_logger
from .vendored_sdks.appplatform.v2022_01_01_preview import models as models_20220101preview
from .vendored_sdks.appplatform.v2021_09_01_preview import models as models_20210901preview

logger = get_logger(__name__)


def certificate_add(cmd, client, resource_group, service, name, only_public_cert=None,
                    vault_uri=None, vault_certificate_name=None, public_certificate_file=None):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return custom_certificate_add(cmd, client, resource_group, service, name, models, only_public_cert,
                    vault_uri, vault_certificate_name, public_certificate_file)


def certificate_show(cmd, client, resource_group, service, name):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return custom_certificate_show(cmd, client, resource_group, service, name)


def certificate_list(cmd, client, resource_group, service, certificate_type=None):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return custom_certificate_list(cmd, client, resource_group, service, certificate_type)


def certificate_remove(cmd, client, resource_group, service, name):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return custom_certificate_remove(cmd, client, resource_group, service, name)


def certificate_list_reference_app(cmd, client, resource_group, service, name):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return custom_certificate_list_reference_app(cmd, client, resource_group, service, name)
