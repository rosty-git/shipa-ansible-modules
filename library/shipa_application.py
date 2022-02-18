#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: shipa_application

short_description: Shipa application module

version_added: "0.0.1"

description: This is module allows to create Shipa application.

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
        description: Shipa application name.
        required: true
        type: str
    framework:
        description: Shipa application framework.
        required: true
        type: str
    teamowner:
        description: Shipa application teamowner.
        required: true
        type: str
    
    description:
        description: Shipa application description.
        required: false
        type: str
    plan:
        description: Shipa application plan.
        required: false
        type: dict
    units:
        description: Shipa application units.
        required: false
        type: list
    cname:
        description: Shipa application cname.
        required: false
        type: list
    ip:
        description: Shipa application ip.
        required: false
        type: str
    org:
        description: Shipa application org.
        required: false
        type: str
    entrypoints:
        description: Shipa application entrypoints.
        required: false
        type: list
    routers:
        description: Shipa application routers.
        required: false
        type: list
    lock:
        description: Shipa framework lock.
        required: false
        type: dict
    tags:
        description: Shipa application tags.
        required: false
        type: list
    platform:
        description: Shipa application platform.
        required: false
        type: str
    status:
        description: Shipa application status.
        required: false
        type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shipa_client import Client


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        framework=dict(type='str', required=True),
        teamowner=dict(type='str', required=True),
        plan=dict(type='str', required=True),
        tags=dict(type='list', required=True),

        # description=dict(type='str', required=False),
        # units=dict(type='list', required=False),
        # cname=dict(type='list', required=False),
        # ip=dict(type='str', required=False),
        # org=dict(type='str', required=False),
        # entrypoints=dict(type='list', required=False),
        # routers=dict(type='list', required=False),
        # lock=dict(type='dict', required=False),
        # platform=dict(type='str', required=False),
        # status=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_application={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    shipa = Client(module, module.params['shipa_host'], module.params['shipa_token'])
    ok, err = shipa.test_access()
    if not ok:
        module.fail_json(msg=err)

    keys = filter(lambda key: not key.startswith('shipa_'), module_args.keys())
    app = {
        key: module.params.get(key) for key in keys
    }
    app['pool'] = app['framework']
    del app['framework']
    app['teamOwner'] = app['teamowner']
    del app['teamowner']

    name = module.params['name']
    exists, current_state = shipa.get_application(name)

    if exists:
        ok, resp = shipa.update_application(name, app)
    else:
        ok, resp = shipa.create_application(app)

    if not ok or '"error"' in str(resp).lower():
        module.fail_json(msg=resp)

    ok, resp = shipa.get_application(name)
    if not ok:
        module.fail_json(msg=resp)

    ignore_field = 'updatedAt'
    if ignore_field in resp:
        del resp[ignore_field]
    if ignore_field in current_state:
        del current_state[ignore_field]

    changed = not exists or current_state != resp

    result['status'] = "SUCCESS"
    result['shipa_application'] = resp
    result['changed'] = changed

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
