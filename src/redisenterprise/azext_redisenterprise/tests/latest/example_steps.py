# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------


from .. import try_manual


# EXAMPLE: /RedisEnterprise/put/RedisEnterpriseCreate
@try_manual
def step_create(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise create '
             '--cluster-name "{myRedisEnterprise}" '
             '--location "West US" '
             '--minimum-tls-version "1.2" '
             '--sku "EnterpriseFlash_F300" '
             '--capacity 3 '
             '--tags tag1="value1" '
             '--zones "1" "2" "3" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /RedisEnterprise/get/RedisEnterpriseGet
@try_manual
def step_show(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise show '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /RedisEnterprise/get/RedisEnterpriseList
@try_manual
def step_list(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise list '
             '-g ""',
             checks=checks)


# EXAMPLE: /RedisEnterprise/get/RedisEnterpriseListByResourceGroup
@try_manual
def step_list2(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise list '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /RedisEnterprise/patch/RedisEnterpriseUpdate
@try_manual
def step_update(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise update '
             '--cluster-name "{myRedisEnterprise}" '
             '--minimum-tls-version "1.2" '
             '--sku "EnterpriseFlash_F300" '
             '--capacity 9 '
             '--tags tag1="value1" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/put/RedisEnterpriseDatabasesCreate
@try_manual
def step_database_create(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database create '
             '--cluster-name "{myRedisEnterprise}" '
             '--client-protocol "Encrypted" '
             '--clustering-policy "EnterpriseCluster" '
             '--eviction-policy "AllKeysLRU" '
             '--modules name="RedisBloom" args="ERROR_RATE 0.00 INITIAL_SIZE 400" '
             '--modules name="RedisTimeSeries" args="RETENTION_POLICY 20" '
             '--modules name="RediSearch" '
             '--persistence aof-enabled=true aof-frequency="1s" '
             '--port 10000 '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/put/RedisEnterpriseDatabasesCreate With Active Geo Replication
@try_manual
def step_database_create2(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database create '
             '--cluster-name "{myRedisEnterprise}" '
             '--client-protocol "Encrypted" '
             '--clustering-policy "EnterpriseCluster" '
             '--eviction-policy "NoEviction" '
             '--group-nickname "groupName" '
             '--linked-databases id="/subscriptions/{subscription_id}/resourceGroups/{rg}/providers/Microsoft.Cache/red'
             'isEnterprise/{myRedisEnterprise}/databases/{myDatabas}" '
             '--linked-databases id="/subscriptions/{subscription_id}/resourceGroups/{rg_2}/providers/Microsoft.Cache/r'
             'edisEnterprise/{myRedisEnterprise2}/databases/{myDatabas}" '
             '--port 10000 '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/get/RedisEnterpriseDatabasesGet
@try_manual
def step_database_show(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database show '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/get/RedisEnterpriseDatabasesListByCluster
@try_manual
def step_database_list(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database list '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/patch/RedisEnterpriseDatabasesUpdate
@try_manual
def step_database_update(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database update '
             '--cluster-name "{myRedisEnterprise}" '
             '--client-protocol "Encrypted" '
             '--eviction-policy "AllKeysLRU" '
             '--persistence rdb-enabled=true rdb-frequency="12h" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/How to unlink a database during a regional outage
@try_manual
def step_database_force_unlink(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database force-unlink '
             '--cluster-name "{myRedisEnterprise}" '
             '--unlink-ids "/subscriptions/{subscription_id}/resourceGroups/{rg_2}/providers/Microsoft.Cache/redisEnterprise/{'
             'myRedisEnterprise2}/databases/{myDatabas}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesExport
@try_manual
def step_database_export(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database export '
             '--cluster-name "{myRedisEnterprise}" '
             '--sas-uri "https://contosostorage.blob.core.window.net/urlToBlobContainer?sasKeyParameters" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesImport
@try_manual
def step_database_import(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database import '
             '--cluster-name "{myRedisEnterprise}" '
             '--sas-uris "https://contosostorage.blob.core.window.net/urltoBlobFile1?sasKeyParameters" '
             '"https://contosostorage.blob.core.window.net/urltoBlobFile2?sasKeyParameters" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesListKeys
@try_manual
def step_database_list_keys(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database list-keys '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesRegenerateKey
@try_manual
def step_database_regenerate_key(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database regenerate-key '
             '--cluster-name "{myRedisEnterprise}" '
             '--key-type "Primary" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/delete/RedisEnterpriseDatabasesDelete
@try_manual
def step_database_delete(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database delete -y '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /OperationsStatus/get/OperationsStatusGet
@try_manual
def step_operation_status_show(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise operation-status show '
             '--operation-id "testoperationid" '
             '--location "West US"',
             checks=checks)


# EXAMPLE: /RedisEnterprise/delete/RedisEnterpriseDelete
@try_manual
def step_delete(test, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise delete -y '
             '--cluster-name "{myRedisEnterprise}" '
             '--resource-group "{rg}"',
             checks=checks)
