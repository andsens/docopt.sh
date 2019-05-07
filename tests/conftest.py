from .usecases import DocoptUsecaseTestFile


def pytest_collect_file(path, parent):
    if path.basename == "usecases.txt":
        return DocoptUsecaseTestFile(path, parent)
