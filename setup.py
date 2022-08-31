from setuptools import setup, find_packages

setup(name='mos-compute-py',
      zip_safe=False,
      version='0.2.0',
      author='Fuinn',
      url='https://github.com/Fuinn/mos-compute-py',
      description='MOS Python compute worker',
      license='Elastic License 2.0',
      packages=find_packages(),
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: MacOS',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3.6'])
