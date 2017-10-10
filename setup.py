import codecs
from setuptools import setup, find_packages

entry_points = {
    "z3c.autoinclude.plugin": [
        'target = nti.contentlibrary',
    ],
}

TESTS_REQUIRE = [
    'fakeredis',
    'nti.testing',
    'zope.testrunner',
    'zope.dottedname',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.contentlibrary_rendering',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI ContentLibrary / Rendering",
    long_description=_read('README.rst'),
    license='Apache',
    keywords='content library rendering',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    url="https://github.com/NextThought/nti.contentlibrary_rendering",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'boto',
        'docutils',
        'isodate',
        'nti.common',
        'nti.contentlibrary',
        'nti.contentrendering',
        'nti.coremetadata',
        'nti.externalization',
        'nti.namedfile',
        'nti.ntiids',
        'nti.publishing',
        'nti.site',
        'nti.traversal',
        'nti.zope_catalog',
        'six',
        'z3c.autoinclude',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.exceptions',
        'zope.interface',
        'zope.location',
        'zope.security'
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)
