from os import path
import shutil
import pytest
from taskbuilder.makefiles import *
from taskbuilder.commands import *
from taskbuilder.repository import TaskRepository

TEST_DIR = path.join('src', 'taskbuilder', 'tests')


def load_answer_file(file_name):
    result = open(path.join(TEST_DIR, file_name), encoding='utf8').read()
    return result.format(shutil.which('mkdir'),
                         shutil.which('touch'),
                         shutil.which('ls'))


@pytest.fixture(scope='function')
def makefile(tmpdir):
    tmpdir = str(tmpdir)
    task_dir = Path(tmpdir) / 'task'
    task_dir.mkdir()
    repo = TaskRepository(task_dir)
    return Makefile(repo)


def test_file_rule1(makefile):
    rule = makefile.add_file_rule('file1.txt')
    rule.add_executable('myexec', args=[OutputFile('file1.txt'),
                                        InputFile('file2.txt')])
    rule.add_executable('myexec2', args=[OutputFile('file1.txt'),
                                         InputFile('file3.txt'),
                                         InputFile('file4.txt')])
    rule.add_command(EchoCommand, 'ok')
    assert rule.get_depends() == {'file2.txt', 'file3.txt', 'file4.txt'}
    assert rule.get_targets() == {'file1.txt'}
    assert rule.dump() == load_answer_file('file_rule1.make')


def test_file_rule2(makefile):
    rule = makefile.add_file_rule('file2.txt')
    rule.add_command(TouchCommand, OutputFile('file3.txt'))
    rule.add_command(TouchCommand, OutputFile('file2.txt'))
    rule.add_shell_cmd('shellcmd', args=[InputFile('a.txt'),
                                         OutputFile('b.txt')])
    rule.add_shell_cmd('shellcmd', args=[InputFile('b.txt')],
                       stdout_redir=OutputFile('c.txt'),
                       flags={CommandFlag.SILENT})

    with pytest.raises(MakefileError):
        rule.dump()
    rule.options = {RuleOptions.RULE_IGNORE}

    assert rule.get_depends() == {'a.txt'}
    assert rule.get_targets() == {'file2.txt', 'b.txt', 'c.txt', 'file3.txt'}
    assert rule.dump() == load_answer_file('file_rule2.make')


def test_dynamic_rule1(makefile):
    rule = makefile.add_dynamic_rule('hello')
    rule.add_depend('world')
    rule.add_command(EchoCommand, 'hello')
    assert rule.dump() == load_answer_file('dyn_rule1.make')


def test_dynamic_rule2(makefile):
    rule = makefile.add_dynamic_rule('rule2',
                                     options={RuleOptions.FORCE_SINGLE_TARGET,
                                              RuleOptions.RULE_SILENT})
    rule.add_executable(Path('..') / 'exe1',
                        stdin_redir=InputFile('file1.txt'))
    rule.add_depend('file1.txt')
    rule.add_depend('file2.txt')
    rule.add_executable('exe2', stdin_redir=InputFile('file2.txt'),
                        flags={CommandFlag.IGNORE})
    rule.add_executable('exe0', stdin_redir=InputFile('file0.txt'),
                        stdout_redir='file4.txt')
    rule.add_command(MakeDirCommand, path.join('hello', 'world'))

    filerule = makefile.add_file_rule('file3.txt')
    filerule.add_depend(rule)

    assert (rule.dump() + '\n' + filerule.dump() ==
            load_answer_file('dyn_rule2.make'))


def test_phony_rule(makefile):
    rule = makefile.add_phony_rule('doit', options={RuleOptions.RULE_IGNORE})
    rule.add_shell_cmd('ls', work_dir='..', stdout_redir=File('log.txt'))
    assert rule.dump() == load_answer_file('phony_rule.make')


def test_makefile(makefile):
    descr1 = makefile.add_phony_rule('descr1',
                                     description='rule 1 with description')
    descr1.add_depend('descr2')
    descr1.add_command(EchoCommand, 'here')

    descr2 = makefile.add_dynamic_rule('descr2',
                                       description='rule 2 with description')
    descr2.add_command(EchoCommand, 'here')

    nodescr1 = makefile.add_phony_rule('nodescr1')
    nodescr1.add_executable('exe1', args=[InputFile('file1.txt')])
    nodescr1.add_global_cmd('ls', stderr_redir=NullFile())
    nodescr1.add_depend('descr1')
    nodescr1.add_depend('descr2')

    makefile.add_dynamic_rule('nodescr2')

    makefile.default_rule.add_shell_cmd('true')

    assert makefile.dump() == load_answer_file('all.make')

    makefile.save()
    assert makefile.repo.open('Makefile', 'r').read() == makefile.dump()
