import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='python-mailroute',
    version='0.1.0',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    license='LGPL',
    description='Python client for mailroute.net',
    long_description=README,
    url='https://mailroute.com',
    author='Alex Moiseenko',
    author_email='imdagger@yandex.ru',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=[
        'requests',
        'python-dateutil',
    ],
    test_suite='mailroute.tests',
    tests_require=[
        'sure>=1.1.7',
        'HTTPretty',
    ]
)
