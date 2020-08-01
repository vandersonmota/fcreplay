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
      entry_points={
          'console_scripts': [
              'fcreplaychat=fcreplay.chat.main:main',
              'fcreplayget=fcreplay.getreplay:console',
              'fcreplayloop=fcreplay.loop:console',
          ]
      },
      install_requires=[
          'numpy',
          'requests',
          'retrying',
          'internetarchive',
          'opencv-python',
          'beautifulsoup4',
          'sqlalchemy',
          'sqlalchemy-utils',
          'pillow',
          'psycopg2',
          'pyscreenshot',
          'sqlalchemy',
          'google-api-python-client',
          'google-cloud-storage'
      ],
      zip_safe=False)
