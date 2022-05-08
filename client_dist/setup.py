from setuptools import setup, find_packages


setup(name='bread_messenger_client',
      version='0.2',
      description='This is my study project. Fresh, raw and uncooked '
                  'like a loaf of bread made for the first time. Client.',
      author='LtBread',
      author_email='primebox21@gmail.com',
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex'],
      scripts=['client/client_run']
      )
