#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type


DOCUMENTATION = r'''
---
module: shipa_job

short_description: Shipa job module

version_added: "0.0.1"

description: This is module allows to create Shipa job.

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
        description: Shipa job name.
        required: true
        type: str
    framework:
        description: Shipa framework name.
        required: true
        type: str
    containers:
        description: Shipa job containers.
        required: true
        type: list
    policy:
        description: Shipa job policy.
        required: true
        type: dict
    
    description:
        description: Shipa job description.
        required: false
        type: str
    backoffLimit:
        description: Shipa job backoffLimit.
        required: false
        type: int
    completions:
        description: Shipa job completions.
        required: false
        type: int
    parallelism:
        description: Shipa job parallelism.
        required: false
        type: int
    suspend:
        description: Shipa job suspend flag.
        required: false
        type: bool
    team:
        description: Shipa job team.
        required: false
        type: str
    type:
        description: Shipa job type.
        required: false
        type: str
    version:
        description: Shipa job version.
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
        containers=dict(type='list', required=True),
        policy=dict(type='dict', required=True),

        description=dict(type='str', required=False),
        backoffLimit=dict(type='int', required=False),
        completions=dict(type='int', required=False),
        parallelism=dict(type='int', required=False),
        suspend=dict(type='bool', required=False),
        team=dict(type='str', required=False),
        type=dict(type='str', required=False),
        version=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        status='',
        shipa_job={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    shipa = Client(module, module.params['shipa_host'], module.params['shipa_token'])
    ok, err = shipa.test_access()
    if not ok:
        module.fail_json(msg=err)

    keys = filter(lambda key: not key.startswith('shipa_'), module_args.keys())
    job = {
        key: module.params.get(key) for key in keys
    }

    name = module.params['name']
    exists, current_state = shipa.get_job(name)
    if not exists:
        ok, resp = shipa.create_job(job)
        if not ok or '"error"' in str(resp).lower():
            module.fail_json(msg=resp)

    ok, resp = shipa.get_job(name)
    if not ok:
        module.fail_json(msg=resp)

    changed = not exists or current_state != resp

    result['status'] = "SUCCESS"
    result['shipa_job'] = resp
    result['changed'] = changed

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
