# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger

logger = get_logger(__name__)


# pylint: disable=line-too-long
def tanzu_app_table_output(result):
    is_list = isinstance(result, list)

    if not is_list:
        result = [result]

    for item in result:
        item['Public Url'] = item['properties']['url']
        deployment = item['properties']['deployment']

        if deployment:
            isStarted = deployment['properties']['status'].upper() == "RUNNING"
            instance_count = deployment['sku']['capacity']
            instances = deployment['properties']['instances']
            if instances is None:
                instances = []
            running_number = len(
                [x for x in instances if x['status'].upper() == "RUNNING"])
            item['Provisioning Status'] = deployment['properties']['provisioningState']
            item['CPU'] = deployment['properties']['deploymentSettings']['cpu']
            item['Memory'] = deployment['properties']['deploymentSettings']['memory']
            item['Running Instance'] = "{}/{}".format(running_number, instance_count) if isStarted else "Stopped"
    return result if is_list else result[0]
