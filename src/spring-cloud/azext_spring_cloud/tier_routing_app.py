# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._util_enterprise import (is_enterprise_tier, get_client)
from ._enterprise import (app_get_enterprise, app_list_enterprise, app_create_enterprise, 
                          app_update_enterprise, app_scale_enterprise, app_deploy_enterprise,
                          app_start_enterprise, app_stop_enterprise, app_restart_enterprise)
from .custom import (app_get as app_get_standard, app_list as app_list_standard, 
                     app_create as app_create_standard, app_update as app_update_standard, 
                     app_scale as app_scale_standard, app_deploy as app_deploy_standard,
                     app_delete as app_delete_standard, app_restart as app_restart_standard,
                     app_start as app_start_standard, app_stop as app_stop_standard,
                     app_identity_assign as identity_assign,
                     app_identity_remove as identity_remove,
                     app_identity_show as identity_show,
                     domain_bind as domain_bind,
                     domain_show as domain_show,
                     domain_list as domain_list,
                     domain_update as domain_update,
                     domain_unbind as domain_unbind,
                     app_append_loaded_public_certificate as append_loaded_public_certificate)
from knack.log import get_logger
from .vendored_sdks.appplatform.v2022_01_01_preview import models as models_20220101preview
from .vendored_sdks.appplatform.v2021_09_01_preview import models as models_20210901preview

logger = get_logger(__name__)


def app_get(cmd, client,
            resource_group,
            service, name):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_get_enterprise(cmd, get_client(cmd), resource_group, service, name)
    else:
        return app_get_standard(cmd, client, resource_group, service, name)


def app_list(cmd, client, resource_group, service):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_list_enterprise(cmd, get_client(cmd), resource_group, service)
    else:
        return app_list_standard(cmd, client, resource_group, service)


def app_create(cmd, client, resource_group, service, name,
               assign_endpoint=None,
               cpu=None,
               memory=None,
               instance_count=None,
               runtime_version=None,
               jvm_options=None,
               env=None,
               enable_persistent_storage=None,
               assign_identity=None):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, enable_persistent_storage assign_ideneity not support
        return app_create_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                     assign_endpoint, cpu, memory, instance_count, jvm_options, 
                                     env, assign_identity)
    else:
        return app_create_standard(cmd, client, resource_group, service, name,
                                   assign_endpoint, cpu, memory, instance_count, runtime_version, 
                                   jvm_options, env, enable_persistent_storage, assign_identity)


def app_update(cmd, client, resource_group, service, name,
               assign_endpoint=None,
               deployment=None,
               runtime_version=None,
               jvm_options=None,
               main_entry=None,
               env=None,
               config_file_patterns=None,
               enable_persistent_storage=None,
               https_only=None,
               enable_end_to_end_tls=None):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, enable_persistent_storage, main_entry, https_only, enable_end_to_end_tls not support
        return app_update_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                     assign_endpoint, deployment, jvm_options, env, config_file_patterns)
    else:
        return app_update_standard(cmd, client, resource_group, service, name,
                                   assign_endpoint, deployment, runtime_version, jvm_options,
                                   main_entry, env, enable_persistent_storage,
                                   https_only, enable_end_to_end_tls)


def app_delete(cmd, client,
               resource_group,
               service,
               name):
    client = get_client(cmd) if is_enterprise_tier(cmd, resource_group, service) else client
    return app_delete_standard(cmd, client, resource_group, service, name)


def app_start(cmd, client,
              resource_group,
              service,
              name,
              deployment=None,
              no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_start_enterprise(cmd, get_client(cmd), resource_group, service, name, deployment, no_wait)
    else:
        return app_start_standard(cmd, client, resource_group, service, name, deployment, no_wait)


def app_stop(cmd, client,
             resource_group,
             service,
             name,
             deployment=None,
             no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_stop_enterprise(cmd, get_client(cmd), resource_group, service, name, deployment, no_wait)
    else:
        return app_stop_standard(cmd, client, resource_group, service, name, deployment, no_wait)


def app_restart(cmd, client,
                resource_group,
                service,
                name,
                deployment=None,
                no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_restart_enterprise(cmd, get_client(cmd), resource_group, service, name, deployment, no_wait)
    else:
        return app_restart_standard(cmd, client, resource_group, service, name, deployment, no_wait)


def app_scale(cmd, client, resource_group, service, name,
              deployment=None,
              cpu=None,
              memory=None,
              instance_count=None,
              no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        return app_scale_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                    deployment, cpu, memory, instance_count, no_wait)
    else:
        return app_scale_standard(cmd, client, resource_group, service, name,
                                  deployment, cpu, memory, instance_count, no_wait)


def app_deploy(cmd, client, resource_group, service, name,
               version=None,
               deployment=None,
               disable_validation=None,
               artifact_path=None,
               builder=None,
               target_module=None,
               runtime_version=None,
               jvm_options=None,
               main_entry=None,
               env=None,
               config_file_patterns=None,
               no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, assign_ideneity, main_entry not support
        return app_deploy_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                     version, deployment, artifact_path, builder, target_module, 
                                     jvm_options, env, config_file_patterns, no_wait)
    else:
        # config_file_patterns not support
        return app_deploy_standard(cmd, client, resource_group, service, name,
                                   version, deployment, disable_validation, artifact_path, target_module, runtime_version, 
                                   jvm_options, main_entry, env, no_wait)


def app_identity_assign(cmd, client, resource_group, service, name, role=None, scope=None):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return identity_assign(cmd, client, models, resource_group, service, name, role, scope)


def app_identity_remove(cmd, client, resource_group, service, name):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return identity_remove(cmd, client, models, resource_group, service, name)


def app_identity_show(cmd, client, resource_group, service, name):
    client = get_client(cmd) if is_enterprise_tier(cmd, resource_group, service) else client
    return identity_show(cmd, client, resource_group, service, name)


def app_domain_bind(cmd, client, resource_group, service, app, domain_name,
                certificate=None,
                enable_end_to_end_tls=None):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return domain_bind(cmd, client, models, resource_group, service, app, domain_name, certificate, enable_end_to_end_tls)


def app_domain_show(cmd, client, resource_group, service, app, domain_name):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return domain_show(cmd, client, resource_group, service, app, domain_name)


def app_domain_list(cmd, client, resource_group, service, app):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return domain_list(cmd, client, resource_group, service, app)


def app_domain_update(cmd, client, resource_group, service, app, domain_name,
                certificate=None,
                enable_end_to_end_tls=None):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return domain_update(cmd, client, models, resource_group, service, app, domain_name, certificate, enable_end_to_end_tls)


def app_domain_unbind(cmd, client, resource_group, service, app, domain_name):
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
    return domain_unbind(cmd, client, resource_group, service, app, domain_name)


def app_append_loaded_public_certificate(cmd, client, resource_group, service, name, certificate_name, load_trust_store):
    models = models_20210901preview
    if is_enterprise_tier(cmd, resource_group, service):
        client = get_client(cmd)
        models = models_20220101preview
    return append_loaded_public_certificate(cmd, client, resource_group, service, name, certificate_name, load_trust_store, models)
