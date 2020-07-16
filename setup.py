from setuptools import setup
setup(name='fcreplay',
      version='0.9',
      description='Fcreplay python code',
      url='http://github.com/glisignoli/fcreplay',
      author='Gino Lisignoli',
      author_email='glisignoli@gmail.com',
      license='GPL3',
      packages=['fcreplay'],
      package_data={'fcreplay': [
          'data/*',
          'data/charnames/*'
      ]},
      entry_points = {
          'console_scripts': [
              'fcreplayloop=fcreplay.loop:console',
              'fcreplayget=fcreplay.get:console',
              'fcreplayplayerget=fcreplay.getplayerreplay:console',
          ]
      },
      install_requires = [
          'numpy',
          'soundmeter',
          'requests',
          'retrying',
          'internetarchive',
          'opencv-python',
          'beautifulsoup4',
          'sqlalchemy',
          'sqlalchemy-utils',
          'psycopg2',
          'sqlalchemy'
      ],
      zip_safe=False)