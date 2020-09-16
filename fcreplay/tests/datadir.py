import os


def datadir(request, filename):
    '''
    Looks for a file in the test_name/ folder

    If the specified file can't be found, then use the 'common' directory
    '''
    testname = request.node.name
    testdir = os.path.splitext(os.environ.get('PYTEST_CURRENT_TEST'))[0]
    commondir = '/'.join(os.path.split(testdir)[:-1]) + '/common'

    if os.path.exists(f"{testdir}/{filename}"):
        return f"{testdir}/{filename}"
    else:
        return f"{commondir}/{filename}"
