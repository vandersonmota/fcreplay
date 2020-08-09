from setuptools import setup
import os


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('./fcreplay/data')

setup(name='fcreplay',
      version='0.9',
      description='Fcreplay python code',
      url='http://github.com/glisignoli/fcreplay',
      author='Gino Lisignoli',
      author_email='glisignoli@gmail.com',
      license='GPL3',
      packages=['fcreplay'],
      package_data={'': extra_files},
      entry_points={
          'console_scripts': [
              'fcreplaychat=fcreplay.chat.main:main',
              'fcreplayget=fcreplay.getreplay:console',
              'fcreplayloop=fcreplay.loop:console',
          ]
      },
      install_requires=[
          'beautifulsoup4',
          'debugpy',
          'docopt',
          'google-api-python-client',
          'internetarchive',
          'numpy',
          'opencv-python',
          'pillow',
          'psycopg2',
          'pyscreenshot',
          'requests',
          'retrying',
          'sqlalchemy',
          'sqlalchemy-utils',
      ],
      zip_safe=False)
