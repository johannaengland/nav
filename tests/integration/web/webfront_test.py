from mock import Mock

from django.urls import reverse
from django.utils.encoding import smart_str
from nav.models.profiles import AccountDashboard
from nav.web.webfront.utils import tool_list


def test_tools_should_be_readable():
    admin = Mock()
    tools = tool_list(admin)
    assert len(tools) > 0


def test_set_default_dashboard_should_succeed(db, client, admin_account):
    """Tests that a default dashboard can be set"""
    dashboard = AccountDashboard.objects.create(
        name="new_default",
        is_default=False,
        account=admin_account,
    )
    url = reverse("set-default-dashboard", args=(dashboard.pk,))
    response = client.post(url, follow=True)

    dashboard.refresh_from_db()

    assert response.status_code == 200
    assert f"Default dashboard set to «{dashboard.name}»" in smart_str(response.content)
    assert dashboard.is_default
    assert (
        AccountDashboard.objects.filter(account=admin_account, is_default=True).count()
        == 1
    )


def test_set_default_dashboard_with_multiple_previous_defaults_should_succeed(
    db, client, admin_account
):
    """
    Tests that a default dashboard can be set if multiple default dashboards
    exist currently
    """
    # By default there already exists one default dashboard for the admin user
    # which is why we only have to create a second default one
    default_dashboard = AccountDashboard.objects.create(
        name="default_dashboard",
        is_default=True,
        account=admin_account,
    )
    dashboard = AccountDashboard.objects.create(
        name="new_default",
        is_default=False,
        account=admin_account,
    )
    url = reverse("set-default-dashboard", args=(dashboard.pk,))
    response = client.post(url, follow=True)

    default_dashboard.refresh_from_db()
    dashboard.refresh_from_db()

    assert response.status_code == 200
    assert f"Default dashboard set to «{dashboard.name}»" in smart_str(response.content)
    assert dashboard.is_default
    assert not default_dashboard.is_default
    assert (
        AccountDashboard.objects.filter(account=admin_account, is_default=True).count()
        == 1
    )


def test_session_id_is_changed_after_logging_in(
    db, client, admin_username, admin_password
):
    login_url = reverse('webfront-login')
    logout_url = reverse('webfront-logout')
    # log out first to compare before and after being logged in
    client.post(logout_url)
    # make sure we have a session ID we can use for comparison
    assert client.session.session_key
    session_id_pre_login = client.session.session_key
    client.post(login_url, {'username': admin_username, 'password': admin_password})
    session_id_post_login = client.session.session_key
    assert session_id_post_login != session_id_pre_login


def test_session_id_is_not_changed_after_request_unrelated_to_login(db, client):
    index_url = reverse('webfront-index')
    # make sure we have a session ID we can use for comparison
    assert client.session.session_key
    session_id_pre_login = client.session.session_key
    client.get(index_url)
    session_id_post_login = client.session.session_key
    assert session_id_post_login == session_id_pre_login
