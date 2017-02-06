import codecs
from setuptools import setup, find_packages

entry_points = {
    "z3c.autoinclude.plugin": [
        'target = nti.contentlibrary',
    ],
    'console_scripts': [
        "nti_library_renderer = nti.contentlibrary_rendering.scripts.renderer:main",
    ]
}

TESTS_REQUIRE = [
    'fudge',
    'nose2[coverage_plugin]',
    'nti.testing',
    'pyhamcrest',
    'z3c.baseregistry',
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
        'nti.async',
        'nti.contentlibrary',
        'nti.contentrendering',
        'nti.coremetadata',
        'nti.externalization',
        'nti.ntiids',
        'z3c.autoinclude',
        'zc.blist',
        'zope.component',
        'zope.interface',
        'zope.location',
        'zope.security',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
    },
    entry_points=entry_points,
)
