# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._util_enterprise import is_enterprise_tier, get_client
from ._enterprise import (deployment_create_enterprise)
from .custom import (deployment_create as deployment_create_standard)
from knack.log import get_logger

logger = get_logger(__name__)


def deployment_create(cmd, client, resource_group, service, app, name,
                      skip_clone_settings=False,
                      version=None,
                      artifact_path=None,
                      source_path=None,
                      disable_validation=None,
                      builder=None,
                      target_module=None,
                      runtime_version=None,
                      jvm_options=None,
                      main_entry=None,
                      cpu=None,
                      memory=None,
                      instance_count=None,
                      env=None,
                      config_file_patterns=None,
                      disable_probe=None,
                      no_wait=False):
    if is_enterprise_tier(cmd, resource_group, service):
        return deployment_create_enterprise(cmd, get_client(cmd), resource_group, service, app, name,
                                            skip_clone_settings=skip_clone_settings,
                                            version=version,
                                            artifact_path=artifact_path,
                                            builder=builder,
                                            target_module=target_module,
                                            jvm_options=jvm_options,
                                            cpu=cpu,
                                            memory=memory,
                                            instance_count=instance_count,
                                            env=env,
                                            config_file_patterns=config_file_patterns,
                                            no_wait=no_wait)
    else:
        return deployment_create_standard(cmd, client, resource_group, service, app, name,
                                          skip_clone_settings=skip_clone_settings,
                                          version=version,
                                          artifact_path=artifact_path,
                                          source_path=source_path,
                                          disable_validation=disable_validation,
                                          target_module=target_module,
                                          runtime_version=runtime_version,
                                          jvm_options=jvm_options,
                                          main_entry=main_entry,
                                          cpu=cpu,
                                          memory=memory,
                                          instance_count=instance_count,
                                          env=env,
                                          disable_probe=disable_probe,
                                          no_wait=no_wait)