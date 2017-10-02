from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name="helga-chess",
    version=version,
    description=('chess in irc'),
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='irc bot chess',
    author='Justin Caratzas',
    author_email='bigjust@lambdaphil.es',
    license='LICENSE',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['helga_chess'],
    zip_safe=True,
    entry_points = dict(
        helga_plugins = [
            'chess = helga_chess:chess_plugin',
        ],
        helga_webhooks=[
            'chess_webhook = helga_chess:chess_board_webhook',
        ]
    ),
    install_requires = (
        'python-chess',
    ),
)
