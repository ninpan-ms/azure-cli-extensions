from time import sleep
from knack.util import CLIError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id
from azure.cli.core.commands import LongRunningOperation
from .vendored_sdks.appplatform.v2022_05_01_preview import models
from .vendored_sdks.appplatform.v2022_05_01_preview import AppPlatformManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from ._utils import  get_azure_files_info, _pack_source_code
from azure.cli.core.util import sdk_no_wait
from .azure_storage_file import FileService
import requests
import sys
from six.moves.urllib import parse
from threading import Thread

logger = get_logger(__name__)
APPLICATION_CONFIGURATION_SERVICE_NAME = "ApplicationConfigurationService"
APPLICATION_CONFIGURATION_SERVICE_PROPERTY_PATTERN = "ConfigFilePatterns"

def _get_client(cmd):
    return get_mgmt_service_client(cmd.cli_ctx, AppPlatformManagementClient)


def _is_enterprise_tier(cmd, resource_group, name):
    resource = _get_client(cmd).services.get(resource_group, name)
    return resource.sku.name == 'E0'


def _get_upload_local_file():
    file_path = os.path.join(tempfile.gettempdir(), 'build_archive_{}.tar.gz'.format(uuid.uuid4().hex))
    _pack_source_code(os.getcwd(), file_path)
    return file_path


def _app_deploy_enterprise(cmd, resource_group, service, app, name, version, path, runtime_version, jvm_options, cpu, memory,
                           instance_count,
                           env,
                           config_file_patterns=None,
                           target_module=None,
                           no_wait=False,
                           update=False):
    '''tanzu_app_deploy
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
    client = _get_client(cmd)
    #get upload url
    upload_url = None
    relative_path = None
    logger.warning("[1/5] Requesting for upload URL.")
    try:
        response = client.build_service.get_resource_upload_url(resource_group, service)
        upload_url = response.upload_url
        relative_path = response.relative_path
    except CloudError as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e.message))
    except AttributeError as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e))
    # upload file
    if not upload_url:
        raise CLIError("Failed to get a SAS URL to upload context.")
    account_name, endpoint_suffix, share_name, relative_name, sas_token = get_azure_files_info(upload_url)
    logger.warning("[2/5] Uploading package to blob.")
    progress_bar = cmd.cli_ctx.get_progress_controller()
    progress_bar.add(message='Uploading')
    progress_bar.begin()
    FileService(account_name,
                sas_token=sas_token,
                endpoint_suffix=endpoint_suffix).create_file_from_path(share_name,
                                                                       None,
                                                                       relative_name,
                                                                       path or _get_upload_local_file())
    progress_bar.stop()
    properties = models.BuildProperties(
        builder="default-enterprise-builder",
        relative_path=relative_path,
        env={"BP_MAVEN_BUILT_MODULE": target_module} if target_module else None)
    build = models.Build(properties=properties)
    # create or update build
    logger.warning("[3/5] Creating or Updating build '{}'.".format(app))
    build_result_id = None
    try:
        build_result_id = client.build_service.create_or_update_build(resource_group,
                                                                      service,
                                                                      app,
                                                                      build).properties.triggered_build_result.id
        build_result_name = parse_resource_id(build_result_id)["resource_name"]
    except (AttributeError, CloudError) as e:
        raise CLIError("Failed to create or update a build. Error: {}".format(e.message))
    # get build result
    logger.warning("[4/5] Waiting for building docker image to finish. This may take a few minutes.")
    result = client.build_service.get_build_result(resource_group, service, app, build_result_name)
    progress_bar.add(message=result.properties.status)
    progress_bar.begin()
    while result.properties.status == "Building" or result.properties.status == "Queuing":
        progress_bar.add(message=result.properties.status)
        sleep(5)
        result = client.build_service.get_build_result(resource_group, service, app, build_result_name)
    progress_bar.stop()
    build_logs = client.build_service.get_build_result_log(resource_group, service, app, build_result_name, "all")
    if build_logs and build_logs.properties and build_logs.properties.blob_url:
        sys.stdout.write(requests.get(build_logs.properties.blob_url).text)
    if result.properties.status != "Succeeded":
        raise CLIError("Failed to build docker image, please check the build logs and retry.")

    logger.warning("[5/5] Deploying the built docker image to deployment {} under app {}".format(name, app))
    if not update:
        cpu = cpu or '1'
        memory = memory or '1Gi'
        instance_count = instance_count or 1
    resource_requests=models.ResourceRequests(cpu=cpu, memory=memory) if cpu or memory else None
    # todo if jvm option, put to env
    settings = models.DeploymentSettings(
        resource_requests=resource_requests,
        addon_configs=_get_addon_configs(config_file_patterns),
        environment_variables=env
    ) if resource_requests or env or (config_file_patterns != None) else None
    sku = models.Sku(name='E0', tier='Enterprise', capacity=instance_count) if instance_count else None
    user_source_info = models.BuildResultUserSourceInfo(version=version, build_result_id=build_result_id)
    properties = models.DeploymentResourceProperties(
        deployment_settings=settings,
        source=user_source_info
    )
    deployment_resource = models.DeploymentResource(properties=properties, sku=sku)
    if update:
        return sdk_no_wait(no_wait, client.deployments.begin_update,
                           resource_group, service, app, name, deployment_resource)

    return sdk_no_wait(no_wait, client.deployments.begin_create_or_update,
                       resource_group, service, app, name, deployment_resource)


def _get_addon_configs(config_file_patterns):
    patterns = models.AddonProfile(
        properties = {
            APPLICATION_CONFIGURATION_SERVICE_PROPERTY_PATTERN: config_file_patterns
        }
    )
    addon_configs = {}
    addon_configs[APPLICATION_CONFIGURATION_SERVICE_NAME] = patterns
    return addon_configs
