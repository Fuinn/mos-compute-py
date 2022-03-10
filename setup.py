from setuptools import setup, find_packages

setup(name='mos-compute',
      zip_safe=False,
      version='0.1.0',
      author='Fuinn',
      url='https://github.com/Fuinn/mos-compute',
      description='MOS compute',
      license='Apache License, Version 2.0',
      packages=find_packages(),
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: MacOS',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3.6'])
