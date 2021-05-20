# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, logging-format-interpolation, protected-access, wrong-import-order, too-many-lines
from time import sleep
from knack.util import CLIError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from .vendored_sdks.appplatform.v2021_03_01_preview import models

logger = get_logger(__name__)
DEFAULT_DEPLOYMENT_NAME = "default"
DEPLOYMENT_CREATE_OR_UPDATE_SLEEP_INTERVAL = 5
APP_CREATE_OR_UPDATE_SLEEP_INTERVAL = 2
TANZU_CONFIGURATION_SERVICE_NAME = "ApplicationConfigurationService"
TANZU_CONFIGURATION_SERVICE_PROPERTY_PATTERN = "pattern"


def tanzu_get(cmd, client, resource_group, name):
    '''tanzu_get
    Get Tanzu Cluster
    '''
    return client.tanzu_services.get(resource_group, name)


def tanzu_app_list(cmd, client, resource_group, service):
    '''tanzu_app_list
    List app under a Tanzu service, together with the deployment
    '''
    apps = client.apps.list(resource_group, service).get(0) or []
    deployments = client.deployments.list_for_cluster(resource_group, service).get(0) or []
    for app in apps:
        app.properties.deployment = next((x for x in deployments if x.id.startswith(app.id)), None)
    return apps


def tanzu_app_get(cmd, client, resource_group, service, name):
    '''tanzu_app_get
    Get an app together with deployment under app
    '''
    return _app_get(cmd, client, resource_group, service, name)


def tanzu_app_delete(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_delete
    Delete an app
    '''
    return client.apps.delete(resource_group, service, name)


def tanzu_app_create(cmd, client, resource_group, service, name,
                     assign_endpoint=None,
                     cpu=None,
                     memory=None,
                     instance_count=None,
                     env=None,
                     no_wait=False):
    '''tanzu_app_create
    Create app together with deployment
    '''
    try:
        _app_get(cmd, client, resource_group, service, name)
        raise CLIError('App {} already exists'.format(name))
    except CloudError:
        logger.info("Creating an un-existing app {}".format(name))
    app_properties = models.AppResourceProperties(
        public=assign_endpoint
    )
    settings = models.DeploymentSettings(
        cpu=cpu,
        memory=memory,
        environment_variables=env,
        serve_traffic=True
    )
    deployment_properties = models.DeploymentResourceProperties(deployment_settings=settings)
    sku = models.Sku(capacity=instance_count)
    return _app_create_or_update(cmd, client, resource_group, service, name, DEFAULT_DEPLOYMENT_NAME,
                                 app_properties, deployment_properties, sku, no_wait, 'Creating')


def tanzu_app_update(cmd, client, resource_group, service, name,
                     assign_endpoint=None,
                     cpu=None,
                     memory=None,
                     instance_count=None,
                     env=None,
                     patterns=None,
                     no_wait=False):
    '''tanzu_app_update
    Update an existing app, if the app doesn't exist, this command exit with error.
    The given app may not contain a deployment at this point.
    Consider there is no way for user to create a deployment under an existing app,
    this method creates the deployment if not exist.
    '''
    def _get_default_settings():
        return models.DeploymentResourceProperties(
            deployment_settings=models.DeploymentSettings(
                cpu='1',
                memory='1Gi',
                serve_traffic=True
            )
        )
    app = _app_get(cmd, client, resource_group, service, name)
    app_properties = app.properties
    if assign_endpoint is not None:
        app_properties.public = assign_endpoint

    # Create new deployment if not exist
    create_deployment = True
    deployment_name = DEFAULT_DEPLOYMENT_NAME
    deployment_properties = _get_default_settings()
    deployment_sku = models.Sku(capacity=1)
    if app.properties.deployment:
        # Found existing deployment
        create_deployment = False
        deployment_name = app.properties.deployment.name
        deployment_properties = app.properties.deployment.properties
        deployment_sku = app.properties.deployment.sku
    # Merge properties from argument
    if cpu:
        deployment_properties.deployment_settings.cpu = cpu
    if memory:
        deployment_properties.deployment_settings.memory = memory
    if env:
        deployment_properties.deployment_settings.environment_variables = env
    if patterns:
        deployment_properties.deployment_settings.addon_config = _set_pattern_for_deployment(patterns)
    deployment_name = app.properties.deployment.name if app.properties.deployment else DEFAULT_DEPLOYMENT_NAME
    sku = app_properties.deployment.sku if app_properties.deployment else models.Sku(capacity=1)
    if instance_count:
        deployment_sku.capacity = instance_count
    return _app_create_or_update(cmd, client, resource_group, service, name, deployment_name,
                                 app_properties, deployment_properties, deployment_sku, no_wait,
                                 create_deployment=create_deployment)


def tanzu_app_start(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_start
    Start deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve_name(cmd, client, resource_group, service, name)
    return client.deployments.start(resource_group, service, name, deployment_name)


def tanzu_app_restart(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_restart
    Restart deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve_name(cmd, client, resource_group, service, name)
    return client.deployments.restart(resource_group, service, name, deployment_name)


def tanzu_app_stop(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_stop
    Stop deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve_name(cmd, client, resource_group, service, name)
    return client.deployments.stop(resource_group, service, name, deployment_name)


def tanzu_app_deploy(cmd, client, resource_group, service, name, artifact_path, no_wait=None):
    '''tanzu_app_deploy
    Deploy artifact to deployment under the existing app.
    Throw exception if app or deployment not found.
    This method does:
    1. Call build service to get upload url
    2. Upload artifact to given Storage file url
    3. Send the url to build service
    4. Query build result from build service
    5. Send build result id to deployment
    '''
    deployment_name = _assert_deployment_exist_and_retrieve_name(cmd, client, resource_group, service, name)
    # todo (qingyi)
    build_result_id = ''
    return client.deployments.deploy(resource_group, service, name, deployment_name, build_result_id=build_result_id)


def tanzu_configuration_service_bind_app(cmd, client, resource_group, service, app_name):
    '''tanzu_configuration_service_bind_app
    Bind Application Configuration Service to an existing app to enable functionality.
    If the app doesn't exist, this command exit with error.
    '''
    _tcs_bind_or_unbind_app(cmd, client, resource_group, service, app_name, True)


def tanzu_configuration_service_unbind_app(cmd, client, resource_group, service, app_name):
    '''tanzu_configuration_service_unbind_app
    Unbind Application Configuration Service to an existing app to disable functionality.
    If the app doesn't exist, this command exit with error.
    '''
    _tcs_bind_or_unbind_app(cmd, client, resource_group, service, app_name, False)


def _app_create_or_update(cmd, client, resource_group, service, app_name, deployment_name,
                          app_properties, deployment_properties, deployment_sku,
                          no_wait, operation='Updating', create_deployment=True):
    '''_app_create_or_update
    Create or Update an app and deployment under that app
    '''
    total_step = 2
    # app.properties.public can be set to True only if there is a deployment exist
    is_public = app_properties.public
    if is_public and create_deployment:
        logger.debug("There is no deployment under app {}, temp set app.public to False".format(app_name))
        total_step = 3
        app_properties.public = False
    logger.warning('[1/{}] {} app {}'.format(total_step, operation, app_name))
    poller = client.apps.create_or_update(
        resource_group, service, app_name, app_properties)
    while not poller.done():
        sleep(APP_CREATE_OR_UPDATE_SLEEP_INTERVAL)
    logger.warning('[2/{}] {} deployment {} under app {}. This may take a few minutes.'
                   .format(total_step, operation, deployment_name, app_name))
    deployment_poller = client.deployments.create_or_update(resource_group, service, app_name, deployment_name,
                                                 properties=deployment_properties, sku=deployment_sku)
    # Finally set the app.properties.public as requested
    if is_public and create_deployment:
        logger.warning('[3/{}] Assign endpoint for app {}.'.format(total_step, app_name))
        app_properties.public = True
        poller = client.apps.create_or_update(resource_group, service, app_name, app_properties)
    if no_wait:
        return deployment_poller
    while not poller.done() or not deployment_poller.done():
        sleep(APP_CREATE_OR_UPDATE_SLEEP_INTERVAL)
    return _app_get(cmd, client, resource_group, service, app_name)


def _app_get(cmd, client, resource_group, service, name):
    '''_app_get
    Get app together with deployment
    '''
    app = client.apps.get(resource_group, service, name)
    if not app:
        return app
    app.properties.deployment = _get_default_deployment(cmd, client, resource_group, service, name)
    return app


def _get_default_deployment(cmd, client, resource_group, service, app_name):
    '''_get_default_deployment
    Currently, an app has no more than one deployment, this method retrieves the deployment under a given app.
    '''
    deployments = client.deployments.list(resource_group, service, app_name).get(0) or []
    return deployments[0] if deployments else None


def _assert_deployment_exist_and_retrieve_name(cmd, client, resource_group, service, name):
    app = _app_get(cmd, client, resource_group, service, name)
    deployment = app.properties.deployment
    if not deployment:
        raise CLIError('Deployment not found, create one by running "az spring-cloud tanzu app '
                       'update -g {} -s {} -n {}"'.format(resource_group, service, name))
    return deployment.name


def _set_pattern_for_deployment(patterns):
    return {
        TANZU_CONFIGURATION_SERVICE_NAME: models.AddonProfile(
            properties = {
                TANZU_CONFIGURATION_SERVICE_PROPERTY_PATTERN: patterns
            }
        )
    }


def _tcs_bind_or_unbind_app(cmd, client, resource_group, service, app_name, enabled):
    try:
        app = _app_get(cmd, client, resource_group, service, app_name)
        previous = app.properties.addon_config[TANZU_CONFIGURATION_SERVICE_NAME].enabled
        app.properties.addon_config[TANZU_CONFIGURATION_SERVICE_NAME] = models.AddonProfile(
            enabled=enabled
        )
        if (enabled != previous):
            return client.apps.create_or_update(resource_group, service, app_name, app.properties)
        elif (enabled):
            logger.warning('app {} has been binded'.format(app_name))
        else:
            logger.warning('app {} has been unbinded'.format(app_name))
    except CloudError:
        raise CLIError('App {} not exists'.format(app_name))
