# coding=utf-8

import os
import sys

if sys.platform.startswith('darwin'):
    from setuptools import setup

    package_info = {}
    exec(open(os.path.join(os.environ['INSPIGTOR_ROOT_DIR'],'src','inspigtor','__pkginfo__.py')).read(), {}, package_info)
    version = package_info['__version__']

    APP = [os.path.join(os.environ['INSPIGTOR_ROOT_DIR'],'src','inspigtor','scripts','run_inspigtor.py')]

    PLIST = {
        u'CFBundleName': u'inspigtor',
        u'CFBundleShortVersionString': version,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'inspigtor-'+version,
        u'LSApplicationCategoryType': u'public.app-category.science'
    }
    OPTIONS = {
        'argv_emulation': False,
        'iconfile': os.path.join(os.environ['INSPIGTOR_ROOT_DIR'],'src','inspigtor','icons','icon.png'),
        'matplotlib_backends': '-',
        'optimize': '1',
        'plist': PLIST,
        'bdist_base': os.path.join(os.environ['INSPIGTOR_ROOT_DIR'],'build'),
        'dist_dir': os.path.join(os.environ['INSPIGTOR_ROOT_DIR'],'dist'),
        'graph': False,
        'xref': False,
        'packages' : ['inspigtor','matplotlib','pandas','scipy','scikit_posthocs','numpy']
    }

    setup(
        name='inspigtor',
        app=APP,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )
else:
    print('No build_app implementation for your system.')
