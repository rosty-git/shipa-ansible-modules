from ansible.module_utils.urls import fetch_url


class HTTPStatus:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400


class Endpoint:
    PLAN = 'plans'
    FRAMEWORK = 'pools-config'

    def __init__(self, host):
        self.host = host

    def plan(self, resource_name=None):
        return self._url(self.PLAN, resource_name)

    def framework(self, resource_name=None):
        return self._url(self.FRAMEWORK, resource_name)

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

    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.token),
        }

    def _get(self, url):
        status_code, body = self._raw_request('GET', url)
        return status_code == HTTPStatus.OK, body

    def _post(self, url, payload):
        status_code, body = self._raw_request('POST', url, payload)
        return status_code in (HTTPStatus.OK, HTTPStatus.CREATED), body

    def _put(self, url, payload):
        status_code, body = self._raw_request('PUT', url, payload)
        return status_code == HTTPStatus.OK, body

    def _raw_request(self, method, url, payload=None):
        kwargs = {
            'headers': self._headers(),
            'method': method
        }
        if payload:
            kwargs['data'] = self.module.jsonify(payload)

        resp, info = fetch_url(self.module, url, **kwargs)
        status_code = info.get('status', HTTPStatus.BAD_REQUEST)
        body = info.get('body') if status_code >= HTTPStatus.BAD_REQUEST else resp.read()
        return status_code, body
