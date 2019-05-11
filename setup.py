import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from docopt_sh import __version__


class PyTestCommand(TestCommand):
  """ Command to run unit py.test unit tests
  """
  def finalize_options(self):
    TestCommand.finalize_options(self)
    self.test_args = []
    self.test_suite = True

  def run(self):
    import pytest
    rcode = pytest.main(self.test_args)
    sys.exit(rcode)


setup(
  name='docopt-sh',
  packages=find_packages(),
  version=__version__,
  author='Anders Ingemann',
  author_email='anders@ingemann.de',
  description='Bash argument parser',
  license='MIT',
  keywords='option arguments parsing getopt',
  url='https://github.com/andsens/docopt.sh',
  entry_points={
    'console_scripts': [
      'docopt.sh = docopt_sh.__main__:main'
    ]
  },
  long_description=open('README.rst').read(),
  classifiers=[
    'Topic :: Utilities',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'License :: OSI Approved :: MIT License',
  ],
  require=[
    'docopt'
  ],
  tests_require=[
    'pytest',
    'pytest-xdist',
    'pytest-pep8',
  ],
  cmdclass={
    'test': PyTestCommand,
  }
)
