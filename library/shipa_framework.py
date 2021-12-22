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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def test_shipa_access(module, shipa_host, shipa_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': "Bearer {}".format(shipa_token),
    }

    response, info = fetch_url(module, shipa_host + "/plans", headers=headers, method="GET")
    if info['status'] == 200:
        return True, ""
    else:
        return False, "shipa client auth failed"


def create_framework(module, shipa_host, shipa_token, name):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(shipa_token),
    }

    payload = {
        "shipaFramework": name,
        "resources": {
            "general": {
                "setup": {
                    "provisioner": "kubernetes"
                }
            }
        }
    }

    resp, info = fetch_url(module, shipa_host + "/pools-config", data=module.jsonify(payload),
                           headers=headers, method="POST")

    status_code = info["status"]
    body = resp.read()
    if status_code >= 400:
        body = info['body']

    if 200 <= status_code <= 201:
        return True, body

    return False, body


def run_module():
    module_args = dict(
        shipa_host=dict(type='str', required=True, no_log=True),
        shipa_token=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        status='',
        shipa_framework={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    ok, err = test_shipa_access(module, module.params['shipa_host'], module.params['shipa_token'])
    if not ok:
        module.fail_json(msg=err)

    ok, resp = create_framework(module, module.params['shipa_host'], module.params['shipa_token'],
                                module.params['name'])
    if not ok:
        module.fail_json(msg=resp)

    result['status'] = "SUCCESS"
    result['shipa_framework'] = resp
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
