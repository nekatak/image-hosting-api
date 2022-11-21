import os
import json

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from user.models import User
from plan.models import Plan


class ImageTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.root_url = "/api/images/"
        self.user = User.objects.create_user(
            username="test",
            email="test@test.com",
            password="test",
        )
        basic_plan = Plan.objects.filter(name="Basic").first()
        assert basic_plan
        self.user.plan = basic_plan
        self.user.save()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def tearDown(self):
        self.token.delete()
        self.user.delete()

    def test_images_api(self):
        """
        Test sequencially post, list, and retrieve file api's.
        """
        filepath = (
                os.path.dirname(os.path.realpath(__file__)) +
                '/test_assets/test.png'
        )
        with open(filepath, 'rb') as rf:
            resp = self.client.post(
                self.root_url,
                data={"name": "test_file", "image_field": rf}
            )
            assert resp.status_code == 201
            object_id = json.loads(resp.content)["id"]

        # retrieve files
        resp = self.client.get(self.root_url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content

        assert any(
            item["id"] == object_id for item in content
        )

        link = None
        for item in content:
            if item["id"] == object_id:
                link = item["links"][0]["uri"]

        assert link
        # retrieve actual thumb
        resp = self.client.get(link.split("http://localhost:8000")[1])
        assert resp.status_code == 200
        assert resp.streaming_content
