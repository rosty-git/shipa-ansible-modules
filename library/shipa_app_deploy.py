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
    appConfig:
        description: Application configuration.
        required: true
        type: dict
    
    canarySettings:
        description: Application canary settings.
        required: false
        type: dict
    podAutoScaler:
        description: Pod auto-scaler settings.
        required: false
        type: dict
    port:
        description: Application port settings.
        required: false
        type: dict
    registry:
        description: Private registry settings.
        required: false
        type: dict
    volumes:
        description: Volumes options.
        required: false
        type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        app=dict(type='str', required=True),
        image=dict(type='str', required=True),

        appConfig=dict(type='dict', required=False),
        canarySettings=dict(type='dict', required=False),
        podAutoScaler=dict(type='dict', required=False),
        port=dict(type='dict', required=False),
        registry=dict(type='dict', required=False),
        volumes=dict(type='list', required=False),
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

    if req.get('port') and req['port'].get('protocol', '') == '':
        req['port']['protocol'] = "TCP"

    if req.get('volumes'):
        volumes = []
        for v in req.get('volumes'):
            vol = {
                'volumeName': v.get('name'),
                'volumeMountPath': v.get('mountPath'),
            }
            if v.get('mountOptions'):
                vol['volumeMountOptions'] = v.get('mountOptions')
            volumes.append(vol)
        req['volumesToBind'] = volumes
        del req['volumes']

    ok, resp = shipa.deploy_app(req)
    if not ok or '"error"' in str(resp).lower():
        module.fail_json(msg=resp)

    result['status'] = 'SUCCESS'
    result['shipa_app_deploy'] = resp
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
