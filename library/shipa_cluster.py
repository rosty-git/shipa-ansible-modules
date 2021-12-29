#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os.path

DOCUMENTATION = r'''
---
module: shipa_cluster

short_description: Shipa cluster module

version_added: "0.0.1"

description: This is module allows to create Shipa cluster.

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
        description: Shipa cluster name.
        required: true
        type: str
    endpoint:
        description: Shipa cluster endpoint.
        required: true
        type: dict
    resources:
        description: Shipa cluster resources.
        required: true
        type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        endpoint=dict(type='dict', required=True, no_log=True),
        resources=dict(type='dict', required=True),
    )

    result = dict(
        changed=False,
        status='',
        shipa_cluster={},
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

    cert = payload['endpoint'].get('caCert')
    if cert and os.path.exists(cert):
        with open(cert) as f:
            payload['endpoint']['caCert'] = f.read().strip(' \n')

    token = payload['endpoint'].get('token')
    if token and os.path.exists(token):
        with open(token) as f:
            payload['endpoint']['token'] = f.read().strip(' \n')

    name = module.params['name']
    exists, current_state = shipa.get_cluster(name)

    if exists:
        ok, resp = shipa.update_cluster(name, payload)
    else:
        ok, resp = shipa.create_cluster(payload)

    if not ok or '"error"' in str(resp).lower():
        module.fail_json(msg=resp)

    ok, resp = shipa.get_cluster(name)
    if not ok:
        module.fail_json(msg=resp)

    changed = not exists or current_state != resp

    result['status'] = "SUCCESS"
    result['shipa_cluster'] = resp
    result['changed'] = changed

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
