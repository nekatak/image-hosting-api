import os
import json
from pathlib import Path
from datetime import datetime, timedelta

import django.core.files
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from freezegun import freeze_time

from user.models import User
from plan.models import Plan
from image.models import Image


class BaseImageTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.root_url = "/api/images/"
        self.user = User.objects.create_user(
            username="test",
            email="test@test.com",
            password="test",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def tearDown(self):
        self.token.delete()
        self.user.delete()


class BasicPlanImageTestCase(BaseImageTestCase):
    def setUp(self):
        super().setUp()

        basic_plan = Plan.objects.filter(name="Basic").first()
        assert basic_plan
        self.user.plan = basic_plan
        self.user.save()

        path = Path('image/test_assets/test.png')
        with open(path, 'rb') as file:
            self.obj = Image(
                user=self.user,
                name='test_image',
                image_field=django.core.files.File(file, name=path.name)
            )
            self.obj.save()
            self.obj.store_thumbnails_and_links()

    def tearDown(self):
        super().tearDown()
        self.obj.delete()

    def test_images_api_list_basic_plan(self):
        resp = self.client.get(self.root_url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content

        assert any(
            item["id"] == str(self.obj.id) for item in content
        )
        # basic plan should have only one link for the small thumb
        assert len(content[0]["links"]) == 1

    def test_images_api_post_basic_plan(self):
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

    def test_images_api_get_image_file_basic_plan(self):
        resp = self.client.get(self.root_url)
        assert resp.status_code == 200
        content = json.loads(resp.content)

        link = None
        for item in content:
            if item["id"] == str(self.obj.id):
                assert len(item["links"]) == 1
                link = item["links"][0]["uri"]

        assert link

        # retrieve actual thumb
        resp = self.client.get(link.split("http://localhost:8000")[1])
        assert resp.status_code == 200
        assert resp.streaming_content


@freeze_time("2012-01-14")
class EnterprisePlanImageTestCase(BaseImageTestCase):
    """
    This will cover expiring links too. Otherwise functionality should be the
    same with the basic plan tests above.
    """
    def setUp(self):
        super().setUp()

        entrp_plan = Plan.objects.filter(name="Enterprise").first()
        assert entrp_plan
        self.user.plan = entrp_plan
        self.user.save()

        path = Path('image/test_assets/test.png')
        with open(path, 'rb') as file:
            self.obj = Image(
                user=self.user,
                name='test_image',
                image_field=django.core.files.File(file, name=path.name)
            )
            self.obj.save()
            self.obj.store_thumbnails_and_links()

    def tearDown(self):
        super().tearDown()
        self.obj.delete()

    def test_images_api_list_enterprise_plan(self):
        resp = self.client.get(self.root_url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content

        assert any(
            item["id"] == str(self.obj.id) for item in content
        )
        # This plan should include a 200, 400, original, and expiring
        assert len(content[0]["links"]) == 4
        # one should have an expiry
        assert any(item["expiry"] for item in content[0]["links"])

    def test_images_api_post_enterprise_plan(self):
        filepath = (
                os.path.dirname(os.path.realpath(__file__)) +
                '/test_assets/test.png'
        )
        with open(filepath, 'rb') as rf:
            resp = self.client.post(
                self.root_url,
                data={
                    "name": "test_file",
                    "image_field": rf,
                    "expiring_link_duration_seconds": 400,
                }
            )
            assert resp.status_code == 201

    def test_images_api_post_enterprise_plan_too_big_expiry(self):
        filepath = (
                os.path.dirname(os.path.realpath(__file__)) +
                '/test_assets/test.png'
        )
        with open(filepath, 'rb') as rf:
            resp = self.client.post(
                self.root_url,
                data={
                    "name": "test_file",
                    "image_field": rf,
                    "expiring_link_duration_seconds": 400000,
                }
            )
            assert resp.status_code == 400

    def test_images_api_get_image_file_with_expiry_enterprise_plan(self):
        resp = self.client.get(self.root_url)
        assert resp.status_code == 200
        content = json.loads(resp.content)

        link = None
        for item in content:
            if item["id"] == str(self.obj.id):
                assert len(item["links"]) == 4
                for ln in item["links"]:
                    if ln["expiry"]:
                        link = ln

        assert link

        # retrieve actual thumb
        resp = self.client.get(link["uri"].split("http://localhost:8000")[1])
        assert resp.status_code == 200
        assert resp.streaming_content

        expiry = datetime.strptime(link["expiry"], "%Y-%m-%dT%H:%M:%SZ")

        assert expiry == datetime.now() + timedelta(seconds=300)
