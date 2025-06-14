import json
import os

import ee


def pytest_sessionstart(session):
    _init_ee_for_tests()


def _init_ee_for_tests():
    # Use the Github Service Account for CI tests
    if os.environ.get("GITHUB_ACTIONS"):
        key_data = os.environ.get("EE_SERVICE_ACCOUNT")
        project_id = json.loads(key_data).get("project_id")
        credentials = ee.ServiceAccountCredentials(None, key_data=key_data)
    # Use stored persistent credentials for local tests
    else:
        # Project should be parsed from credentials
        project_id = None
        credentials = "persistent"

    ee.Initialize(credentials, project=project_id)
