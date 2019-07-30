from pathlib import Path
import pytest
from ...pytest_fixtures import config_manager
from configs.configs import *
from configs.managers import *


def test_global_manager(config_manager):
    manager.add_default('my', '[q]\nw=2')
    assert manager['my']['q']['w'] == 2


def test_config_manager(tmpdir):
    tmpdir = Path(str(tmpdir))
    sys1_conf = tmpdir / 'sys1'
    sys2_conf = tmpdir / 'sys2'
    user1_conf = tmpdir / 'user1'
    user2_conf = tmpdir / 'user2'

    sys1_conf.mkdir()
    sys2_conf.mkdir()
    user1_conf.mkdir()
    user2_conf.mkdir()

    (sys1_conf / 'test.conf.d').mkdir()
    (sys1_conf / 'test.conf.d' / 'some-dir').mkdir()
    (user2_conf / 'test.conf.d').mkdir()

    (sys1_conf / 'test.conf.d' / '30file').open('w', encoding='utf8').write('''
[conf1]
ok = true
value = -1
[common]
value = -1
''')
    (sys1_conf / 'test.conf.d' / '10file').open('w', encoding='utf8').write('''
[conf1]
value = 0
system = true
''')
    (sys1_conf / 'test.conf').open('w', encoding='utf8').write('''
[common]
value = 0
''')

    (user2_conf / 'test.conf.d' / '42').open('w', encoding='utf8').write('''
[common]
value = 2
system = false
[conf2]
ok = true
''')

    paths = ConfigPaths()
    paths.site_paths = [sys1_conf, sys2_conf]
    paths.user_paths = [user1_conf, user2_conf]

    assert paths.filenames('test') == [sys1_conf / 'test.conf',
                                       sys1_conf / 'test.conf.d' / '10file',
                                       sys1_conf / 'test.conf.d' / '30file',
                                       sys2_conf / 'test.conf',
                                       user1_conf / 'test.conf',
                                       user2_conf / 'test.conf',
                                       user2_conf / 'test.conf.d' / '42']
    assert paths.user_config('test') == user1_conf / 'test.conf'

    paths.init_user('my-conf')
    assert (user1_conf / 'my-conf.conf.d').is_dir()
    assert (user2_conf / 'my-conf.conf.d').is_dir()

    manager = ConfigManager(paths)
    manager.add_default('test', '''
[common]
value=42
default=true
''')
    assert 'test' not in manager
    test_conf = manager['test']
    assert manager['test'] is test_conf
    assert (user1_conf / 'test.conf.d').is_dir()
    assert 'test' in manager

    with (user1_conf / 'test.conf').open('r', encoding='utf8') as file:
        assert file.read() == '''
[common]
value: int = 42
default: bool = true'''

    with pytest.raises(KeyError):
        manager.add_default('test', '')

    test_conf_expected = {
        'common': {
            'value': 2,
            'default': True,
            'system': False
        },
        'conf1': {
            'value': -1,
            'ok': True,
            'system': True
        },
        'conf2': {
            'ok': True
        }
    }
    assert dict(test_conf) == test_conf_expected
    assert test_conf['conf2'] == test_conf_expected['conf2']

    test_conf['unknown']['unknown'] = 42
    assert test_conf['unknown'] == {'unknown': 42}
