import os
import subprocess


ROOT = subprocess.check_output([
    'git', 'rev-parse', '--show-toplevel']).decode('ascii').strip()

VERSION_FILE = os.path.join(ROOT, 'cosmic_ray', 'version.py')


def git(*args):
    subprocess.check_call(('git',) + args)


def tags():
    result = [t.decode('ascii') for t in subprocess.check_output([
        'git', 'tag'
    ]).split(b"\n")]
    assert len(set(result)) == len(result)
    return set(result)


def create_tag_and_push(version):
    assert version not in tags()
    git('config', 'user.name', 'Travis CI on behalf of Austin Bingham')
    git('config', 'user.email', 'austin@sixty-north.com')
    git('config', 'core.sshCommand', 'ssh -i deploy_key')
    git(
        'remote', 'add', 'ssh-origin',
        'git@github.com:sixty-north/cosmic-ray.git'
    )
    git('tag', version)

    subprocess.check_call([
        'ssh-agent', 'sh', '-c',
        'chmod 0600 deploy_key && ' +
        'ssh-add deploy_key && ' +
        # 'git push ssh-origin HEAD:master &&'
        'git push ssh-origin --tags'
    ])


def read_version(version_file):
    vars = {}
    with open(version_file) as f:
        exec(f.read(), {}, vars)
    return (vars['__version__'], vars['__version_info__'])


if __name__ == '__main__':
    version, version_info = read_version(VERSION_FILE)
    create_tag_and_push(version)
