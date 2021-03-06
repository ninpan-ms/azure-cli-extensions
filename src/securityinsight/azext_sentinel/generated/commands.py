# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):

    from azext_sentinel.generated._client_factory import cf_alert_rule
    sentinel_alert_rule = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._alert_rule_operations#AlertRuleOperat'
        'ions.{}',
        client_factory=cf_alert_rule)
    with self.command_group('sentinel alert-rule', sentinel_alert_rule, client_factory=cf_alert_rule,
                            is_experimental=True) as g:
        g.custom_command('list', 'sentinel_alert_rule_list')
        g.custom_show_command('show', 'sentinel_alert_rule_show')
        g.custom_command('create', 'sentinel_alert_rule_create')
        g.generic_update_command('update', setter_arg_name='alert_rule',
                                 custom_func_name='sentinel_alert_rule_update')
        g.custom_command('delete', 'sentinel_alert_rule_delete', confirmation=True)
        g.custom_command('get-action', 'sentinel_alert_rule_get_action')

    from azext_sentinel.generated._client_factory import cf_action
    sentinel_action = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._action_operations#ActionOperations.{}'
        '',
        client_factory=cf_action)
    with self.command_group('sentinel action', sentinel_action, client_factory=cf_action, is_experimental=True) as g:
        g.custom_command('list', 'sentinel_action_list')

    from azext_sentinel.generated._client_factory import cf_alert_rule_template
    sentinel_alert_rule_template = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._alert_rule_template_operations#AlertR'
        'uleTemplateOperations.{}',
        client_factory=cf_alert_rule_template)
    with self.command_group('sentinel alert-rule-template', sentinel_alert_rule_template,
                            client_factory=cf_alert_rule_template, is_experimental=True) as g:
        g.custom_command('list', 'sentinel_alert_rule_template_list')
        g.custom_show_command('show', 'sentinel_alert_rule_template_show')

    from azext_sentinel.generated._client_factory import cf_bookmark
    sentinel_bookmark = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._bookmark_operations#BookmarkOperation'
        's.{}',
        client_factory=cf_bookmark)
    with self.command_group('sentinel bookmark', sentinel_bookmark, client_factory=cf_bookmark,
                            is_experimental=True) as g:
        g.custom_command('list', 'sentinel_bookmark_list')
        g.custom_show_command('show', 'sentinel_bookmark_show')
        g.custom_command('create', 'sentinel_bookmark_create')
        g.custom_command('update', 'sentinel_bookmark_update')
        g.custom_command('delete', 'sentinel_bookmark_delete', confirmation=True)

    from azext_sentinel.generated._client_factory import cf_data_connector
    sentinel_data_connector = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._data_connector_operations#DataConnect'
        'orOperations.{}',
        client_factory=cf_data_connector)
    with self.command_group('sentinel data-connector', sentinel_data_connector, client_factory=cf_data_connector,
                            is_experimental=True) as g:
        g.custom_command('list', 'sentinel_data_connector_list')
        g.custom_show_command('show', 'sentinel_data_connector_show')
        g.custom_command('create', 'sentinel_data_connector_create')
        g.generic_update_command('update', setter_arg_name='data_connector', custom_func_name=''
                                 'sentinel_data_connector_update')
        g.custom_command('delete', 'sentinel_data_connector_delete', confirmation=True)

    from azext_sentinel.generated._client_factory import cf_incident
    sentinel_incident = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._incident_operations#IncidentOperation'
        's.{}',
        client_factory=cf_incident)
    with self.command_group('sentinel incident', sentinel_incident, client_factory=cf_incident,
                            is_experimental=True) as g:
        g.custom_command('list', 'sentinel_incident_list')
        g.custom_show_command('show', 'sentinel_incident_show')
        g.custom_command('create', 'sentinel_incident_create')
        g.custom_command('update', 'sentinel_incident_update')
        g.custom_command('delete', 'sentinel_incident_delete', confirmation=True)

    from azext_sentinel.generated._client_factory import cf_incident_comment
    sentinel_incident_comment = CliCommandType(
        operations_tmpl='azext_sentinel.vendored_sdks.securityinsight.operations._incident_comment_operations#IncidentC'
        'ommentOperations.{}',
        client_factory=cf_incident_comment)
    with self.command_group('sentinel incident-comment', sentinel_incident_comment, client_factory=cf_incident_comment,
                            is_experimental=True) as g:
        g.custom_command('list', 'sentinel_incident_comment_list')
        g.custom_show_command('show', 'sentinel_incident_comment_show')
        g.custom_command('create', 'sentinel_incident_comment_create')
