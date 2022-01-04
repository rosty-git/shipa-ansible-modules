import re
import base64
from datetime import timedelta
from ansible.module_utils.six.moves.urllib.parse import urlencode

from ansible.module_utils.urls import fetch_url

regex = re.compile(
    r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$'
)


def parse_duration(duration):
    """
    Parse a duration string e.g. (2h13m) into a timedelta object.

    :param duration: A string identifying a duration.  (eg. 2h13m)
    :return datetime.timedelta: A datetime.timedelta object
    """
    parts = regex.match(duration)
    assert parts is not None, \
        "Could not parse any time information from '{}'.  " \
        "Examples of valid strings: '8h', '2d8h5m20s', '2m4s'".format(duration)

    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return timedelta(**time_params)


def form_urlencoded(params):
    """ Convert data into a form-urlencoded string """
    # result = [(to_text(key), to_text(value)) for key, value in params.items()]
    result = [(key, value) for key, value in params.items()]
    return urlencode(result, doseq=True)


class HTTPStatus:
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400


class Endpoint:
    PLAN = 'plans'
    FRAMEWORK = 'pools-config'
    APPLICATION = 'apps'
    CLUSTER = 'provisioner/clusters'

    def __init__(self, host):
        self.host = host

    def plan(self, resource_name=None):
        return self._url(self.PLAN, resource_name)

    def framework(self, resource_name=None):
        return self._url(self.FRAMEWORK, resource_name)

    def application(self, resource_name=None):
        return self._url(self.APPLICATION, resource_name)

    def cluster(self, resource_name=None):
        return self._url(self.CLUSTER, resource_name)

    def app_deploy(self, app):
        return '{}/deploy'.format(self._url(self.APPLICATION, app))

    def app_cname(self, app):
        return '{}/cname'.format(self._url(self.APPLICATION, app))

    def app_env(self, app):
        return '{}/env'.format(self._url(self.APPLICATION, app))

    def network_policy(self, app):
        return '{}/network-policy'.format(self._url(self.APPLICATION, app))

    def _url(self, endpoint, resource_name=None):
        url = '{}/{}'.format(self.host, endpoint)
        if resource_name:
            url = '{}/{}'.format(url, resource_name)
        return url


class Client:
    def __init__(self, module, host, token):
        self.module = module
        self.token = token
        self._resource = Endpoint(host)

    def test_access(self):
        ok, _ = self._get(self._resource.plan())
        return ok, '' if ok else 'shipa client auth failed'

    def get_framework(self, name):
        return self._get(self._resource.framework(name))

    def create_framework(self, name, resources=None):
        return self._post(self._resource.framework(), self._prepare_framework_payload(name, resources))

    def update_framework(self, name, resources=None):
        return self._put(self._resource.framework(), self._prepare_framework_payload(name, resources))

    @staticmethod
    def _prepare_framework_payload(name, resources=None):
        if not resources:
            resources = {
                "general": {
                    "setup": {
                        "provisioner": "kubernetes"
                    }
                }
            }

        return {
            "shipaFramework": name,
            "resources": resources
        }

    def get_application(self, name):
        return self._get(self._resource.application(name))

    def create_application(self, app):
        return self._post(self._resource.application(), app)

    def update_application(self, name, app):
        payload = {
            key: app.get(key) for key in ('pool', 'teamowner', 'description', 'plan', 'platform', 'tags')
        }
        return self._put(self._resource.application(name), payload)

    def get_cluster(self, name):
        return self._get(self._resource.cluster(name))

    def create_cluster(self, payload):
        return self._post(self._resource.cluster(), payload)

    def update_cluster(self, name, payload):
        return self._put(self._resource.cluster(name), payload)

    def deploy_app(self, req):
        params = {
            'image': req['image']
        }

        if req.get('private_image'):
            params['private-image'] = 'true'
            params['registry-user'] = req.get('registry_user')
            params['registry-secret'] = req.get('registry_secret')

        if req.get('steps'):
            params['steps'] = str(req.get('steps'))

        if req.get('step_weight'):
            params['step-weight'] = str(req.get('step_weight'))

        if req.get('step_interval'):
            d = parse_duration(req.get('step_interval'))
            params['step-interval'] = d.seconds

        if req.get('port'):
            params['port-number'] = int(req.get('port'))
            params['port-protocol'] = 'TCP'

        if req.get('detach'):
            params['detach'] = 'true'

        if req.get('message'):
            params['message'] = req.get('message')

        if req.get('shipayaml'):
            with open(req.get('shipayaml')) as f:
                content = f.read()
                content_bytes = content.encode('ascii')
                base64_bytes = base64.b64encode(content_bytes)
                params['shipayaml'] = base64_bytes.decode('ascii')

        url = self._resource.app_deploy(req['app'])
        payload = form_urlencoded(params)
        headers = self._headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        kwargs = {
            'headers': headers,
            'method': 'POST',
            'timeout': 1500,
            'data': payload
        }

        resp, info = fetch_url(self.module, url, **kwargs)
        status_code = info.get('status', HTTPStatus.BAD_REQUEST)
        ok = status_code in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED)
        body = info.get('body') or resp.read()
        if 'There are vulnerabilities!' in str(body):
            ok = False
        return ok, body

    def create_app_cname(self, req):
        return self._post(self._resource.app_cname(req['app']), req)

    def create_app_env(self, req):
        return self._post(self._resource.app_env(req['app']), req)

    def create_network_policy(self, req):
        return self._put(self._resource.network_policy(req['app']), req)

    def get_network_policy(self, app):
        return self._get(self._resource.network_policy(app))

    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.token),
        }

    def _get(self, url):
        status_code, body = self._raw_request('GET', url)
        return status_code == HTTPStatus.OK, self.module.from_json(body)

    def _post(self, url, payload):
        status_code, body = self._raw_request('POST', url, payload)
        return status_code in (HTTPStatus.OK, HTTPStatus.CREATED), body

    def _put(self, url, payload):
        status_code, body = self._raw_request('PUT', url, payload)
        return status_code == HTTPStatus.OK, body

    def _raw_request(self, method, url, payload=None):
        kwargs = {
            'headers': self._headers(),
            'method': method,
            'timeout': 1500
        }
        if payload:
            kwargs['data'] = self.module.jsonify(payload)

        resp, info = fetch_url(self.module, url, **kwargs)
        status_code = info.get('status', HTTPStatus.BAD_REQUEST)
        body = info.get('body') if status_code >= HTTPStatus.BAD_REQUEST else resp.read()
        return status_code, body
