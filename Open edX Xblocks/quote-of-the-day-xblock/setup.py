"""Setup for Quote of the day XBlock."""

import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='xblock-quote-of-the-day',
    version='0.1694',
    description='Quote of the day XBlock',   # TODO: write a better description.
    license='UNKNOWN',          # TODO: choose a license: 'AGPL v3' and 'Apache 2.0' are popular.
    packages=[
        'quote_of_the_day',
    ],
    install_requires=[
        'XBlock', 'requests'
    ],
    entry_points={
        'xblock.v1': [
            'quote_of_the_day = quote_of_the_day:QuoteOfTheDayXBlock',
        ]
    },
    package_data=package_data("quote_of_the_day", ["static", "public"]),
)
