from distutils.core import setup

setup(name='curbformation',
      version='0.2',
      scripts=[
          'bin/cf'
      ],
      url='https://github.com/ridecharge/curbformation',
      packages=['cf'],
      install_requires=['boto>=2.34.0','awscli>=1.7.5', 'nose>=1.3.4', 'coverage>=3.7.1']
)
