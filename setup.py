from setuptools import setup
from pathlib import Path
import re

project_name = 'AutoBackupAJM'


def get_long_description():
    this_dir = Path(__file__).parent
    readme_path = this_dir / "README.md"
    if readme_path.is_file():
        long_description = (this_dir / "README.md").read_text()
    else:
        long_description = 'allows automated backup on a chosen schedule'
    return long_description


def get_property(prop, project):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/_version.py').read())
    return result.group(1)


setup(
    name=project_name,
    version=get_property('__version__', project_name),
    packages=['AutoBackupAJM', 'AutoBackupAJM.Hasher'],
    url='https://github.com/amcsparron2793-Water/AutoBackupAJM',
    download_url=f'https://github.com/amcsparron2793-Water/AutoBackupAJM/archive/refs/tags/{get_property("__version__", project_name)}.tar.gz',
    keywords=[],
    install_requires=["questionary", 'EasyLoggerAJM',"MultiHasherMatchAJM", 'tqdm'],
    license='MIT License',
    author='Amcsparron',
    author_email='amcsparron@albanyny.gov',
    description='allows automated backup on a chosen schedule',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    # this is for pypi categories etc
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',      # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        'Programming Language :: Python :: 3',      # Specify which python versions that you want to support
    ]
)
