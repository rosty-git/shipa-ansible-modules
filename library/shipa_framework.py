#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: shipa_framework

short_description: Shipa framework module

version_added: "0.0.1"

description: This is module allows to create Shipa framework.

options:
    shipa_host:
        description: Shipa server host.
        required: true
        type: str
    shipa_token:
        description: Shipa API token.
        required: true
        type: str
    name:
        description: Shipa framework name.
        required: true
        type: str
    resources:
        description: Shipa framework resources.
        required: false
        type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        resources=dict(type='dict', required=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_framework={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    shipa = Client(module, module.params['shipa_host'], module.params['shipa_token'])
    ok, err = shipa.test_access()
    if not ok:
        module.fail_json(msg=err)

    name, resources = module.params['name'], module.params.get('resources')
    exists, current_state = shipa.get_framework(name)
    if not exists:
        ok, resp = shipa.create_framework(name, resources)
        changed = True
    else:
        ok, resp = shipa.update_framework(name, resources)
        changed = current_state != resp

    if not ok:
        module.fail_json(msg=resp)

    result['status'] = "SUCCESS"
    result['shipa_framework'] = resp
    result['changed'] = changed

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
