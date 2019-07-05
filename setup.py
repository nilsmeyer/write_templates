from setuptools import setup

setup(
    name='write_template',
    author='Nils Meyer',
    author_email='nils@nm.cx',
    description='write out templates from cloud-config userdata',
    version='0.1',
    py_modules=['write_template'],
    install_requires=[
        'Jinja2', 'ruamel.yaml'
    ],
    extras_require={
        'ansible': ['ansible'],
        'kms': ['boto3']
    },
    entry_points='''
        [console_scripts]
        write_template=write_template:cli
    ''',
)
