import codecs
from setuptools import setup, find_packages

entry_points = {
    "z3c.autoinclude.plugin": [
        'target = nti.contentlibrary',
    ],
}

TESTS_REQUIRE = [
    'fakeredis',
    'fudge',
    'nti.testing',
    'zope.dottedname',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.contentlibrary_rendering',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI ContentLibrary Rendering",
    long_description=(
        _read('README.rst')
        + '\n\n'
        + _read("CHANGES.rst")
    ),
    license='Apache',
    keywords='content library rendering',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
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
        'BTrees',
        'docutils',
        'isodate',
        'lxml',
        'nti.asynchronous',
        'nti.base',
        'nti.common',
        'nti.containers',
        'nti.contentlibrary',
        'nti.contentrendering',
        'nti.coremetadata',
        'nti.dublincore',
        'nti.externalization',
        'nti.namedfile',
        'nti.ntiids',
        'nti.plasTeX',
        'nti.property',
        'nti.publishing',
        'nti.recorder',
        'nti.schema',
        'nti.site',
        'nti.traversal',
        'nti.zodb',
        'nti.zope_catalog',
        'Pillow',
        'Pygments',
        'simplejson',
        'six',
        'transaction',
        'z3c.autoinclude',
        'zc.intid',
        'zope.annotation',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.container',
        'zope.event',
        'zope.exceptions',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.location',
        'zope.mimetype',
        'zope.proxy',
        'zope.schema',
        'zope.security',
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
