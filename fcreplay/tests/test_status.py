import pytest

from fcreplay.status import status as main_status
from fcreplay.site.status import Status as SiteStatus


def test_valid_site_status():
    valid_status = True
    for status in SiteStatus().status_description:
        try:
            getattr(main_status, status)
        except AttributeError:
            valid_status = False

    assert valid_status, "Website status contains invalid status"


def test_valid_main_status():
    valid_status = True
    for status in main_status.__dict__:
        if str(status).startswith('__'):
            continue
        try:
            SiteStatus().status_description[str(status)]
        except KeyError:
            valid_status = False
    
    assert valid_status, "Site status missing a status code"
