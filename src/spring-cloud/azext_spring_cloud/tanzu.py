# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, logging-format-interpolation, protected-access, wrong-import-order, too-many-lines

def tanzu_get(cmd, client, resource_group, name):
    return client.tanzu_services.get(resource_group, name)