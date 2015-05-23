""" Setup file. """
import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()

REQUIREMENTS = [
    'dropbox',
    'psycopg2',
    'pycrypto',
    'pyramid>=1.5',
    'pyramid_beaker',
    'pyramid_duh>=0.1.2',
    'pyramid_jinja2',
    'pyramid_tm',
    'python-dateutil',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
]

TEST_REQUIREMENTS = []

if __name__ == "__main__":
    setup(
        name='stevetags',
        version="develop",
        description='Dropbox assistant',
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Framework :: Pyramid',
            'Private :: Do Not Upload',
        ],
        author='Steven Arcangeli',
        author_email='stevearc@stevearc.com',
        url='',
        platforms='any',
        include_package_data=True,
        zip_safe=False,
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'st-deploy = stevetags:deploy',
            ],
            'paste.app_factory': [
                'main = stevetags:main',
            ],
            'paste.filter_app_factory': [
                'security_headers = stevetags.security:SecurityHeaders',
            ],
        },
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
