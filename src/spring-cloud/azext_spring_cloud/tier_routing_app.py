# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._util_enterprise import (is_enterprise_tier, get_client)
from ._enterprise import (app_create_enterprise,
                          app_update_enterprise,
                          app_deploy_enterprise,
                          set_deployment,
                          unset_deployment)
from .custom import (app_create as app_create_standard, app_update as app_update_standard, 
                     app_deploy as app_deploy_standard,
                     app_set_deployment as set_deployment_standard,
                     app_unset_deployment as unset_deployment_standard)
from knack.log import get_logger
from .vendored_sdks.appplatform.v2022_01_01_preview import models as models_20220101preview
from .vendored_sdks.appplatform.v2021_09_01_preview import models as models_20210901preview

logger = get_logger(__name__)


def app_create(cmd, client, resource_group, service, name,
               assign_endpoint=None,
               cpu=None,
               memory=None,
               instance_count=None,
               disable_probe=None,
               runtime_version=None,
               jvm_options=None,
               env=None,
               enable_persistent_storage=None,
               assign_identity=None,
               persistent_storage=None,
               loaded_public_certificate_file=None):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, enable_persistent_storage not support
        return app_create_enterprise(cmd, get_client(cmd), resource_group, service, name, 
                                     assign_endpoint=assign_endpoint, 
                                     cpu=cpu, 
                                     memory=memory, 
                                     instance_count=instance_count, 
                                     jvm_options=jvm_options, 
                                     env=env, 
                                     assign_identity=assign_identity)
    else:
        return app_create_standard(cmd, client, resource_group, service, name,
                                   assign_endpoint=assign_endpoint,
                                   cpu=cpu,
                                   memory=memory,
                                   instance_count=instance_count,
                                   disable_probe=disable_probe,
                                   runtime_version=runtime_version,
                                   jvm_options=jvm_options,
                                   env=env,
                                   enable_persistent_storage=enable_persistent_storage,
                                   assign_identity=assign_identity,
                                   persistent_storage=persistent_storage,
                                   loaded_public_certificate_file=loaded_public_certificate_file)


def app_update(cmd, client, resource_group, service, name,
               assign_endpoint=None,
               deployment=None,
               runtime_version=None,
               jvm_options=None,
               main_entry=None,
               env=None,
               config_file_patterns=None,
               disable_probe=None,
               enable_persistent_storage=None,
               https_only=None,
               enable_end_to_end_tls=None,
               persistent_storage=None,
               loaded_public_certificate_file=None):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, enable_persistent_storage, main_entry, https_only, enable_end_to_end_tls not support
        return app_update_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                     assign_endpoint=assign_endpoint,
                                     deployment=deployment,
                                     jvm_options=jvm_options,
                                     env=env,
                                     config_file_patterns=config_file_patterns)
    else:
        return app_update_standard(cmd, client, resource_group, service, name,
                                   assign_endpoint=assign_endpoint,
                                   deployment=deployment,
                                   runtime_version=runtime_version,
                                   jvm_options=jvm_options,
                                   main_entry=main_entry,
                                   env=env,
                                   disable_probe=disable_probe,
                                   enable_persistent_storage=enable_persistent_storage,
                                   https_only=https_only,
                                   enable_end_to_end_tls=enable_end_to_end_tls,
                                   persistent_storage=persistent_storage,
                                   loaded_public_certificate_file=loaded_public_certificate_file)



def app_deploy(cmd, client, resource_group, service, name,
               version=None,
               deployment=None,
               disable_validation=None,
               artifact_path=None,
               builder=None,
               source_path=None,
               target_module=None,
               runtime_version=None,
               jvm_options=None,
               main_entry=None,
               env=None,
               config_file_patterns=None,
               disable_probe=None,
               no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        # runtime_version, assign_ideneity, main_entry not support
        return app_deploy_enterprise(cmd, get_client(cmd), resource_group, service, name,
                                     version=version, 
                                     deployment=deployment, 
                                     artifact_path=artifact_path, 
                                     builder=builder,
                                     target_module=target_module,
                                     jvm_options=jvm_options,
                                     env=env,
                                     config_file_patterns=config_file_patterns,
                                     no_wait=no_wait)
    else:
        # config_file_patterns not support
        return app_deploy_standard(cmd, client, resource_group, service, name,
                                   version=version,
                                   deployment=deployment,
                                   disable_validation=disable_validation,
                                   artifact_path=artifact_path,
                                   source_path=source_path,
                                   target_module=target_module,
                                   runtime_version=runtime_version,
                                   jvm_options=jvm_options,
                                   main_entry=main_entry,
                                   env=env,
                                   disable_probe=disable_probe,
                                   no_wait=no_wait)


def app_set_deployment(cmd, client, resource_group, service, name, deployment):
    if is_enterprise_tier(cmd, resource_group, service):
        return set_deployment(cmd, get_client(cmd), resource_group, service, name, deployment)
    else:
        return set_deployment_standard(cmd, client, resource_group, service, name, deployment)



def app_unset_deployment(cmd, client, resource_group, service, name):
    if is_enterprise_tier(cmd, resource_group, service):
        return unset_deployment(cmd, get_client(cmd), resource_group, service, name)
    else:
        return unset_deployment_standard(cmd, client, resource_group, service, name)