try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='rpm2cpe',
      packages=['rpm2cpe'],
      version='0.0.2',
      description='Tool to correlate RPM\'s with CVE\'s.',
      author='Kenneth Evensen',
      author_email='kevensen@redhat.com',
      license='GPLv3',
      url='https://github.com/fedoraredteam/rpm2cpe',
      download_url='https://github.com/fedoraredteam/rpm2cpe/archive/0.0.2.zip',
      keywords=['cpe', 'rpm'],
      classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 2.7',
      ],
      scripts=['bin/rpm2cpe'],
      platforms=['Linux'])
