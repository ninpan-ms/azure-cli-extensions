# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._validators import (_parse_sku_name)
from ._util_enterprise import (is_enterprise_tier, get_client)
from ._enterprise import (spring_cloud_create as create_enterprise)
from .custom import (spring_cloud_create as create_standard)
from knack.log import get_logger

logger = get_logger(__name__)


def spring_cloud_create(cmd, client, resource_group, name, 
                        location=None,
                        vnet=None, 
                        service_runtime_subnet=None, 
                        app_subnet=None, 
                        reserved_cidr_range=None,
                        service_runtime_network_resource_group=None, 
                        app_network_resource_group=None,
                        app_insights_key=None, 
                        app_insights=None,
                        sampling_rate=None,
                        disable_app_insights=None,
                        enable_java_agent=None,
                        enable_application_configuration_service=None,
                        enable_service_registry=None,
                        enable_gateway=None,
                        gateway_instance_count=None,
                        enable_api_portal=None,
                        api_portal_instance_count=None,
                        sku=None,
                        tags=None,
                        build_pool_size=None,
                        no_wait=False):
    if _parse_sku_name(sku) == 'enterprise':
        return create_enterprise(cmd, get_client(cmd), resource_group, name, 
                                 location=location,
                                 vnet=vnet, 
                                 service_runtime_subnet=service_runtime_subnet, 
                                 app_subnet=app_subnet, 
                                 reserved_cidr_range=reserved_cidr_range,
                                 service_runtime_network_resource_group=service_runtime_network_resource_group, 
                                 app_network_resource_group=app_network_resource_group,
                                 app_insights_key=app_insights_key, 
                                 app_insights=app_insights,
                                 sampling_rate=sampling_rate,
                                 disable_app_insights=disable_app_insights,
                                 enable_java_agent=enable_java_agent,
                                 enable_application_configuration_service=enable_application_configuration_service,
                                 enable_service_registry=enable_service_registry,
                                 enable_gateway=enable_gateway,
                                 gateway_instance_count=gateway_instance_count,
                                 enable_api_portal=enable_api_portal,
                                 api_portal_instance_count=api_portal_instance_count,
                                 sku=sku,
                                 tags=tags,
                                 build_pool_size=build_pool_size,
                                 no_wait=no_wait)
    else:
        return create_standard(cmd, client, resource_group, name, 
                               location=location,
                               vnet=vnet, 
                               service_runtime_subnet=service_runtime_subnet, 
                               app_subnet=app_subnet, 
                               reserved_cidr_range=reserved_cidr_range,
                               service_runtime_network_resource_group=service_runtime_network_resource_group, 
                               app_network_resource_group=app_network_resource_group,
                               app_insights_key=app_insights_key, 
                               app_insights=app_insights,
                               sampling_rate=sampling_rate,
                               disable_app_insights=disable_app_insights,
                               enable_java_agent=enable_java_agent,
                               sku=sku,
                               tags=tags,
                               no_wait=no_wait)