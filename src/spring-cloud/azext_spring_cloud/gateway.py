# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from .vendored_sdks.appplatform.v2022_01_01_preview import models
from ._resource_quantity import validate_cpu, validate_memory
from knack.util import CLIError

DEFAULT_NAME = "default"

def gateway_update(cmd, client, resource_group, service,
                   cpu=None,
                   memory=None,
                   instance_count=None,
                   assign_endpoint=None,
                   https_only=None,
                   scope=None,
                   client_id=None,
                   client_secret=None,
                   issuer_uri=None,
                   api_title=None,
                   api_description=None,
                   api_documentation_location=None,
                   api_version=None,
                   server_url=None,
                   allowed_origins=None,
                   allowed_methods=None,
                   allowed_headers=None,
                   max_age=None,
                   allow_credentials=None,
                   exposed_headers=None
                   ):
    cpu = validate_cpu(cpu)
    memory = validate_memory(memory)
    all_provided = scope and client_id and client_secret and issuer_uri
    none_provided = scope is None and client_id is None and client_secret is None and issuer_uri is None
    if not all_provided and not none_provided :
        raise CLIError("Single Sign On configurations '--scope --client-id --client-secret --issuer-uri' should be all provided or none provided.")

    gateway = client.gateways.get(resource_group, service, DEFAULT_NAME)

    sso_properties = gateway.properties.sso_properties
    if all_provided:
        scope = scope.split(",")
        sso_properties = models.SsoProperties(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            issuer_uri=issuer_uri,
        )

    api_metadata_properties = models.GatewayApiMetadataProperties(
        title=api_title or gateway.properties.api_metadata_properties.title,
        description=api_description or gateway.properties.api_metadata_properties.description,
        documentation=api_documentation_location or gateway.properties.api_metadata_properties.documentation,
        version=api_version or gateway.properties.api_metadata_properties.version,
        server_url=server_url or gateway.properties.api_metadata_properties.server_url
    )

    if allowed_origins:
        allowed_origins = allowed_origins.split(",")
    if allowed_methods:
        allowed_methods = allowed_methods.split(",")
    if allowed_headers:
        allowed_headers = allowed_headers.split(",")
    if exposed_headers:
        exposed_headers = exposed_headers.split(",")

    cors_properties = models.GatewayCorsProperties(
        allowed_origins=allowed_origins or gateway.properties.cors_properties.allowed_origins,
        allowed_methods=allowed_methods or gateway.properties.cors_properties.allowed_methods,
        allowed_headers=allowed_headers or gateway.properties.cors_properties.allowed_headers,
        max_age=max_age or gateway.properties.cors_properties.max_age,
        allow_credentials=allow_credentials or gateway.properties.cors_properties.allow_credentials,
        exposed_headers=exposed_headers or gateway.properties.cors_properties.exposed_headers
    )

    resource_requests = models.GatewayResourceRequests(
        cpu=cpu or gateway.properties.resource_requests.cpu,
        memory=memory or gateway.properties.resource_requests.memory
    )

    properties = models.GatewayProperties(
        public=assign_endpoint if assign_endpoint is not None else gateway.properties.public,
        https_only=https_only if https_only is not None else gateway.properties.https_only,
        sso_properties=sso_properties,
        api_metadata_properties=api_metadata_properties,
        cors_properties=cors_properties,
        resource_requests=resource_requests)

    sku = models.Sku(name=gateway.sku.name, tier=gateway.sku.tier,
                     capacity=instance_count or gateway.sku.capacity)

    gateway_resource = models.GatewayResource(properties=properties, sku=sku)
    return client.gateways.begin_create_or_update(resource_group, service, DEFAULT_NAME, gateway_resource)


def gateway_show(cmd, client, resource_group, service):
    return client.gateways.get(resource_group, service, DEFAULT_NAME)


def gateway_clear(cmd, client, resource_group, service):
    gateway = client.gateways.get(resource_group, service, DEFAULT_NAME)
    properties = models.GatewayProperties()
    sku = models.Sku(name=gateway.sku.name, tier=gateway.sku.tier)
    gateway_resource = models.GatewayResource(properties=properties, sku=sku)
    return client.gateways.begin_create_or_update(resource_group, service, DEFAULT_NAME, gateway_resource)


def gateway_custom_domain_show(cmd, client, resource_group, service, domain_name):
    return client.gateway_custom_domains.get(resource_group, service, DEFAULT_NAME, domain_name)


def gateway_custom_domain_list(cmd, client, resource_group, service):
    return client.gateway_custom_domains.list(resource_group, service, DEFAULT_NAME)


def gateway_custom_domain_update(cmd, client, resource_group, service,
                                 domain_name,
                                 certificate=None):
    properties = models.GatewayCustomDomainProperties()
    if certificate is not None:
        certificate_response = client.gateways.certificates.get(
            resource_group, service, certificate)
        properties = models.GatewayCustomDomainProperties(
            thumbprint=certificate_response.properties.thumbprint
        )

    custom_domain_resource = models.GatewayCustomDomainResource(
        properties=properties)
    return client.gateway_custom_domains.begin_create_or_update(resource_group, service, DEFAULT_NAME,
                                                                domain_name, custom_domain_resource)


def gateway_custom_domain_unbind(cmd, client, resource_group, service, domain_name):
    client.gateway_custom_domains.get(resource_group, service,
                                      DEFAULT_NAME, domain_name)
    return client.gateway_custom_domains.begin_delete(resource_group, service, DEFAULT_NAME, domain_name)


def gateway_route_config_show(cmd, client, resource_group, service, name):
    return client.gateway_route_configs.get(resource_group, service, DEFAULT_NAME, name)


def gateway_route_config_list(cmd, client, resource_group, service):
    return client.gateway_route_configs.list(resource_group, service, DEFAULT_NAME)


def gateway_route_config_create(cmd, client, resource_group, service, name,
                                app_name=None,
                                routes_json=None,
                                routes_file=None):
    if routes_json is not None and routes_file is not None:
        raise CLIError(
            "You can only specify either --routes-json or --routes-file.")

    route_configs = client.gateway_route_configs.list(
        resource_group, service, DEFAULT_NAME)
    if name in (route_config.name for route_config in list(route_configs)):
        raise CLIError("Route config " + name + " already exists")

    app_resource = client.apps.get(resource_group, service, app_name)

    routes = []
    if routes_file is not None:
        with open(routes_file, 'r') as json_file:
            routes = json.load(json_file)

    if routes_json is not None:
        routes = json.loads(routes_json)

    properties = models.GatewayRouteConfigProperties(
        app_resource_id=app_resource.id, routes=routes)

    route_config_resource = models.GatewayRouteConfigResource(
        properties=properties)
    return client.gateway_route_configs.begin_create_or_update(resource_group, service, DEFAULT_NAME, name, route_config_resource)


def gateway_route_config_update(cmd, client, resource_group, service, name,
                                app_name=None,
                                routes_json=None,
                                routes_file=None):
    if routes_json is not None and routes_file is not None:
        raise CLIError(
            "You can only specify either --routes-json or --routes-file.")

    gateway_route_config = client.gateway_route_configs.get(
        resource_group, service, DEFAULT_NAME, name)

    app_resource_id = gateway_route_config.properties.app_resource_id
    if app_name is not None:
        app_resource = client.apps.get(resource_group, service, app_name)
        app_resource_id = app_resource.id

    routes = gateway_route_config.properties.routes
    if routes_file is not None:
        with open(routes_file, 'r') as json_file:
            routes = json.load(json_file)

    if routes_json is not None:
        routes = json.loads(routes_json)

    properties = models.GatewayRouteConfigProperties(
        app_resource_id=app_resource_id, routes=routes)

    route_config_resource = models.GatewayRouteConfigResource(
        properties=properties)
    return client.gateway_route_configs.begin_create_or_update(resource_group, service, DEFAULT_NAME, name, route_config_resource)


def gateway_route_config_remove(cmd, client, resource_group, service, name):
    return client.gateway_route_configs.begin_delete(resource_group, service, DEFAULT_NAME, name)
