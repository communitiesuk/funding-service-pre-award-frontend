# @pytest.mark.mock_parameters(
#     {
#         "fund_short_name": "NSTF",
#         "round_short_name": "TR",
#         "expected_search_params": {
#             "search_term": "",
#             "search_in": "organisation_name,short_id",
#             "funding_type": "ALL",
#             "status": "ALL",
#             "filter_by_tag": "ALL",
#             "local_authority": "ALL",
#             "country": "ALL",
#             "region": "ALL",
#         },
#     }
# )
# @pytest.mark.application_id("resolved_app")
# def test_route_fund_dashboard_NSTF(
#     self,
#     request,
#     flask_test_client,
#     mock_get_funds,
#     mock_get_round,
#     mock_get_fund,
#     mock_get_application_overviews,
#     mock_get_assessment_progress,
#     mock_get_application_metadata,
#     mock_get_active_tags_for_fund_round,
#     mock_get_tag_types,
# ):
#     flask_test_client.set_cookie(
#         "localhost",
#         "fsd_user_token",
#         create_valid_token(fund_specific_claim_map["NSTF"]["ASSESSOR"]),
#     )

#     params = request.node.get_closest_marker("mock_parameters").args[0]

#     fund_short_name = params["fund_short_name"]
#     round_short_name = params["round_short_name"]

#     response = flask_test_client.get(
#         f"/assess/fund_dashboard/{fund_short_name}/{round_short_name}",
#         follow_redirects=True,
#     )
#     assert 200 == response.status_code, "Wrong status code on response"
#     soup = BeautifulSoup(response.data, "html.parser")

#     all_table_headings = str(soup.find_all("th", class_="govuk-table__header"))
#     expected_titles = [
#         "Reference",
#         "Organisation name",
#         "Funding type",
#         "Funding requested",
#         "Status",
#     ]
#     assert all(title in all_table_headings for title in expected_titles)

# @pytest.mark.mock_parameters(
#     {
#         "fund_short_name": "COF",
#         "round_short_name": "TR",
#         "expected_search_params": {
#             "search_term": "",
#             "search_in": "project_name,short_id",
#             "asset_type": "ALL",
#             "status": "ALL",
#             "filter_by_tag": "ALL",
#             "local_authority": "ALL",
#             "country": "ALL",
#             "region": "ALL",
#         },
#     }
# )
# @pytest.mark.application_id("resolved_app")
# def test_route_fund_dashboard_COF(
#     self,
#     request,
#     flask_test_client,
#     mock_get_fund,
#     mock_get_funds,
#     mock_get_round,
#     mock_get_application_overviews,
#     mock_get_assessment_progress,
#     mock_get_active_tags_for_fund_round,
#     mock_get_tag_types,
# ):
#     flask_test_client.set_cookie(
#         "localhost",
#         "fsd_user_token",
#         create_valid_token(fund_specific_claim_map["COF"]["ASSESSOR"]),
#     )

#     params = request.node.get_closest_marker("mock_parameters").args[0]

#     fund_short_name = params["fund_short_name"]
#     round_short_name = params["round_short_name"]

#     response = flask_test_client.get(
#         f"/assess/fund_dashboard/{fund_short_name}/{round_short_name}",
#         follow_redirects=True,
#     )
#     assert 200 == response.status_code, "Wrong status code on response"
#     soup = BeautifulSoup(response.data, "html.parser")
#     assert (
#         soup.title.string == "Team dashboard – Assessment Hub – GOV.UK"
#     ), "Response does not contain expected heading"

#     all_table_headings = str(soup.find_all("th", class_="govuk-table__header"))
#     expected_titles = [
#         "Reference",
#         "Project name",
#         "Asset type",
#         "Funding requested",
#         "Location",
#         "Status",
#     ]
#     assert all(title in all_table_headings for title in expected_titles)

#     all_table_data_elements = str(soup.find_all("td", class_="govuk-table__cell"))
#     project_titles = [
#         "Project In prog and Res",
#         "Project In prog and Stop",
#         "Project Completed Flag and QA",
#     ]
#     assert all(title in all_table_data_elements for title in project_titles)

# @pytest.mark.mock_parameters(
#     {
#         "fund_short_name": "DPIF",
#         "round_short_name": "TR",
#         "expected_search_params": {
#             "search_term": "",
#             "search_in": "organisation_name,short_id",
#             "status": "ALL",
#             "filter_by_tag": "ALL",
#             "publish_datasets": "ALL",
#             "datasets": "ALL",
#             "team_in_place": "ALL",
#         },
#     }
# )
# @pytest.mark.application_id("resolved_app")
# def test_route_fund_dashboard_DPIF(
#     self,
#     request,
#     flask_test_client,
#     mock_get_fund,
#     mock_get_funds,
#     mock_get_round,
#     mock_get_application_overviews,
#     mock_get_assessment_progress,
#     mock_get_active_tags_for_fund_round,
#     mock_get_tag_types,
# ):
#     flask_test_client.set_cookie(
#         "localhost",
#         "fsd_user_token",
#         create_valid_token(fund_specific_claim_map["DPIF"]["ASSESSOR"]),
#     )

#     params = request.node.get_closest_marker("mock_parameters").args[0]

#     fund_short_name = params["fund_short_name"]
#     round_short_name = params["round_short_name"]

#     response = flask_test_client.get(
#         f"/assess/fund_dashboard/{fund_short_name}/{round_short_name}",
#         follow_redirects=True,
#     )
#     assert 200 == response.status_code, "Wrong status code on response"
#     soup = BeautifulSoup(response.data, "html.parser")
#     assert (
#         soup.title.string == "Team dashboard – Assessment Hub – GOV.UK"
#     ), "Response does not contain expected heading"

#     all_table_headings = str(soup.find_all("th", class_="govuk-table__header"))
#     expected_titles = [
#         "Reference",
#         "Organisation Name",
#         "Lead Contact",
#         "Team in place",
#         "Dataset",
#         "Publish datasets",
#         "Tags",
#         "Status",
#     ]
#     assert all(title in all_table_headings for title in expected_titles)

#     all_table_data_elements = str(soup.find_all("td", class_="govuk-table__cell"))
#     project_titles = [
#         "FQAC",
#         "FS",
#         "INP",
#     ]
#     assert all(title in all_table_data_elements for title in project_titles)
