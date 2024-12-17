from bs4 import BeautifulSoup

from config import Config


def test_404(flask_test_client):
    response = flask_test_client.get("not_found")

    assert response.status_code == 404

    soup = BeautifulSoup(response.data, "html.parser")

    # Find all links in the HTML
    links = soup.find_all("a", href=True)

    # Check if the portal link is present
    assert any(
        link["href"] == Config.SUPPORT_DESK_APPLY for link in links
    ), f"Expected URL {Config.SUPPORT_DESK_APPLY} not found in the links"


def test_500(flask_test_client, mocker):
    mocker.patch.object(
        flask_test_client.application, "dispatch_request", side_effect=Exception("This is a simulated 500 error.")
    )

    response = flask_test_client.get("/service/magic-links/invalid")

    assert response.status_code == 500

    soup = BeautifulSoup(response.data, "html.parser")

    assert soup.find("title").text == "Sorry, there is a problem with the service - Access Funding"
