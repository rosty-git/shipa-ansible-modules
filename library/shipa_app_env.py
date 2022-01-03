#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: shipa_app_env

short_description: Shipa app-env module

version_added: "0.0.1"

description: This is module allows to create Shipa app env.

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
    envs:
        description: Shipa application envs.
        required: true
        type: list
    norestart:
        description: Shipa app envs norestart flag.
        required: false
        type: bool
    private:
        description: Shipa app envs private flag.
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
        envs=dict(type='list', required=True),
        norestart=dict(type='bool', default=False),
        private=dict(type='bool', default=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_app_env={},
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

    ok, resp = shipa.create_app_env(payload)
    if not ok or '"error"' in str(resp).lower():
        module.fail_json(msg=resp)

    result['status'] = "SUCCESS"
    result['shipa_app_env'] = resp
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
