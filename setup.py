# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.2.1'

DESCRIPTION = """
Toxicjasmine: Nothing interresting here.
""".strip()


setup(name='toxicjasmine',
      version=VERSION,
      author='Juca Crispim',
      author_email='juca@poraodojuca.net',
      url='',
      description=DESCRIPTION,
      long_description=DESCRIPTION,
      packages=find_packages(exclude=['tests', 'tests.*']),
      license='GPL',
      include_package_data=True,
      install_requires=['jasmine==3.5.0', 'jasmine-core==3.5.0',
                        'Jinja2==2.10.3', 'markupsafe==2.0.1'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: No Input/Output (Daemon)',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
      ],
      entry_points={
          'console_scripts': [
              'toxicjasmine=toxicjasmine:begin',
          ]
      },
      test_suite='tests',
      provides=['toxicjasmine'],)
