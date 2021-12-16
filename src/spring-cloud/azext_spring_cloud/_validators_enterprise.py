# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, unused-argument, redefined-builtin

from re import match
from azure.cli.core.util import CLIError
from azure.cli.core.commands.validators import validate_tag
from azure.core.exceptions import ResourceNotFoundError
from knack.log import get_logger
from ._enterprise import DEFAULT_BUILD_SERVICE_NAME
from ._resource_quantity import (
    validate_cpu as validate_and_normalize_cpu, 
    validate_memory as validate_and_normalize_memory)
from ._util_enterprise import (
    is_enterprise_tier, get_client
)
from .vendored_sdks.appplatform.v2022_01_01_preview.models import _app_platform_management_client_enums as AppPlatformEnums
from ._validators import _parse_sku_name


logger = get_logger(__name__)

def only_support_enterprise(cmd, namespace):
    if namespace.resource_group and namespace.service and not is_enterprise_tier(cmd, namespace.resource_group, namespace.service):
        raise CLIError("'{}' only supports for Enterprise tier Spring instance.".format(namespace.command))


def not_support_enterprise(cmd, namespace):
    if namespace.resource_group and namespace.service and is_enterprise_tier(cmd, namespace.resource_group, namespace.service):
        raise CLIError("'{}' doesn't support for Enterprise tier Spring instance.".format(namespace.command))


def validate_cpu(namespace):
    namespace.cpu = validate_and_normalize_cpu(namespace.cpu)


def validate_memory(namespace):
    namespace.memory = validate_and_normalize_memory(namespace.memory)


def validate_git_uri(namespace):
    uri = namespace.uri
    if uri and (not uri.startswith("https://")) and (not uri.startswith("git@")):
        raise CLIError("Git URI should start with \"https://\" or \"git@\"")


def validate_config_file_patterns(namespace):
    if namespace.config_file_patterns:
        _validate_patterns(namespace.config_file_patterns)


def validate_acs_patterns(namespace):
    if namespace.patterns:
        _validate_patterns(namespace.patterns)


def _validate_patterns(patterns):
    pattern_list = patterns.split(',')
    invalid_list = [p for p in pattern_list if not _is_valid_pattern(p)]
    if len(invalid_list) > 0:
        logger.warning("Patterns '%s' are invalid.", ','.join(invalid_list))
        raise CLIError("Patterns should be the collection of patterns separated by comma, each pattern in the format of 'application' or 'application/profile'")


def _is_valid_pattern(pattern):
    return _is_valid_app_name(pattern) or _is_valid_app_and_profile_name(pattern)


def _is_valid_app_name(pattern):
    return match(r"^[a-zA-Z][-_a-zA-Z0-9]*$", pattern) is not None


def _is_valid_profile_name(profile):
    return profile == "*" or _is_valid_app_name(profile)


def _is_valid_app_and_profile_name(pattern):
    parts = pattern.split('/')
    return len(parts) == 2 and _is_valid_app_name(parts[0]) and _is_valid_profile_name(parts[1])


def validate_buildpacks_binding_properties(namespace):
    """ Extracts multiple space-separated properties in key[=value] format """
    if isinstance(namespace.properties, list):
        properties_dict = {}
        for item in namespace.properties:
            properties_dict.update(validate_tag(item))
        namespace.properties = properties_dict


def validate_buildpacks_binding_secrets(namespace):
    """ Extracts multiple space-separated secrets in key[=value] format """
    if isinstance(namespace.secrets, list):
        secrets_dict = {}
        for item in namespace.secrets:
            secrets_dict.update(validate_tag(item))
        namespace.secrets = secrets_dict


def validate_buildpacks_binding_not_exist(cmd, namespace):
    client = get_client(cmd)
    try:
        binding_resource = client.buildpacks_binding.get(namespace.resource_group,
                                                         namespace.service,
                                                         DEFAULT_BUILD_SERVICE_NAME,
                                                         namespace.name)
        if binding_resource is not None:
            raise CLIError('Buildpacks Binding {} already exists '
                           'in resource group {}, service {}. You can edit it by set command.'
                           .format(namespace.name, namespace.resource_group, namespace.service))
    except ResourceNotFoundError:
        # Excepted case
        pass


def validate_buildpacks_binding_exist(cmd, namespace):
    client = get_client(cmd)
    # If not exists exception will be raised
    client.buildpacks_binding.get(namespace.resource_group,
                                  namespace.service,
                                  DEFAULT_BUILD_SERVICE_NAME,
                                  namespace.name)


def validate_builder(cmd, namespace):
    client = get_client(cmd)
    builder = client.build_service_builder.get(namespace.resource_group,
                                               namespace.service,
                                               DEFAULT_BUILD_SERVICE_NAME,
                                               namespace.builder)
    if builder.properties.provisioning_state != AppPlatformEnums.BuilderProvisioningState.SUCCEEDED:
        raise CLIError('The provision state of builder {} is not succeeded, please choose a succeeded builder.'
                       .format(namespace.builder))

def validate_build_pool_size(namespace):
    if _parse_sku_name(namespace.sku) != 'enterprise':
        namespace.build_pool_size = None
