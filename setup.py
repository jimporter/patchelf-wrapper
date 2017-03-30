import errno
import hashlib
import os
import re
import shutil
import subprocess
import tarfile
from contextlib import contextmanager
from distutils.core import setup, Command
from distutils import log
from distutils.command.build import build as BuildCommand
from distutils.command.install import install as OrigInstallCommand

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

version = '1.0.3'


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        try:
            os.makedirs(dirname, mode)
        except OSError as e:
            if ( not exist_ok or e.errno != errno.EEXIST or
                 not os.path.isdir(dirname) ):
                raise

    os.chdir(dirname)
    yield
    os.chdir(old)


class CheckPatchelfCommand(Command):
    description = 'check for the existence of patchelf on the system'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def sha256sum(filename, blocksize=65536):
        sha = hashlib.sha256()
        with open(filename, 'rb') as f:
            for block in iter(lambda: f.read(blocksize), b''):
                sha.update(block)
        return sha.hexdigest()

    def run(self):
        try:
            output = subprocess.check_output(
                ['which', 'patchelf'], universal_newlines=True
            )
            self.announce('Found patchelf at {}'.format(output.strip()),
                          log.INFO)
            self.found_patchelf = True
        except:
            self.announce('patchelf not found', log.INFO)
            self.found_patchelf = False


class FetchPatchelfCommand(Command):
    description = 'fetch the source distribution of patchelf'
    user_options = [
        ('download-dir=', 'd', 'download directory (where to save tarball)'),
        ('force', 'f', 'force download'),
    ]

    patchelf_name = 'patchelf-0.9'
    patchelf_url = ('https://nixos.org/releases/patchelf/{0}/{0}.tar.gz'
                    .format(patchelf_name))
    sha256_hash = ('f2aa40a6148cb3b0ca807a1bf836b081' +
                   '793e55ec9e5540a5356d800132be7e0a')

    def initialize_options(self):
        self.download_dir = None
        self.force = False

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'download_dir'),
                                   ('force', 'force'))
        self.set_undefined_options('install', ('force', 'force'))

    @staticmethod
    def sha256sum(filename, blocksize=65536):
        sha = hashlib.sha256()
        with open(filename, 'rb') as f:
            for block in iter(lambda: f.read(blocksize), b''):
                sha.update(block)
        return sha.hexdigest()

    def run(self):
        if not self.force:
            self.run_command('check_patchelf')
            if self.get_finalized_command('check_patchelf').found_patchelf:
                return

        if self.dry_run:
            return

        filename = os.path.basename(self.patchelf_url)
        with pushd(self.download_dir, makedirs=True, exist_ok=True):
            if ( os.path.exists(filename) and
                 self.sha256sum(filename) == self.sha256_hash ):
                self.announce('Using cached {}'.format(filename))
            else:
                self.announce('Downloading {}...'.format(self.patchelf_url),
                              log.INFO)
                urlretrieve(self.patchelf_url, filename)

                if self.sha256sum(filename) != self.sha256_hash:
                    raise RuntimeError(
                        "{} doesn't match checksum".format(filename)
                    )


class BuildPatchelfCommand(Command):
    description = 'build the patchelf binary'
    user_options = [
        ('download-dir=', 'd', 'download directory (where to find tarball)'),
        ('build-dir=', 'b', 'directory for compiled executable'),
        ('force', 'f', 'force building'),
    ]

    def initialize_options(self):
        self.download_dir = None
        self.build_dir = None
        self.force = False

    def finalize_options(self):
        self.set_undefined_options('install', ('force', 'force'))
        self.set_undefined_options('build',
                                   ('build_base', 'download_dir'),
                                   ('build_lib', 'build_dir'),
                                   ('force', 'force'))

    def run(self):
        if not self.force:
            self.run_command('check_patchelf')
            if self.get_finalized_command('check_patchelf').found_patchelf:
                return

        self.run_command('fetch_patchelf')

        if self.dry_run:
            return

        filename = os.path.join(
            self.download_dir,
            os.path.basename(FetchPatchelfCommand.patchelf_url)
        )
        tar = tarfile.open(filename, 'r:gz')

        with pushd(self.build_dir, makedirs=True, exist_ok=True):
            sub = self.get_finalized_command('fetch_patchelf').patchelf_name

            if os.path.exists(sub):
                self.announce('Cleaning {}'.format(sub), log.INFO)
                shutil.rmtree(sub)

            self.announce('Extracting to {}/{}'.format(self.build_dir, sub),
                          log.INFO)
            tar.extractall('.')

            with pushd(sub):
                configure = ['./configure']
                prefix = self.get_finalized_command('install').install_base

                if prefix:
                    configure += ['--prefix', prefix]

                self.announce('Configuring: {}'.format(' '.join(configure)),
                              log.INFO)
                subprocess.check_call(configure)

                self.announce('Building...', log.INFO)
                subprocess.check_call(['make'])


class InstallPatchelfCommand(Command):
    description = 'install the patchelf binary'
    user_options = [
        ('build-dir=', 'b', 'build directory (where to install from)'),
        ('skip-build', None, 'skip the build steps'),
        ('force', 'f', 'force installation (overwrite any existing files)'),
    ]

    def initialize_options(self):
        self.build_dir = None
        self.skip_build = False
        self.force = False
        self.outputs = []

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_lib', 'build_dir'),
                                   ('skip_build', 'skip_build'))
        self.set_undefined_options('install', ('force', 'force'))

    def run(self):
        if not self.force:
            self.run_command('check_patchelf')
            if self.get_finalized_command('check_patchelf').found_patchelf:
                return

        if not self.skip_build:
            self.run_command('build_patchelf')

        if self.dry_run:
            return

        sub = self.get_finalized_command('fetch_patchelf').patchelf_name
        with pushd(os.path.join(self.build_dir, sub), makedirs=True,
                   exist_ok=True):
            subprocess.check_call(['make', 'install'])

            prefix = self.get_finalized_command('install').install_base
        self.outputs = [
            os.path.join(prefix, 'bin', 'patchelf'),
            os.path.join(prefix, 'share', 'doc', 'patchelf', 'README'),
            os.path.join(prefix, 'share', 'man', 'man1', 'patchelf.1')
        ]

    def get_outputs(self):
        return self.outputs


class InstallCommand(OrigInstallCommand):
    """Override the install command with our own version so that setuptools
    can't use *its* version of the install command. This is necessary because
    older versions of setuptools try very hard to install this package as an
    egg, which won't work."""

    sub_commands = OrigInstallCommand.sub_commands + [
        ('install_patchelf', lambda x: True)
    ]

    # Add options used by setuptools so that it thinks everything is ok.
    user_options = OrigInstallCommand.user_options + [
        ('old-and-unmanageable', None,
         'provided for compatibility with setuptools'),
        ('single-version-externally-managed', None,
         'provided for compatibility with setuptools'),
    ]
    boolean_options = OrigInstallCommand.boolean_options + [
        'old-and-unmanageable', 'single-version-externally-managed',
    ]

    def initialize_options(self):
        OrigInstallCommand.initialize_options(self)
        self.old_and_unmanageable = None
        self.single_version_externally_managed = None


custom_cmds = {
    'check_patchelf':   CheckPatchelfCommand,
    'fetch_patchelf':   FetchPatchelfCommand,
    'build_patchelf':   BuildPatchelfCommand,
    'install_patchelf': InstallPatchelfCommand,
    'install':          InstallCommand,
}

BuildCommand.sub_commands.append(('build_patchelf', lambda x: True))

with open('README.md', 'r') as f:
    long_desc = re.sub(r'(^# patchelf-wrapper)\n\n(.+\n)*', r'\1', f.read())

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='patchelf-wrapper',
    version=version,

    description='A wrapper for patchelf',
    long_description=long_desc,
    keywords='patchelf',
    url='https://github.com/jimporter/patchelf-wrapper',

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',

        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    cmdclass=custom_cmds,
)
