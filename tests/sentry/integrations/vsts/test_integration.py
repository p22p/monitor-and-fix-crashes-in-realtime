from __future__ import absolute_import

import responses


from mock import Mock
from django.http import HttpRequest
from time import time

from sentry.integrations.vsts import VstsIntegration, VstsIntegrationProvider, ProjectConfigView, ProjectForm, get_projects
from sentry.identity.vsts import VSTSIdentityProvider
from sentry.models import Integration, Identity, IdentityProvider
from sentry.testutils import TestCase


class ProjectConfigViewTest(TestCase):
    def setUp(self):
        self.instance = 'example.visualstudio.com'
        self.projects = [
            {
                'id': 'first-project-id',
                'name': 'First Project',
                        'url': 'https://myfirstproject.visualstudio.com/DefaultCollection/_apis/projects/xxxxxxx-xxxx-xxxx-xxxxxxxxxxxxxxxx',
                        'description': 'My First Project!',
            },
            {
                'id': 'second-project-id',
                'name': 'Second Project',
                        'url': 'https://mysecondproject.visualstudio.com/DefaultCollection/_apis/projects/xxxxxxx-xxxx-xxxx-xxxxxxxxxxxxxxxz',
                        'description': 'Not My First Project!',
            }
        ]
        responses.add(
            responses.GET,
            'https://{}/DefaultCollection/_apis/projects'.format(self.instance),
            json={
                'value': self.projects,
                'count': 2,
            },
        )

    @responses.activate
    def test_get_projects(self):
        result = get_projects(self.instance, 'access-token')
        assert result['count'] == 2
        assert result['value'][0]['name'] == 'First Project'
        assert result['value'][1]['name'] == 'Second Project'

    def test_project_form(self):
        project_form = ProjectForm(self.projects)
        assert project_form.fields['project'].choices == [
            ('first-project-id', 'First Project'), ('second-project-id', 'Second Project')]

    def test_dispatch(self):
        view = ProjectConfigView()
        request = HttpRequest()
        request.POST = {'project': 'first-project-id'}

        pipeline = Mock()
        pipeline.state = {'projects': self.projects}
        pipeline.fetch_state = lambda key: pipeline.state[key]
        pipeline.bind_state = lambda name, value: pipeline.state.update({name: value})

        view.dispatch(request, pipeline)

        assert pipeline.fetch_state(key='project') == self.projects[0]
        assert pipeline.next_step.call_count == 1


class VstsIntegrationProviderTest(TestCase):
    def setUp(self):
        self.integration = VstsIntegrationProvider()

    def test_build_integration(self):
        state = {
            'identity': {
                'data': {
                    'access_token': 'xxx-xxxx',
                    'expires_in': '3600',
                    'refresh_token': 'rxxx-xxxx',
                    'token_type': 'jwt-bearer',
                },
                'account': {'AccountName': 'sentry', 'AccountId': '123435'},
                'instance': 'sentry.visualstudio.com',
            },
            'project': {'name': 'My Project', 'id': 'my-project-id'},
        }
        integration_dict = self.integration.build_integration(state)
        assert integration_dict['name'] == 'My Project'
        assert integration_dict['external_id'] == 'my-project-id'
        assert integration_dict['metadata']['scopes'] == list(VSTSIdentityProvider.oauth_scopes)
        assert integration_dict['metadata']['domain_name'] == 'sentry.visualstudio.com'

        assert integration_dict['user_identity']['type'] == 'vsts'
        assert integration_dict['user_identity']['external_id'] == '123435'
        assert integration_dict['user_identity']['scopes'] == []

        assert integration_dict['user_identity']['data']['access_token'] == 'xxx-xxxx'
        assert isinstance(integration_dict['user_identity']['data']['expires'], int)
        assert integration_dict['user_identity']['data']['refresh_token'] == 'rxxx-xxxx'
        assert integration_dict['user_identity']['data']['token_type'] == 'jwt-bearer'


class VstsIntegrationTestCase(TestCase):

    def setUp(self):
        self.user = self.create_user()
        self.organization = self.create_organization()
        self.access_token = '1234567890'
        self.instance = 'instance.visualstudio.com'
        self.model = Integration.objects.create(
            provider='integrations:vsts',
            external_id='vsts_external_id',
            name='vsts_name',
            metadata={
                'domain_name': 'sentryuser.visualstudio.com',
            }
        )
        self.identity_provider = IdentityProvider.objects.create(type='vsts')
        self.identity = Identity.objects.create(
            idp=self.identity_provider,
            user=self.user,
            external_id='vsts_id',
            data={
                'access_token': self.access_token,
                'refresh_token': 'qwertyuiop',
                'expires': int(time()) - int(1234567890),
            }
        )
        self.model.add_organization(self.organization.id, self.identity.id)
        self.integration = VstsIntegration(self.model, self.organization.id)

    def assert_identity_updated(self, new_identity, expected_data):
        assert new_identity.data['access_token'] == expected_data['access_token']
        assert new_identity.data['token_type'] == expected_data['token_type']
        assert new_identity.data['refresh_token'] == expected_data['refresh_token']
        assert new_identity.data['expires'] >= time()

    def test_get_client(self):
        client = self.integration.get_client()
        assert client.identity.data['access_token'] == self.access_token

    @responses.activate
    def test_refreshes_expired_token(self):

        projects = {'value': ['Project1', 'Project2'], 'count': 2, }
        refresh_data = {
            'access_token': 'access token for this user',
            'token_type': 'type of token',
            'expires_in': 123456789,
            'refresh_token': 'new refresh token to use when the token has timed out',
        }
        responses.add(
            responses.POST,
            'https://app.vssps.visualstudio.com/oauth2/token',
            json=refresh_data,
        )
        responses.add(
            responses.GET,
            'https://{}/DefaultCollection/_apis/projects'.format(self.instance),
            json=projects,
        )

        result = self.integration.get_client().get_projects(self.instance)

        assert len(responses.calls) == 2
        default_identity = self.integration.default_identity
        self.assert_identity_updated(default_identity, refresh_data)

        identity = Identity.objects.get(id=self.identity.id)
        self.assert_identity_updated(identity, refresh_data)

        assert result == projects
