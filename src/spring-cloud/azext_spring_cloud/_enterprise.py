from time import sleep
from knack.util import CLIError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id
from .vendored_sdks.appplatform.v2022_01_01_preview import models
from ._utils import  get_azure_files_info, _pack_source_code
from .custom import app_get
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import sdk_no_wait
from .azure_storage_file import FileService
from requests.auth import HTTPBasicAuth
import os
import requests
import re
import sys
import tempfile
import uuid

logger = get_logger(__name__)
APPLICATION_CONFIGURATION_SERVICE_NAME = "ApplicationConfigurationService"
APPLICATION_CONFIGURATION_SERVICE_PROPERTY_PATTERN = "ConfigFilePatterns"
DEFAULT_DEPLOYMENT_NAME = "default"

# pylint: disable=line-too-long
NO_PRODUCTION_DEPLOYMENT_ERROR = "No production deployment found, use --deployment to specify deployment or create deployment with: az spring-cloud app deployment create"
NO_PRODUCTION_DEPLOYMENT_SET_ERROR = "This app has no production deployment, use \"az spring-cloud app deployment create\" to create a deployment and \"az spring-cloud app set-deployment\" to set production deployment."
DELETE_PRODUCTION_DEPLOYMENT_WARNING = "You are going to delete production deployment, the app will be inaccessible after this operation."
LOG_RUNNING_PROMPT = "This command usually takes minutes to run. Add '--verbose' parameter if needed."

DEFAULT_BUILD_SERVICE_NAME = "default"


def app_create_enterprise(cmd, client, resource_group, service, name, 
                          assign_endpoint, cpu, memory, instance_count, jvm_options, env, assign_identity):
    '''app_create_enterprise
    Create app with an active deployment, deployment should be deployed with default banner
    1. Create app
    2. Create deployment with default banner
    3. [Optional] Update app properties which needs an active deployment exist
    '''
    _ensure_app_not_exist(client, resource_group, service, name)
    need_update_app_after_deployment = assign_endpoint
    total_steps = 3 if need_update_app_after_deployment else 2

    logger.warning("[1/{}] Creating app {}".format(total_steps, name))
    app_poller = _create_app(client, resource_group, service, name, assign_identity)
    _wait_till_end(cmd, app_poller)

    logger.warning('[2/{}] Create default deployment with name {} {}'.format(total_steps, DEFAULT_DEPLOYMENT_NAME, 
                   '(this operation can take a while to complete)' if not need_update_app_after_deployment else ''))
    source = models.BuildResultUserSourceInfo(build_result_id='<default>') 
    deployment_poller = _create_deployment(cmd, client, resource_group, service, name, DEFAULT_DEPLOYMENT_NAME, source,
                                           cpu, memory, instance_count, jvm_options, env, is_active=True)
    if need_update_app_after_deployment:
        logger.warning('[3/{}] Update app {} properties (this operation can take a while to complete)'.format(total_steps, name))
        app_resource = _update_app(assign_endpoint=assign_endpoint)
        app_poller = client.apps.begin_update(resource_group, service, name, app_resource)
    _wait_till_end(cmd, app_poller, deployment_poller)
    return app_get(cmd, client, resource_group, service, name)


def app_update_enterprise(cmd, client, resource_group, service, name,
                         assign_endpoint,
                         deployment,
                         jvm_options,
                         env,
                         config_file_patterns):
    '''app_update_enterprise
    1. update app properties (make sure some properties requires active deployment exist)
    2. update deployment properties
    '''
    # check app properties need active deployment exist
    is_app_update = any(x is not None for x in [assign_endpoint])
    is_deployment_update = any(x is not None for x in [jvm_options, env, config_file_patterns])
    app_properties_needs_deployment_update = any(x is not None for x in [assign_endpoint])
    app_poller = None
    deployment_poller = None
    if is_app_update:
        app_resource = _update_app(assign_endpoint=assign_endpoint)
        app_poller = client.apps.begin_update(resource_group, service, name, app_resource)
    if is_deployment_update:
        deployment_resource = models.DeploymentResource(
            properties=models.DeploymentResourceProperties(
                deployment_settings=_format_deployment_settings(jvm_options=jvm_options, env=env, config_file_patterns=config_file_patterns)
            )
        )
        deployment_poller = client.deployments.begin_update(resource_group, service, name, deployment.name, deployment_resource)
    _wait_till_end(cmd, app_poller, deployment_poller)
    return app_get(cmd, client, resource_group, service, name)


def app_deploy_enterprise(cmd, client, resource_group, service, name,
                          version, deployment, artifact_path, builder, target_module, jvm_options,
                          env, config_file_patterns, no_wait):
    '''app_deploy_enterprise
    Deploy artifact to deployment under the existing app.
    Update active deployment's pattern if --config-profile-patterns are provided.
    Throw exception if app or deployment not found.
    This method does:
    1. Call build service to get upload url
    2. Upload artifact to given Storage file url
    3. Send the url to build service
    4. Query build result from build service
    5. Send build result id to deployment
    '''
    logger.warning(LOG_RUNNING_PROMPT)
    
    deployment_settings = _format_deployment_settings(jvm_options=jvm_options, env=env, config_file_patterns=config_file_patterns)
    user_source_info = _build_and_get_result(cmd, client, resource_group, service, name, version, artifact_path, builder, target_module, additional_steps=1)
    logger.warning("[5/5] Deploying the built docker image to deployment {} under app {}".format(deployment.name, name))
    resource = models.DeploymentResource(
        properties=models.DeploymentResourceProperties(
            deployment_settings=deployment_settings,
            source=user_source_info
        )
    )
    return sdk_no_wait(no_wait, client.deployments.begin_update, resource_group, service, name, deployment.name, resource)
    

def deployment_create_enterprise(cmd, client, resource_group, service, app, name,
                                 skip_clone_settings=False,
                                 version=None,
                                 artifact_path=None,
                                 builder=None,
                                 target_module=None,
                                 jvm_options=None,
                                 cpu=None,
                                 memory=None,
                                 instance_count=None,
                                 env=None,
                                 config_file_patterns=None,
                                 no_wait=False):
    _ensure_deployment_not_exist(client, resource_group, service, app, name)
    origin_deployment = _get_active_deployment_or_default(client, resource_group, service, app, skip_clone_settings)
    sku = _format_sku(instance_count or origin_deployment.sku.capacity)
    origin_settings = origin_deployment.properties.deployment_settings
    settings = _format_deployment_settings(cpu=cpu or origin_settings.resource_requests.cpu,
                                           memory=memory or origin_settings.resource_requests.memory,
                                           jvm_options=jvm_options,
                                           env=env or origin_settings.environment_variables,
                                           config_file_patterns=config_file_patterns or _get_config_file_patterns(origin_settings.addon_configs))
    user_source_info = _build_and_get_result(cmd, client, resource_group, service, app, version, artifact_path, builder, target_module, additional_steps=1)
    resource = models.DeploymentResource(
        properties=models.DeploymentResourceProperties(
            source=user_source_info,
            deployment_settings=settings
        ),
        sku=sku
    )
    logger.warning("[5/5] Create deployment {} (this operation can take a while to complete)".format(name))
    return sdk_no_wait(no_wait, client.deployments.begin_create_or_update,
                       resource_group, service, app, name, resource)


def set_deployment(cmd, client, resource_group, service, name, deployment):
    resource = client.deployments.get(resource_group, service, name, deployment)
    if resource.properties.active:
        raise InvalidArgumentValueError('Deployment {} is already the production deployment'.format(deployment))
    active_deployment_collection = models.ActiveDeploymentCollection(
        active_deployment_names=[deployment]
    )
    return client.apps.set_active_deployments(resource_group, service, name, active_deployment_collection)


def unset_deployment(cmd, client, resource_group, service, name):
    active_deployment_collection = models.ActiveDeploymentCollection(
        active_deployment_names=[]
    )
    return client.apps.set_active_deployments(resource_group, service, name, active_deployment_collection)


def _build_and_get_result(cmd, client, resource_group, service, name, version, artifact_path, builder, target_module, additional_steps=0):
    total_steps = 4 + additional_steps
    logger.warning("[1/{}] Requesting for upload URL.".format(total_steps))
    upload_url, relative_path = _request_upload_url(client,  resource_group, service, name)
    logger.warning("[2/{}] Uploading package to blob.".format(total_steps))
    _compress_and_upload(cmd, client, upload_url, artifact_path)
    logger.warning("[3/{}] Creating or Updating build '{}'.".format(total_steps, name))
    build_result_id = _queue_build(cmd, client, resource_group, service, name, relative_path, builder, target_module)
    logger.warning("[4/{}] Waiting for building docker image to finish. This may take a few minutes.".format(total_steps))
    _wait_build_finished(cmd, client, service, build_result_id)
    return models.BuildResultUserSourceInfo(version=version, build_result_id=build_result_id)


def _wait_build_finished(cmd, client, service, build_result_id):
    resource_id = parse_resource_id(build_result_id)
    resource_group = resource_id['resource_group']
    service = resource_id['name']
    build_service = resource_id['child_name_1']
    build = resource_id['child_name_2']
    build_result_name = resource_id['resource_name']

    def _wait_build_pod_to_start_callback():
        result = client.build_service.get_build_result(resource_group, service, build_service, build, build_result_name)
        pod_not_started = not result.properties.build_pod_name or not result.properties.build_stages
        still_building = _is_build_result_still_building(result)
        return result, pod_not_started and still_building, result.properties.provisioning_state

    def _wait_build_job_to_finish_callback():
        result = client.build_service.get_build_result(resource_group, service, build_service, build, build_result_name)
        return result, _is_build_result_still_building(result), result.properties.provisioning_state

    def _try_to_stream_build_logs(progress_bar, pod, stages):
        if not stages:
            return False
        for stage in stages:
            if not _start_build_log_streaming_with_retry(progress_bar, client,
                                                         resource_group, service,
                                                         build_service, build, build_result_name,
                                                         pod, stage.name):
                return False
        return True

    progress_bar = cmd.cli_ctx.get_progress_controller()
    result = _do_long_running_build_operation(progress_bar, _wait_build_pod_to_start_callback)
    build_log_streaming_available = _try_to_stream_build_logs(progress_bar, result.properties.build_pod_name, result.properties.build_stages)
    if not build_log_streaming_available:
        logger.warning("Cannot show real time build logs at this moment")
    result = _do_long_running_build_operation(progress_bar, _wait_build_job_to_finish_callback)
    if not build_log_streaming_available:
        _do_long_running_build_operation(progress_bar, lambda: (None, True, "getting offline build logs"), "getting offline build logs", 1, 5)
        _try_print_build_logs_after_build(client, resource_group, service, build_service, build, build_result_name)

    if result.properties.provisioning_state != "Succeeded":
        raise CLIError("Failed to build docker image, please check the build logs and retry.")


def _do_long_running_build_operation(progress_bar, callback, initial_status = None, interval_seconds = 3, max_retries = -1):
    progress_bar.begin()
    progress_bar.add(message=initial_status)
    retry_count = 0
    obj, should_retry, status = callback()
    progress_bar.add(message=status)
    while should_retry and (retry_count < max_retries or max_retries < 0):
        sleep(interval_seconds)
        retry_count += 1
        obj, should_retry, status = callback()
        progress_bar.add(message=status)
    progress_bar.end()
    return obj


def _is_build_result_still_building(build_result):
    if not build_result or not build_result.properties:
        return None
    else:
        return build_result.properties.provisioning_state == "Building" or build_result.properties.provisioning_state == "Queuing"


def _queue_build(cmd, client, resource_group, service, name, relative_path, builder=None, target_module=None):
    subscription = get_subscription_id(cmd.cli_ctx)
    service_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}'.format(subscription, resource_group, service)
    properties = models.BuildProperties(
        builder='{}/buildservices/default/builders/{}'.format(service_resource_id, builder),
        agent_pool='{}/buildservices/default/agentPools/default'.format(service_resource_id),
        relative_path=relative_path,
        env={"BP_MAVEN_BUILT_MODULE": target_module} if target_module else None)
    build = models.Build(properties=properties)
    try:
        return client.build_service.create_or_update_build(resource_group,
                                                           service,
                                                           builder,
                                                           name,
                                                           build).properties.triggered_build_result.id
    except (AttributeError, CloudError) as e:
        raise CLIError("Failed to create or update a build. Error: {}".format(e.message))


def _compress_and_upload(cmd, client, upload_url, artifact_path):
    account_name, endpoint_suffix, share_name, relative_name, sas_token = get_azure_files_info(upload_url)
    progress_bar = cmd.cli_ctx.get_progress_controller()
    progress_bar.add(message='Uploading')
    progress_bar.begin()
    FileService(account_name,
                sas_token=sas_token,
                endpoint_suffix=endpoint_suffix).create_file_from_path(share_name,
                                                                       None,
                                                                       relative_name,
                                                                       artifact_path or _get_upload_local_file())
    progress_bar.stop()


def _request_upload_url(client,  resource_group, service, name):
    try:
        response = client.build_service.get_resource_upload_url(resource_group, service, 'default')
        if not response.upload_url:
            raise CLIError("Failed to get a SAS URL to upload context.")
        return response.upload_url, response.relative_path
    except CloudError as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e.message))
    except AttributeError as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e))


def _get_addon_configs(config_file_patterns):
    patterns = models.AddonProfile(
        properties = {
            APPLICATION_CONFIGURATION_SERVICE_PROPERTY_PATTERN: config_file_patterns
        }
    )
    addon_configs = {}
    addon_configs[APPLICATION_CONFIGURATION_SERVICE_NAME] = patterns
    return addon_configs


def _get_config_file_patterns(addon_configs):
    return addon_configs.get(APPLICATION_CONFIGURATION_SERVICE_NAME) if addon_configs is not None else None


def _get_active_deployment(client, resource_group, service, name):
    deployments = client.deployments.list(resource_group, service, name)
    return next(iter(x for x in deployments if x.properties.active), None)


def _ensure_active_deployment_exist_and_get(client, resource_group, service, name):
    deployment_resource = _get_active_deployment(client, resource_group, service, name)
    if not deployment_resource:
        raise CLIError(NO_PRODUCTION_DEPLOYMENT_ERROR)
    return deployment_resource

def _deployment_or_active_deployment_name(client, resource_group, service, app, deployment):
    if deployment:
        return client.deployments.get(resource_group, service, app, deployment).name
    else:
        return _ensure_active_deployment_exist_and_get(client, resource_group, service, app).name

def _format_deployment_settings(cpu=None, memory=None, jvm_options=None, env=None, config_file_patterns=None):
    if all(x is None for x in [cpu, memory, jvm_options, env, config_file_patterns]):
        return None
    resource_requests = models.ResourceRequests(cpu=cpu, memory=memory) if cpu or memory else None
    env = _merge_jvm_to_env(env, jvm_options)
    addon_configs = _get_addon_configs(config_file_patterns) if config_file_patterns is not None else None
    return models.DeploymentSettings(
        addon_configs=addon_configs,
        resource_requests=resource_requests,
        environment_variables=env
    )


def _merge_jvm_to_env(env, jvm_options):
    if not jvm_options:
        return env
    env = env or {}
    env['JAVA_OPTS'] = jvm_options
    return env


def _format_sku(instance_count):
    return models.Sku(name="E0", tier="ENTERPRISE", capacity=instance_count) if instance_count else None


def _get_upload_local_file():
    file_path = os.path.join(tempfile.gettempdir(), 'build_archive_{}.tar.gz'.format(uuid.uuid4().hex))
    _pack_source_code(os.getcwd(), file_path)
    return file_path


def _ensure_deployment_not_exist(client, resource_group, service, app, name):
    deployment = None
    try:
        deployment = client.deployments.get(resource_group, service, app, name)
    except Exception:
        # ingore
        return
    if deployment:
        raise CLIError('Deployment {} already exist.'.format(deployment.id))


def _ensure_app_not_exist(client, resource_group, service, name):
    app = None
    try:
        app = client.apps.get(resource_group, service, name)
    except Exception:
        # ignore
        return
    if app:
        raise CLIError('App {} already exist.'.format(app.id))


def _create_app(client, resource_group, service, name, assign_identity):
    resource = models.AppResource(
                    properties=models.AppResourceProperties(
                        temporary_disk=models.TemporaryDisk(size_in_gb=5, mount_path='/tmp')
                    )
                )
    if assign_identity is True:
        resource.identity = models.ManagedIdentityProperties(type="systemassigned")
    return client.apps.begin_create_or_update(resource_group, service, name, resource)


def _update_app(assign_endpoint=None):
    if assign_endpoint is None:
        return
    properties = models.AppResourceProperties(
       public=assign_endpoint 
    )
    return models.AppResource(
        properties=properties
    )


def _create_deployment(cmd, client, resource_group, service, app, name, source,
                       cpu, memory, instance_count, jvm_options, env, is_active=None):
    settings = _format_deployment_settings(cpu=cpu, memory=memory, jvm_options=jvm_options, env=env)
    sku = _format_sku(instance_count)
    resource = models.DeploymentResource(
        properties=models.DeploymentResourceProperties(
            deployment_settings=settings,
            source=source,
            active=is_active
        ),
        sku=sku
    )
    return client.deployments.begin_create_or_update(resource_group, service, app, name, resource)


def _get_active_deployment_or_default(client, resource_group, service, app, skip_clone_settings):
    deployment = models.DeploymentResource(
        properties=models.DeploymentResourceProperties(
            deployment_settings=_default_deployment_settings()
        ),
        sku = _default_deployment_sku()
    )
    if not skip_clone_settings:
        active_deployment = _get_active_deployment(client, resource_group, service, app)
        if not active_deployment:
            logger.warning("No production deployment found, use --skip-clone-settings to skip copying settings from "
                           "production deployment.")
        else:
            deployment = active_deployment
    return deployment



def _default_deployment_settings():
    return _format_deployment_settings(cpu='1', memory='1Gi')

def _default_deployment_sku():
    return _format_sku(instance_count=1)

def _wait_till_end(cmd, *pollers):
    if not pollers:
        return
    progress_bar = cmd.cli_ctx.get_progress_controller()
    progress_bar.add(message='Running')
    progress_bar.begin()
    while any(x and not x.done() for x in pollers):
        progress_bar.add(message='Running')
        sleep(5)


# Try to print out build logs after a build succeeded
def _try_print_build_logs_after_build(client, resource_group, service, build_service, build, build_result):
    try:
        logs = client.build_service.get_build_result_log(resource_group, service, build_service, build, build_result, "all")
        if logs and logs.properties and logs.properties.blob_url:
            sys.stdout.write(requests.get(logs.properties.blob_url).text)
        else:
            logger.warning("No offline build logs available.")
    except:
        logger.warning("Unfortunately we are not able to display offline build logs due to unknown errors.")


# Try to print build log streaming for a specific pod and build stage
# Return value: True - no errors please continue; False - unknown error happened
def _start_build_log_streaming_with_retry(progress_bar, client, resource_group, service, build_service, build, build_result_name, pod_name, stage_name):
    if not pod_name or not stage_name:
        return False

    streaming_url = primary_key = None
    def _ensure_streaming_url():
        nonlocal streaming_url, primary_key
        if not streaming_url:
            test_keys = client.services.list_test_keys(resource_group, service)
            primary_key = test_keys.primary_key
            if not primary_key:
                logger.warning("To use the log streaming feature, please enable the test endpoint by running 'az spring-cloud test-endpoint enable -n {0} -g {1}'".format(service, resource_group))
                raise CLIError("Please enable test endpoint")
            test_url = test_keys.primary_test_endpoint
            base_url = test_url.replace('.test.', '.')
            base_url = re.sub('https://.+?\@', '', base_url)
            streaming_url = "https://{}/api/logstream/buildpods/{}/stages/{}?follow=true".format(base_url, pod_name, stage_name)

    def _wait_build_container_logs_callback():
        build_result = client.build_service.get_build_result(resource_group, service, build_service, build, build_result_name)
        _ensure_streaming_url()
        need_retry, err = _try_stream_build_log(progress_bar, streaming_url, primary_key, build_result)
        return err, need_retry, "fetching build pod container logs"

    try:
        MAX_RETRY_COUNT = 20
        error = _do_long_running_build_operation(progress_bar, _wait_build_container_logs_callback, "connecting to build pod container", max_retries=MAX_RETRY_COUNT)
        if error:
            logger.warning(error)
            return False
        return True
    except:
        return False


# Call build log streaming API and return whether we need to retry
# Return value is a tuple of:
#   boolean: True - not ready yet and need to retry; False - No need to retry
#   string: error message, None means no errors
def _try_stream_build_log(progress_bar, streaming_url, primary_key, build_result):
    with requests.get(streaming_url, stream=True, auth=HTTPBasicAuth("primary", primary_key)) as response:
        if response.status_code == 200:
            progress_bar.end()
            std_encoding = sys.stdout.encoding
            for content in response.iter_content():
                if content:
                    sys.stdout.write(content.decode(encoding='utf-8', errors='replace')
                                        .encode(std_encoding, errors='replace')
                                        .decode(std_encoding, errors='replace'))
            return False, None
        elif response.status_code == 400:
            return (True, None) if _is_build_result_still_building(build_result) else (False, None)
        else:
            return True, "Failed to get build logs with status code '{}' and reason '{}'".format(
                    response.status_code, response.content)