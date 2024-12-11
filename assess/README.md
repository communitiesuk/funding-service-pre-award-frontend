# Funding Service Design - Assessment Frontend

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![CodeQL](https://github.com/communitiesuk/funding-service-design-assessment/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/communitiesuk/funding-service-design-assessment/actions/workflows/codeql-analysis.yml)

This service provides the frontend for the Access Funding Assessment tool.

[Developer setup guide](https://github.com/communitiesuk/funding-service-design-workflows/blob/main/readmes/python-repos-setup.md)

This service depends on the following:
- [Fund store](https://github.com/communitiesuk/funding-service-design-fund-store)
- [Assessment Store](https://github.com/communitiesuk/funding-service-design-assessment-store)
- [Application Store](https://github.com/communitiesuk/funding-service-design-application-store)
- [Account Store](https://github.com/communitiesuk/funding-service-design-account-store)
- [Authenticator](https://github.com/communitiesuk/funding-service-design-authenticator)

# Styles
During development if you need to copy styles from `app/static/src/styles` to the `dist` dir, you can do this by running

    invoke copy-styles

This uses `invoke` and the tasks defined in `tasks.py` to just copy the contents of the source styles directory to dist, saving the time to reinstall the whole govuk bundle by running the full build as above.

# Local Authentication
The assessment app protects different parts of functionality by interrogating the roles of the logged in user. In order to test this locally where we don't have SSO available, a debug user is available. This bypassess login and puts the required information in the session to allow you to appear logged in when running locally. To enable this:
* You must be running with `FLASK_ENV=development` (the default for `flask run` or the docker runner)
* Update [DevelopmentConfig](../config/envs/development.py) so that `DEBUG_USER_ON=True`
* Supply the desired role for the debug user using environment variable `DEBUG_USER_ROLE`. eg. `DEBUG_USER_ROLE=ASSESSOR`
* Run the app and navigate to /assess/fund_dashboard/, you will see the logged in view and be able to comment, score, flag etc.
* When running locally with the debug user enabled, you will also see a yellow box in the top right hand corner of all pages to state which user you are using and their role.

## Troubleshooting
- If despite setting up the development user above you still see a 'you do not have the right roles' message when accessing the assessment frontend locally, try in an incognito window. For example if you have outlook on the web open in one tab and navigate to local assessment in another, assessment sees your outlook session, which doesn't contain any FSD roles, and will use that. Using incognito will fix this.
