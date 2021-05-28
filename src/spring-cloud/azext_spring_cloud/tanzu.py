# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, logging-format-interpolation, protected-access, wrong-import-order, too-many-lines
from time import sleep
from knack.util import CLIError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id
from azure.cli.core.commands import LongRunningOperation
from .vendored_sdks.appplatform.v2021_03_01_preview import models
from ._utils import _get_tanzu_upload_local_file, get_azure_files_info
from .azure_storage_file import FileService
import requests
import sys
from six.moves.urllib import parse
from threading import Thread


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
        app.properties.deployment = next((x for x in deployments if x.id.startswith(app.id + '/')), None)
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
                     config_file_patterns=None,
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
    update_app = False
    if assign_endpoint is not None and app_properties.public != assign_endpoint:
        app_properties.public = assign_endpoint
        update_app = True

    # Create new deployment if not exist
    create_deployment = True
    deployment_name = DEFAULT_DEPLOYMENT_NAME
    deployment_properties = _get_default_settings()
    deployment_sku = models.Sku(capacity=1)
    # logger.warning()
    if app.properties.deployment:
        # Found existing deployment
        create_deployment = False
        deployment_name = app.properties.deployment.name
        deployment_properties = app.properties.deployment.properties
        deployment_sku = app.properties.deployment.sku
    # Merge properties from argument
    update_deployment = create_deployment
    if cpu and deployment_properties.deployment_settings.cpu != cpu:
        deployment_properties.deployment_settings.cpu = cpu
        update_deployment = True
    if memory and deployment_properties.deployment_settings.memory != memory:
        deployment_properties.deployment_settings.memory = memory
        update_deployment = True
    if env:  # Skip comparation here
        update_deployment = True
        deployment_properties.deployment_settings.environment_variables = env
    if config_file_patterns:
        update_deployment = True
        deployment_properties.deployment_settings.addon_config = _set_pattern_for_deployment(config_file_patterns)
    deployment_name = app.properties.deployment.name if app.properties.deployment else DEFAULT_DEPLOYMENT_NAME
    deployment_sku = app_properties.deployment.sku if app_properties.deployment else models.Sku(capacity=1)
    if instance_count and deployment_sku.capacity != instance_count:
        deployment_sku.capacity = instance_count
        update_deployment = True
    return _app_create_or_update(cmd, client, resource_group, service, name, deployment_name,
                                 app_properties, deployment_properties, deployment_sku, no_wait,
                                 create_deployment=create_deployment,
                                 skip_app_operation=(not update_app), skip_deployment_operation=(not update_deployment))


def tanzu_app_start(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_start
    Start deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name).name
    return client.deployments.start(resource_group, service, name, deployment_name)


def tanzu_app_restart(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_restart
    Restart deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name).name
    return client.deployments.restart(resource_group, service, name, deployment_name)


def tanzu_app_stop(cmd, client, resource_group, service, name, no_wait=None):
    '''tanzu_app_stop
    Stop deployment under the existing app.
    Throw exception if app or deployment not found
    '''
    deployment_name = _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name).name
    return client.deployments.stop(resource_group, service, name, deployment_name)


def tanzu_app_deploy(cmd, client, resource_group, service, name,
                    artifact_path=None, target_module=None, config_file_patterns=None, no_wait=None):
    '''tanzu_app_deploy
    Deploy artifact to deployment under the existing app.
    Update active deployment's pattern if --config-file-patterns are provided.
    Throw exception if app or deployment not found.
    This method does:
    1. Call build service to get upload url
    2. Upload artifact to given Storage file url
    3. Send the url to build service
    4. Query build result from build service
    5. Send build result id to deployment
    '''
    deployment = _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name)
    deployment_name = deployment.name
    # get upload url
    upload_url = None
    relative_path = None
    logger.warning("[1/5] Requesting for upload URL.")
    try:
        response = client.build_service.get_upload_url(resource_group, service)
        upload_url = response.upload_url
        relative_path = response.relative_path
    except (AttributeError, CloudError) as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e.message))
    # upload file
    if not upload_url:
        raise CLIError("Failed to get a SAS URL to upload context.")
    account_name, endpoint_suffix, share_name, relative_name, sas_token = get_azure_files_info(upload_url)
    logger.warning("[2/5] Uploading package to blob.")
    progress_bar = cmd.cli_ctx.get_progress_controller()
    progress_bar.add(message='Uploading')
    progress_bar.begin()
    FileService(account_name,
                sas_token=sas_token,
                endpoint_suffix=endpoint_suffix).create_file_from_path(share_name,
                                                                       None,
                                                                       relative_name,
                                                                       artifact_path or _get_tanzu_upload_local_file())
    progress_bar.stop()
    properties = models.BuildProperties(
        builder="default-tanzu-builder",
        name=name,
        relative_path=relative_path,
        env={"BP_MAVEN_BUILT_MODULE": target_module} if target_module else None)
    # create or update build
    logger.warning("[3/5] Creating or Updating build '{}'.".format(name))
    build_result_id = None
    try:
        build_result_id = client.build_service.create_or_update_build(resource_group,
                                                                      service,
                                                                      name,
                                                                      properties).properties.triggered_build_result.id
        build_result_name = parse_resource_id(build_result_id)["resource_name"]
    except (AttributeError, CloudError) as e:
        raise CLIError("Failed to create or update a build. Error: {}".format(e.message))
    # get build result
    logger.warning("[4/5] Waiting build finish. This may take a few minutes.")
    result = client.build_service.get_build_result(resource_group, service, name, build_result_name)
    progress_bar.add(message=result.properties.status)
    progress_bar.begin()
    while result.properties.status == "Building" or result.properties.status == "Queuing":
        progress_bar.add(message=result.properties.status)
        sleep(5)
        result = client.build_service.get_build_result(resource_group, service, name, build_result_name)
    progress_bar.stop()
    build_logs = client.build_service.get_build_result_log(resource_group, service, name, build_result_name, "all")
    if build_logs and build_logs.properties and build_logs.properties.blob_url:
        sys.stdout.write(requests.get(build_logs.properties.blob_url).text)
    if result.properties.status != "Succeeded":
        raise CLIError("Failed to get a successful build result.")

    # update config-file-patterns for deployment
    if config_file_patterns:
        _update_deployment_pattern(client, resource_group, service, name, deployment, config_file_patterns)

    logger.warning("[5/5] Deploying build result to deployment {} under app {}".format(deployment_name, name))
    poller = client.deployments.deploy(resource_group,
                                       service, name,
                                       deployment_name,
                                       build_result_id=build_result_id)
    if no_wait:
        return poller
    progress_bar.add(message='Deploying')
    LongRunningOperation(cmd.cli_ctx)(poller)
    return _app_get(cmd, client, resource_group, service, name)


def tanzu_app_tail_log(cmd, client, resource_group, service, name, instance=None,
                       follow=False, lines=50, since=None, limit=2048):
    '''tanzu_app_tail_log
    Get real time logs from the app.
    Throw exception if app or deployment not found.
    '''
    if not instance:
        deployment = _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name)
        if not deployment.properties.instances:
            raise CLIError("No deployment instances found for app '{0}'".format(name))
        instances = deployment.properties.instances
        if len(instances) > 1:
            logger.warning("Multiple app instances found:")
            for temp_instance in instances:
                logger.warning("{}".format(temp_instance.name))
            raise CLIError("Please use '-i/--instance' parameter to specify the instance name")
        instance = instances[0].name

    streaming_url = "https://{0}.asc-test.net/api/logstream/apps/{1}/instances/{2}".format(
        service, name, instance)
    params = {}
    params["tailLines"] = lines
    params["limitBytes"] = limit
    if since:
        params["sinceSeconds"] = since
    if follow:
        params["follow"] = True

    exceptions = []
    streaming_url += "?{}".format(parse.urlencode(params)) if params else ""
    t = Thread(target=_get_app_log, args=(
        streaming_url, exceptions))
    t.daemon = True
    t.start()

    while t.is_alive():
        sleep(5)  # so that ctrl+c can stop the command

    if exceptions:
        raise exceptions[0]


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
                          no_wait, operation='Updating', create_deployment=True,
                          skip_app_operation=False, skip_deployment_operation=False):
    '''_app_create_or_update
    Create or Update an app and deployment under that app.
    :param str operation: What is the caller command, this operation will be used in log.
    :param bool create_deployment: Whether the deployment need to be created in this method.
        app.properties.public cannot be true if there is no deployment exist.
    :param bool skip_app_operation: There is no need to real create or update app.
    :param bool skip_deployment_operation: There is no need to real create or update deployment.
    '''
    # if a deployment need to be created, it cannot be skipped
    skip_deployment_operation = (not create_deployment) and skip_deployment_operation
    total_step = 2
    step_count = 0
    need_additional_step = not skip_app_operation and app_properties.public and create_deployment
    if skip_deployment_operation:
        logger.debug("No need to create or update deployment {}".format(deployment_name))
        total_step -= 1
    if skip_app_operation:
        logger.debug("No need to create or update app {}".format(app_name))
        total_step -= 1
    if need_additional_step:
        # app.properties.public can be set to True only if there is a deployment exist
        logger.debug("There is no deployment under app {}, temp set app.public to False".format(app_name))
        total_step += 1
        app_properties.public = False

    # Real operation
    poller = None
    deployment_poller = None
    if not skip_app_operation:
        step_count += 1
        logger.warning('[{}/{}] {} app {}'.format(step_count, total_step, operation, app_name))
        LongRunningOperation(cmd.cli_ctx)(client.apps.create_or_update(resource_group,
                                                                       service,
                                                                       app_name,
                                                                       app_properties))

    if not skip_deployment_operation:
        step_count += 1
        logger.warning('[{}/{}] {} deployment {} under app {}. This may take a few minutes.'
                       .format(step_count, total_step, operation, deployment_name, app_name))
        deployment_poller = client.deployments.create_or_update(resource_group, service, app_name, deployment_name,
                                                                properties=deployment_properties, sku=deployment_sku)
    # Finally set the app.properties.public as requested
    if need_additional_step:
        step_count += 1
        logger.warning('[{}/{}] Assign endpoint for app {}.'.format(step_count, total_step, app_name))
        app_properties.public = True
        poller = client.apps.create_or_update(resource_group, service, app_name, app_properties)
    if no_wait:
        return None
    if deployment_poller:
        LongRunningOperation(cmd.cli_ctx)(deployment_poller)
    if poller:
        LongRunningOperation(cmd.cli_ctx)(poller)
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


def _assert_deployment_exist_and_retrieve(cmd, client, resource_group, service, name):
    app = _app_get(cmd, client, resource_group, service, name)
    deployment = app.properties.deployment
    if not deployment:
        raise CLIError('Deployment not found, create one by running "az spring-cloud tanzu app '
                       'update -g {} -s {} -n {}"'.format(resource_group, service, name))
    return deployment


def _set_pattern_for_deployment(patterns):
    return {
        TANZU_CONFIGURATION_SERVICE_NAME: models.AddonProfile(
            properties={
                TANZU_CONFIGURATION_SERVICE_PROPERTY_PATTERN: patterns
            }
        )
    }


def _update_deployment_pattern(cmd, client, resource_group, service, name, deployment, config_file_patterns):
    deployment_properties = deployment.properties
    deployment_properties.deployment_settings.addon_config = _set_pattern_for_deployment(config_file_patterns)
    deployment_poller = client.deployments.create_or_update(resource_group, service, name, deployment.name,
                                                            properties=deployment_properties, sku=deployment.sku)
    LongRunningOperation(cmd.cli_ctx)(deployment_poller)


def _tcs_bind_or_unbind_app(cmd, client, resource_group, service, app_name, enabled):
    # todo: replace put with patch for app update
    app = _app_get(cmd, client, resource_group, service, app_name)
    app.properties.addon_config = {
        TANZU_CONFIGURATION_SERVICE_NAME: models.AddonProfile()
    } if app.properties.addon_config is None else app.properties.addon_config

    if app.properties.addon_config.get(TANZU_CONFIGURATION_SERVICE_NAME).enabled == enabled:
        logger.warning('App {} has been {}binded'.format(app_name, '' if enabled else 'un'))
        return None

    app.properties.addon_config[TANZU_CONFIGURATION_SERVICE_NAME].enabled = enabled
    client.apps.create_or_update(resource_group, service, app_name, app.properties)
    logger.warning('Succeed to {}bind app.{}'.format('' if enabled else 'un',
                                                     '' if enabled else ' Please restart the app to take effect.'))

def _get_app_log(url, exceptions):
    with requests.get(url, stream=True) as response:
        try:
            if response.status_code != 200:
                raise CLIError("Failed to connect to the server with status code '{}' and reason '{}'".format(
                    response.status_code, response.reason))
            std_encoding = sys.stdout.encoding
            for content in response.iter_content():
                if content:
                    sys.stdout.write(content.decode(encoding='utf-8', errors='replace')
                                     .encode(std_encoding, errors='replace')
                                     .decode(std_encoding, errors='replace'))
        except CLIError as e:
            exceptions.append(e)
