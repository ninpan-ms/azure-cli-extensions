# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, unused-argument, redefined-builtin

from .vendored_sdks.appplatform.v2022_01_01_preview import models as models_20220101preview

DEFAULT_BUILD_SERVICE_NAME = "default"
DEFAULT_BUILD_AGENT_POOL_NAME = "default"


def _update_default_build_agent_pool(cmd, client, resource_group, name, build_pool_size=None):
    if build_pool_size is not None:
        build_properties = models_20220101preview.BuildServiceAgentPoolProperties(
            pool_size=models_20220101preview.BuildServiceAgentPoolSizeProperties(
                name=build_pool_size))
        agent_pool_resource = models_20220101preview.BuildServiceAgentPoolResource(
            properties=build_properties)
        return client.build_service_agent_pool.begin_update_put(
            resource_group, name, DEFAULT_BUILD_SERVICE_NAME, DEFAULT_BUILD_AGENT_POOL_NAME, agent_pool_resource)
