#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: shipa_app_deploy

short_description: Shipa app deploy module

version_added: "0.0.1"

description: This is module allows to deploy Shipa application.

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
    image:
        description: Shipa application image.
        required: true
        type: str
    port:
        description: Shipa application port.
        required: true
        type: int
    
    private-image:
        description: Is a private image.
        required: false
        type: bool
    registry-user:
        description: Private docker registry user name.
        required: false
        type: str
    registry-secret:
        description: Private docker registry secret.
        required: false
        type: str
    steps:
        description: Steps.
        required: false
        type: int
    step-weight:
        description: Step weight.
        required: false
        type: int
    step-interval:
        description: Step interval.
        required: false
        type: str
    detach:
        description: Detach.
        required: false
        type: bool
    message:
        description: Message.
        required: false
        type: str
    shipayaml:
        description: ShipaYaml.
        required: false
        type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        app=dict(type='str', required=True),
        image=dict(type='str', required=True),
        port=dict(type='int', required=True),

        private_image=dict(type='bool', required=False),
        registry_user=dict(type='str', required=False),
        registry_secret=dict(type='str', required=False),
        steps=dict(type='int', required=False),
        step_weight=dict(type='int', required=False),
        step_interval=dict(type='str', required=False),
        detach=dict(type='bool', required=False),
        message=dict(type='str', required=False),
        shipayaml=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_app_deploy={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    shipa = Client(module, module.params['shipa_host'], module.params['shipa_token'])
    ok, err = shipa.test_access()
    if not ok:
        module.fail_json(msg=err)

    keys = filter(lambda key: not key.startswith('shipa_'), module_args.keys())
    req = {
        key: module.params.get(key) for key in keys
    }

    name = module.params['app']
    exists, resp = shipa.get_application(name)
    if not exists:
        module.fail_json(msg=resp)

    ok, resp = shipa.deploy_app(req)
    if not ok or 'error' in str(resp).lower():
        module.fail_json(msg=resp)

    result['status'] = 'SUCCESS'
    result['shipa_app_deploy'] = resp
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
