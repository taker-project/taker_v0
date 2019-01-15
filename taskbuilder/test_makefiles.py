from taskbuilder.makefiles import *
from taskbuilder.commands import *
from taskbuilder.repository import TaskRepository
from os import path
import shutil
import pytest

test_dir = path.join('taskbuilder', 'tests')


def load_answer_file(file_name):
    result = open(path.join(test_dir, file_name), encoding='utf8').read()
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
    f = makefile.add_file_rule('file1.txt')
    f.add_executable('myexec', args=[OutputFile('file1.txt'),
                                     InputFile('file2.txt')])
    f.add_executable('myexec2', args=[OutputFile('file1.txt'),
                                      InputFile('file3.txt'),
                                      InputFile('file4.txt')])
    f.add_command(EchoCommand, 'ok')
    assert f.dump() == load_answer_file('file_rule1.make')


def test_file_rule2(makefile):
    f = makefile.add_file_rule('file2.txt')
    f.add_command(TouchCommand, OutputFile('file3.txt'))
    f.add_command(TouchCommand, OutputFile('file2.txt'))
    f.add_shell_cmd('shellcmd', args=[InputFile('a.txt'), OutputFile('b.txt')])
    f.add_shell_cmd('shellcmd', args=[InputFile('b.txt')],
                    stdout_redir=OutputFile('c.txt'))

    with pytest.raises(MakefileError):
        f.dump()
    f.options = {RuleOptions.RULE_IGNORE}

    assert f.dump() == load_answer_file('file_rule2.make')


def test_dynamic_rule1(makefile):
    f = makefile.add_dynamic_rule('hello')
    f.add_depend('world')
    f.add_command(EchoCommand, 'hello')
    assert f.dump() == load_answer_file('dyn_rule1.make')


def test_dynamic_rule2(makefile):
    f = makefile.add_dynamic_rule('rule2',
                                  options={RuleOptions.FORCE_SINGLE_TARGET,
                                           RuleOptions.RULE_SILENT})
    f.add_executable(Path('..') / 'exe1', stdin_redir=InputFile('file1.txt'))
    f.add_depend('file1.txt')
    f.add_depend('file2.txt')
    f.add_executable('exe2', stdin_redir=InputFile('file2.txt'))
    f.add_executable('exe0', stdin_redir=InputFile('file0.txt'),
                     stdout_redir='file4.txt')
    f.add_command(MakeDirCommand, path.join('hello', 'world'))

    f2 = makefile.add_file_rule('file3.txt')
    f2.add_depend('rule2')

    assert f.dump() + '\n' + f2.dump() == load_answer_file('dyn_rule2.make')


def test_phony_rule(makefile):
    f = makefile.add_phony_rule('doit', options={RuleOptions.RULE_IGNORE})
    f.add_shell_cmd('ls', work_dir='..', stdout_redir=File('log.txt'))
    assert f.dump() == load_answer_file('phony_rule.make')


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

    nodescr2 = makefile.add_dynamic_rule('nodescr2')

    makefile.default_rule.add_shell_cmd('true')

    assert makefile.dump() == load_answer_file('all.make')

    makefile.save_makefile()
    assert makefile.repo.open('Makefile', 'r').read() == makefile.dump()
