
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, logging-format-interpolation, protected-access, wrong-import-order, too-many-lines

from ._enterprise import app_get_enterprise
from ._util_enterprise import (is_enterprise_tier, get_client)
from .vendored_sdks.appplatform.v2022_05_01_preview import models as models
from azure.cli.core.commands import cached_put
from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger
from knack.util import CLIError

APPLICATION_CONFIGURATION_SERVICE_NAME = "ApplicationConfigurationService"

logger = get_logger(__name__)

def application_configuration_service_show(cmd, client, service, resource_group):
    _validate_tier(cmd, resource_group, service)

    return client.configuration_services.get(resource_group, service)


def application_configuration_service_clear(cmd, client, service, resource_group):
    _validate_tier(cmd, resource_group, service)

    properties = models.ConfigurationServiceGitProperty()
    acs_resource = models.ConfigurationServiceResource(properties=properties)
    return client.configuration_services.begin_create_or_update(resource_group, service, acs_resource)


def application_configuration_service_git_add(cmd, client, service, resource_group,
                                              name, patterns, uri, label,
                                              search_paths=None,
                                              username=None,
                                              password=None,
                                              host_key=None,
                                              host_key_algorithm=None,
                                              private_key=None,
                                              strict_host_key_checking=None,
                                              no_wait=False):
    _validate_tier(cmd, resource_group, service)

    if patterns:
        patterns = patterns.split(",")
    repo = models.ConfigurationServiceGitRepository(name=name, patterns=patterns, uri=uri, label=label)

    if search_paths:
        search_paths = search_paths.split(",")
    repo.search_paths = search_paths
    repo.username = username
    repo.password = password
    repo.host_key = host_key
    repo.host_key_algorithm = host_key_algorithm
    repo.private_key = private_key
    repo.strict_host_key_checking = strict_host_key_checking

    acs_resource = client.configuration_services.get(resource_group, service)
    if acs_resource is None or acs_resource.properties is None:
        raise CLIError("Application Configuration Service is not enabled.")
    
    acs_settings = acs_resource.properties.settings

    if acs_settings is None or acs_settings.git_property is None or acs_settings.git_property.repositories is None:
        repos = []
        git_property = models.ConfigurationServiceGitProperty(repositories=repos)
        acs_settings = models.ConfigurationServiceSettings(git_property=git_property)
    else:
        repos = acs_settings.git_property.repositories
    
    repos.append(repo)
    acs_settings.git_property.repositories = repos
    acs_resource.properties.settings = acs_settings

    logger.warning("[1/2] Validating Application Configuration Service settings")
    _validate_acs_settings(client, resource_group, service, acs_settings)

    logger.warning("[2/2] Updating Application Configuration Service settings, (this operation can take a while to complete)")
    return sdk_no_wait(no_wait, client.configuration_services.begin_create_or_update, resource_group, service, acs_resource)


def application_configuration_service_git_update(cmd, client, service, resource_group, name,
                                              patterns=None,
                                              uri=None,
                                              label=None,
                                              search_paths=None,
                                              username=None,
                                              password=None,
                                              host_key=None,
                                              host_key_algorithm=None,
                                              private_key=None,
                                              strict_host_key_checking=None,
                                              no_wait=False):
    _validate_tier(cmd, resource_group, service)

    acs_resource = client.configuration_services.get(resource_group, service)
    acs_settings = acs_resource.properties.settings
    if not acs_settings or not acs_settings.git_property or not acs_settings.git_property.repositories:
        raise CLIError("Repo '{}' not found.".format(name))
    repos = acs_settings.git_property.repositories

    if search_paths:
        search_paths = search_paths.split(",")

    if patterns:
        patterns = patterns.split(",")

    found = False
    for repo in repos:
        if repo.name == name:
            found = True
            repo.patterns = patterns or repo.patterns
            repo.uri = uri or repo.uri
            repo.label = label or repo.label
            repo.search_paths = search_paths or repo.search_paths
            repo.username = username or repo.username
            repo.password = password or repo.password
            repo.host_key = host_key or repo.host_key
            repo.host_key_algorithm = host_key_algorithm or repo.host_key_algorithm
            repo.private_key = private_key or repo.private_key
            repo.strict_host_key_checking = strict_host_key_checking or repo.strict_host_key_checking

    if not found:
        raise CLIError("Repo '{}' not found.".format(name))

    logger.warning("[1/2] Validating Application Configuration Service settings")
    _validate_acs_settings(client, resource_group, service, acs_settings)

    logger.warning("[2/2] Updating Application Configuration Service settings repo, (this operation can take a while to complete)")
    return sdk_no_wait(no_wait, client.configuration_services.begin_create_or_update, resource_group, service, acs_resource)


def application_configuration_service_git_remove(cmd, client, service, resource_group, name, no_wait=False):
    _validate_tier(cmd, resource_group, service)

    acs_resource = client.configuration_services.get(resource_group, service)
    acs_settings = acs_resource.properties.settings
    if not acs_settings or not acs_settings.git_property or not acs_settings.git_property.repositories:
        raise CLIError("Repo '{}' not found.".format(name))

    git_property = acs_settings.git_property
    repository = [repo for repo in git_property.repositories if repo.name == name]
    if not repository:
        raise CLIError("Repo '{}' not found.".format(name))

    git_property.repositories.remove(repository[0])

    acs_settings = models.ConfigurationServiceSettings(git_property=git_property)
    properties = models.ConfigurationServiceProperties(settings=acs_settings)

    logger.warning("[1/2] Validating Application Configuration Service settings")
    _validate_acs_settings(client, resource_group, service, acs_settings)

    logger.warning("[2/2] Deleting Application Configuration Service settings repo, (this operation can take a while to complete)")
    acs_resource = models.ConfigurationServiceResource(properties=properties)
    return sdk_no_wait(no_wait, client.configuration_services.begin_create_or_update, resource_group, service, acs_resource)


def application_configuration_service_git_list(cmd, client, service, resource_group):
    _validate_tier(cmd, resource_group, service)

    acs_resource = client.configuration_services.get(resource_group, service)
    acs_settings = acs_resource.properties.settings

    if not acs_settings or not acs_settings.git_property or not acs_settings.git_property.repositories:
        raise CLIError("Repos not found.")

    return acs_settings.git_property.repositories


def application_configuration_service_bind(cmd, client, service, resource_group, app):
    _validate_tier(cmd, resource_group, service)

    _acs_bind_or_unbind_app(cmd, client, service, resource_group, app, True)


def application_configuration_service_unbind(cmd, client, service, resource_group, app):
    _validate_tier(cmd, resource_group, service)

    _acs_bind_or_unbind_app(cmd, client, service, resource_group, app, False)


def _acs_bind_or_unbind_app(cmd, client, service, resource_group, app_name, enabled):
    app = app_get_enterprise(cmd, client, resource_group, service, app_name)
    app.properties.addon_configs = {
        APPLICATION_CONFIGURATION_SERVICE_NAME: models.AddonProfile()
    } if app.properties.addon_configs is None else app.properties.addon_configs

    if app.properties.addon_configs.get(APPLICATION_CONFIGURATION_SERVICE_NAME).enabled == enabled:
        logger.warning('App "{}" has been {}binded'.format(app_name, '' if enabled else 'un'))
        return

    app.properties.addon_configs[APPLICATION_CONFIGURATION_SERVICE_NAME].enabled = enabled
    return client.apps.begin_update(resource_group, service, app_name, app)


def _is_valid_git_uri(uri):
    return uri.startswith("https://") or uri.startswith("git@")


def _validate_acs_settings(client, resource_group, service, acs_settings):
    uri_error_msg = "Git URI should start with \"https://\" or \"git@\""

    if acs_settings is None or acs_settings.git_property is None:
        return

    for repo in acs_settings.git_property.repositories:
        if not _is_valid_git_uri(repo.uri):
            raise CLIError(uri_error_msg)

    try:
        result = sdk_no_wait(False, client.configuration_services.begin_validate, resource_group, service, acs_settings).result()
    except Exception as err:  # pylint: disable=broad-except
        raise CLIError("{0}. You may raise a support ticket if needed by the following link: https://docs.microsoft.com/azure/spring-cloud/spring-cloud-faq?pivots=programming-language-java#how-can-i-provide-feedback-and-report-issues".format(err))

    if result is not None and result.git_property_validation_result is not None:
        git_result = result.git_property_validation_result
        if not git_result.is_valid:
            result = git_result.git_repos_validation_result
            for item in result or []:
                if len(item.messages) > 0:
                    if item.name:
                        logger.error("Item of the name \"%s\" meets error:", item.name)
                    logger.error("\n".join(item.messages))
            raise CLIError("Application Configuration Service settings contain errors.")


def _validate_tier(cmd, resource_group, service):
    if not is_enterprise_tier(cmd, resource_group, service):
        raise CLIError("Service Registry is only supported in Enterprise tier.")
