
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, logging-format-interpolation, protected-access, wrong-import-order, too-many-lines
import json

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
    return client.configuration_services.get(resource_group, service)


def application_configuration_service_clear(cmd, client, service, resource_group):
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
    repo = models.ConfigurationServiceGitRepository(name=name, patterns=patterns, uri=uri, label=label)
    repo = _get_input_repo(repo, patterns, uri, label, search_paths, username, password, host_key, host_key_algorithm, private_key, strict_host_key_checking)

    acs_resource = client.configuration_services.get(resource_group, service)
    acs_resource = _get_acs_resource(acs_resource)
    repos = acs_resource.properties.settings.git_property.repositories
    repos.append(repo)
    acs_resource.properties.settings.git_property.repositories = repos

    _validate_acs_settings(client, resource_group, service, acs_resource.properties.settings)

    logger.warning("[2/2] Adding item to Application Configuration Service settings, (this operation can take a while to complete)")
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
    acs_resource = client.configuration_services.get(resource_group, service)
    acs_resource = _get_acs_resource(acs_resource)

    repo = _get_existing_repo(acs_resource.properties.settings.git_property.repositories, name)

    repo = _get_input_repo(repo, patterns, uri, label, search_paths, username, password, host_key, host_key_algorithm, private_key, strict_host_key_checking)    
    _replace_in_repos(repo, acs_resource.properties.settings.git_property.repositories)

    _validate_acs_settings(client, resource_group, service, acs_resource.properties.settings)

    logger.warning("[2/2] Updating item of Application Configuration Service settings, (this operation can take a while to complete)")
    return sdk_no_wait(no_wait, client.configuration_services.begin_create_or_update, resource_group, service, acs_resource)


def application_configuration_service_git_remove(cmd, client, service, resource_group, name, no_wait=False):
    acs_resource = client.configuration_services.get(resource_group, service)
    acs_resource = _get_acs_resource(acs_resource)

    repo = _get_existing_repo(acs_resource.properties.settings.git_property.repositories, name)

    acs_resource.properties.settings.git_property.repositories.remove(repo)

    _validate_acs_settings(client, resource_group, service, acs_resource.properties.settings)

    logger.warning("[2/2] Removing item of Application Configuration Service settings, (this operation can take a while to complete)")
    return sdk_no_wait(no_wait, client.configuration_services.begin_create_or_update, resource_group, service, acs_resource)


def application_configuration_service_git_list(cmd, client, service, resource_group):
    acs_resource = client.configuration_services.get(resource_group, service)
    acs_settings = acs_resource.properties.settings

    if not acs_settings or not acs_settings.git_property or not acs_settings.git_property.repositories:
        raise CLIError("Repos not found.")

    return acs_settings.git_property.repositories


def application_configuration_service_bind(cmd, client, service, resource_group, app):
    _acs_bind_or_unbind_app(cmd, client, service, resource_group, app, True)


def application_configuration_service_unbind(cmd, client, service, resource_group, app):
    _acs_bind_or_unbind_app(cmd, client, service, resource_group, app, False)


def _acs_bind_or_unbind_app(cmd, client, service, resource_group, app_name, enabled):
    app = client.apps.get(resource_group, service, app_name)
    app.properties.addon_configs = {
        APPLICATION_CONFIGURATION_SERVICE_NAME: models.AddonProfile()
    } if app.properties.addon_configs is None else app.properties.addon_configs

    if app.properties.addon_configs.get(APPLICATION_CONFIGURATION_SERVICE_NAME).enabled == enabled:
        logger.warning('App "{}" has been {}binded'.format(app_name, '' if enabled else 'un'))
        return

    app.properties.addon_configs[APPLICATION_CONFIGURATION_SERVICE_NAME].enabled = enabled
    return client.apps.begin_update(resource_group, service, app_name, app)


def _get_input_repo(repo, patterns, uri, label, search_paths, username, password, host_key, host_key_algorithm, private_key, strict_host_key_checking):
    if patterns:
        patterns = patterns.split(",")
    if search_paths:
        search_paths = search_paths.split(",")

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
    return repo


def _get_existing_repo(repos, name):
    repos = [r for r in repos if r.name == name]
    if not repos or len(repos) != 1:
        raise CLIError("Repo '{}' not found.".format(name))
    return repos[0]


def _replace_in_repos(repo, repos):
    [repo if repo.name == r.name else r for r in repos]


def _get_acs_resource(acs_resource):
    if acs_resource is None:
        acs_resource = models.ConfigurationServiceResource()
    acs_resource.properties = _get_acs_properties(acs_resource.properties)
    return acs_resource


def _get_acs_properties(properties):
    if properties is None:
        properties = models.ConfigurationServiceProperties()
    properties.settings = _get_acs_settings(properties.settings)
    return properties


def _get_acs_settings(acs_settings):
    if acs_settings is None:
        acs_settings = models.ConfigurationServiceSettings()
    acs_settings.git_property = _get_acs_git_property(acs_settings.git_property)
    return acs_settings


def _get_acs_git_property(git_property):
    if git_property is None:
        git_property = models.ConfigurationServiceGitProperty()
    git_property.repositories = _get_acs_repos(git_property.repositories)
    return git_property


def _get_acs_repos(repos):
    if repos is None:
        repos = []
    return repos


def _validate_acs_settings(client, resource_group, service, acs_settings):
    logger.warning("[1/2] Validating Application Configuration Service settings")

    if acs_settings is None or acs_settings.git_property is None:
        return

    try:
        result = sdk_no_wait(False, client.configuration_services.begin_validate, resource_group, service, acs_settings).result()
    except Exception as err:  # pylint: disable=broad-except
        raise CLIError("{0}. You may raise a support ticket if needed by the following link: https://docs.microsoft.com/azure/spring-cloud/spring-cloud-faq?pivots=programming-language-java#how-can-i-provide-feedback-and-report-issues".format(err))

    if result is not None and result.git_property_validation_result is not None:
        git_result = result.git_property_validation_result
        if not git_result.is_valid:
            validation_result = git_result.git_repos_validation_result
            filter_result = [{'name':x.name, 'messages':x.messages} for x in validation_result if len(x.messages) > 0]
            raise CLIError("Application Configuration Service settings contain errors.\n{}".format(json.dumps(filter_result, indent=2)))
