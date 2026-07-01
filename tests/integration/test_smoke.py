import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_lobby_page_loads(client):
    resp = client.get(reverse("tournaments:lobby"))
    assert resp.status_code == 200
    assert b"Football Elo Market" in resp.content


@pytest.mark.django_db
def test_login_page_loads(client):
    resp = client.get(reverse("accounts:login"))
    assert resp.status_code == 200


def test_admin_registered():
    from django.contrib import admin
    assert admin.site is not None
