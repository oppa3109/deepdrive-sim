from __future__ import print_function

import argparse
import os
from subprocess import Popen, PIPE
from pathlib import Path

import config
import sys

DIR = os.path.dirname(os.path.realpath(__file__))


def run_command(cmd, cwd=None, env=None):
    print('running %s' % cmd)
    if not isinstance(cmd, list):
        cmd = cmd.split()
    cmd = filter(None, cmd)  # filter out empty items
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=cwd, env=env)
    result, err = p.communicate()
    if not isinstance(result, str):
        result = ''.join(map(chr, result))
    result = result.strip()
    print(result)
    if p.returncode != 0:
        if not isinstance(err, str):
            err = ''.join(map(chr, err))
        err = err.strip()
        raise RuntimeError(' '.join(cmd) + ' finished with error ' + err)
    return result


def main(build_type):
    unreal_root = str(Path(DIR).parent.parent.parent.parent.parent)
    print('Unreal root %s' % unreal_root)
    env = os.environ.copy()
    py = sys.executable
    get_package_version_path = os.path.join(unreal_root, 'Packaging', 'get_package_version.py')
    env['DEEPDRIVE_VERSION'] = run_command('%s %s' % (py, get_package_version_path))
    env['DEEPDRIVE_BRANCH'] = (env.get('TRAVIS_BRANCH') or env.get('APPVEYOR_REPO_BRANCH') or
                               run_command(['git', '-C', unreal_root, 'rev-parse', '--abbrev-ref', 'HEAD']))
    print('DEEPDRIVE_VERSION is %s' % env['DEEPDRIVE_VERSION'])
    ext_root = os.path.dirname(DIR)
    print('PYPY_USERNAME is %s' % env.get('PYPI_USERNAME'))
    if build_type == 'dev':
        run_command('%s -m pip uninstall --yes '    % py + config.PACKAGE_NAME, env=env, cwd=ext_root)
        try:
            run_command('pip uninstall --yes ' + config.PACKAGE_NAME, env=env, cwd=ext_root)
        except Exception as e:
            print('Best effort uninstall of external deepdrive package failed, error was: %s' % str(e))
        try:
            run_command('%s -m pip install -e . --upgrade --force-reinstall --ignore-installed --no-deps' % py,
                    env=env, cwd=ext_root)
        except Exception as e:
            raise Exception('Error building, is the module imported into a live python process?', e)

    elif build_type == 'win_bdist':
        print(run_command('%s -u setup.py bdist_wheel' % py, env=env, cwd=ext_root))
        if env['DEEPDRIVE_BRANCH'] == 'release':
            scripts_dir = os.path.join(env['PYTHON'], 'Scripts')
            print('DEBUG scripts dir %s' % list(os.listdir(scripts_dir)))
            for name in os.listdir(os.path.join(ext_root, 'dist')):
                if env['DEEPDRIVE_VERSION'] in name and name.endswith(".whl"):
                    twine = os.path.join(scripts_dir, 'twine')
                    run_command([twine, 'upload', os.path.join(ext_root, 'dist', name), '-u', env['PYPI_USERNAME'],
                                 '-p', env['PYPI_PASSWORD']], env=env, cwd=ext_root)
    elif build_type == 'linux_bdist':
        env['PRE_CMD'] = env.get('PRE_CMD') or ''
        env['DOCKER_IMAGE'] = env.get('DOCKER_IMAGE') or 'quay.io/pypa/manylinux1_x86_64'

        # Build in CentOS to get a portable binary
        run_command(['docker', 'run', '--rm', '-e', '"DEEPDRIVE_SRC_DIR=/io"',
                     '-e', 'PYPI_USERNAME',
                     '-e', 'PYPI_PASSWORD',
                     '-e', 'DEEPDRIVE_BRANCH',
                     '-e', 'DEEPDRIVE_VERSION',
                     '-v', unreal_root + '/Plugins/DeepDrivePlugin/Source:/io',
                     env['DOCKER_IMAGE'],
                     env['PRE_CMD'],
                     '/io/DeepDrivePython/build/build-linux-wheels.sh'], env=env, cwd=os.path.dirname(DIR))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('--type', nargs='?', default='dev', help='Type of build', choices=['dev', 'win_bdist',
                                                                                           'linux_bdist'])
    args = parser.parse_args()
    main(args.type)
