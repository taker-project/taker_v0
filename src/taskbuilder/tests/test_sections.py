from pathlib import Path
from taskbuilder import SectionManager
from ...pytest_fixtures import *


def test_sections(repo_manager):
    config1 = Path('root.take')
    config2 = Path('my') / 'good' / 'config.take'
    config3 = Path('_') / 'conf3.take'
    config1_abs = repo_manager.repo.abspath(config1)
    config2_abs = repo_manager.repo.abspath(config2)
    config3_abs = repo_manager.repo.abspath(config3)
    repo_manager.repo.abspath(config2).parent.mkdir(parents=True)
    repo_manager.repo.abspath(config3).parent.mkdir(parents=True)

    repo_manager.repo.open(config1, 'w').write('''\
[section1]
a = 3
b = 5
[section2]
a = 4
# comment
d = 7
''')

    repo_manager.repo.open(config2, 'w').write('''\
[.]
f1 = "hello"
[1]
_ = '42'
[2]
__ = '33'
''')

    repo_manager.repo.open(config3, 'w').write('''\
[something]
field: string = null
[to-delete]
yes = true
[empty]
''')

    section_manager = SectionManager(repo_manager.repo)
    bad_file = section_manager.internal_dir(True) / 'bad_file'
    bad_file.open('w').write('hello\n')
    section_manager.update()
    assert not bad_file.exists()
    section_manager.add_section(config1, 'section1')
    section_manager.add_section(config1, 'nonexistent')
    section_manager.add_section(config1_abs, 'nonexistent2')
    section_manager.add_section(config1_abs, 'section2')
    section_manager.add_section(config1, 'section1')
    section_manager.add_section(config2, '.')
    section_manager.add_section(config2_abs, '2')
    section_manager.add_section(config3, 'something')
    section_manager.add_section(config3, 'to-delete')
    section_manager.add_section(config3, 'empty')
    section_manager.add_section(config3_abs, 'something')
    assert len(section_manager.sections()) == 9
    assert len(section_manager.targets()) == 9
    assert section_manager.sections() == [
        (config3, 'empty'), (config3, 'something'), (config3, 'to-delete'),
        (config2, '.'), (config2, '2'), (config1, 'nonexistent'),
        (config1, 'nonexistent2'), (config1, 'section1'),
        (config1, 'section2')]
    section_manager.update()
    assert len(list(section_manager.internal_dir(True).iterdir())) == 7

    repo_manager.repo.open(config3, 'w').write('''\
[something]
field: string = null
[empty]
''')
    section_manager.update()

    assert len(list(section_manager.internal_dir(True).iterdir())) == 6

    config3_abs.unlink()
    section_manager.update()
    assert len(list(section_manager.internal_dir(True).iterdir())) == 4

    hash_filename = section_manager.target_file(config1, 'section2', True)
    old_hash = hash_filename.open().read()

    section_manager.update()
    assert hash_filename.open().read() == old_hash

    repo_manager.repo.open(config1, 'w').write('''\
[section1]
a = 3
b = 5
[section2]
a = 4
d: int = 7
''')
    section_manager.update()
    assert hash_filename.open().read() == old_hash

    repo_manager.repo.open(config1, 'w').write('''\
[section1]
a = 3
b = 5
[section2]
a = 4
d: int = 7
e = 42
''')
    section_manager.update()
    assert hash_filename.open().read() != old_hash

    repo_manager.repo.open(config1, 'w').write('''\
[section1]
a = 3
b = 5
[section2]
d = 7
a = 4
''')
    section_manager.update()
    assert hash_filename.open().read() == old_hash
