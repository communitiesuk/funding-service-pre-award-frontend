"""
Some very basic tests. Tests if the flask client spins
up and serves the index. This is a selected subset
of the test_routes.py test. These tests are marked
"init" so that github actions can run them before
the other tests. This saves time.
This is the most basic set of tests.
"""


def test_flask_initiates(assess_test_client, mock_get_funds):
    """
    GIVEN Our Flask Application
    WHEN the '/' page (index) is requested (GET)
    THEN check that the get response is successful.
    If this test succeeds then our flask application
    is AT LEAST up and running without errors.
    """
    assess_test_client.set_cookie(
        "fsd_user_token",
        "",
    )
    response = assess_test_client.get("/", follow_redirects=True)
    assert response.status_code == 200


def testHealthcheckRoute(assess_test_client, mock_get_funds):
    result = assess_test_client.get("/healthcheck")
    assert result.status_code == 200, "Unexpected status code"
    assert {"check_flask_running": "OK"} in result.json["checks"]
