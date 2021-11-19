# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._enterprise import DEFAULT_BUILD_SERVICE_NAME
from .vendored_sdks.appplatform.v2022_01_01_preview import models


def create_or_update_buildpacks_binding(cmd, client, resource_group, service,
                                        name, type, properties=None, secrets=None):
    binding_resource = _build_buildpacks_binding_resource(type, properties, secrets)
    return client.buildpacks_binding.create_or_update(resource_group,
                                                      service,
                                                      DEFAULT_BUILD_SERVICE_NAME,
                                                      name,
                                                      binding_resource)


def buildpacks_binding_show(cmd, client, resource_group, service, name):
    return client.buildpacks_binding.get(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, name)


def buildpacks_binding_delete(cmd, client, resource_group, service, name):
    return client.buildpacks_binding.delete(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, name)


def _build_buildpacks_binding_resource(binding_type, properties_dict, secrets_dict):
    launch_properties = models.BuildpacksBindingLaunchProperties(properties=properties_dict,
                                                                 secrets=secrets_dict)
    binding_properties = models.BuildpacksBindingProperties(binding_type=binding_type,
                                                            launch_properties=launch_properties)
    return models.BuildpacksBindingResource(properties=binding_properties)
