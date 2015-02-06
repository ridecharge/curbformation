from distutils.core import setup

setup(name='curbformation',
      version='0.1',
      scripts=[
          'bin/cf',
          'bin/sync',
          'bin/bootstrap_env'
      ],
      url='https://github.com/ridecharge/curbformation',
      packages=['cf.stacks', 'cf.validation', 'cf'],
      install_requires=['boto>=2.34.0']
)
