#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: shipa_network_policy

short_description: Shipa network policy module

version_added: "0.0.1"

description: This is module allows to create Shipa network policy.

options:
    shipa_host:
        description: Shipa server host.
        required: true
        type: str
    shipa_token:
        description: Shipa API token.
        required: true
        type: str
    app:
        description: Shipa application name.
        required: true
        type: str
    ingress:
        description: Shipa network policy config.
        required: false
        type: dict
    egress:
        description: Shipa network policy config.
        required: false
        type: dict
    restart_app:
        description: Shipa network policy restart app flag.
        required: false
        type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        app=dict(type='str', required=True),
        ingress=dict(type='dict', required=False),
        egress=dict(type='dict', required=False),
        restart_app=dict(type='bool', default=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_network_policy={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    shipa = Client(module, module.params['shipa_host'], module.params['shipa_token'])
    ok, err = shipa.test_access()
    if not ok:
        module.fail_json(msg=err)

    keys = filter(lambda key: not key.startswith('shipa_'), module_args.keys())
    payload = {
        key: module.params.get(key) for key in keys
    }

    name = module.params['app']
    exists, resp = shipa.get_application(name)
    if not exists:
        module.fail_json(msg=resp)

    ok, resp = shipa.create_network_policy(payload)
    if not ok or '"error"' in str(resp).lower():
        module.fail_json(msg=resp)

    ok, resp = shipa.get_network_policy(name)
    if not ok:
        module.fail_json(msg=resp)

    result['status'] = "SUCCESS"
    result['shipa_network_policy'] = resp
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
