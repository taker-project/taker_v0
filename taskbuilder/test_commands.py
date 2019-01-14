from taskbuilder.commands import *
from taskbuilder.manager import TaskManager
from os import path
import shutil


def test_files():
    infile = InputFile('q.txt')
    outfile = OutputFile('w.txt')
    assert str(infile) == 'q.txt'
    assert str(outfile) == 'w.txt'
    assert InputFile('q.txt') == InputFile('q.txt')
    assert not (InputFile('q.txt') != InputFile('q.txt'))
    assert InputFile('q.txt') != InputFile('w.txt')
    assert not (InputFile('q.txt') == InputFile('w.txt'))
    assert not (File('q.txt') == InputFile('q.txt'))
    assert File('q.txt') != InputFile('q.txt')


def test_commands(tmpdir):
    tmpdir = Path(str(tmpdir))
    task_dir = tmpdir / 'task'
    task_dir.mkdir()
    (task_dir / 'inner').mkdir()

    manager = TaskManager(task_dir)
    manager.init_task()

    command = Command(
        manager,
        Executable('local_exe'),
        args=[File('file.txt'),
              InputFile(path.join(path.pardir, 'input_file.txt')),
              OutputFile(path.join(path.pardir, 'output_file.txt')),
              File(tmpdir / 'file2.txt'),
              AbsoluteFile(Path.home().root),
              'arg1'],
        stdin_redir=InputFile('in_redir.txt'),
        stdout_redir=OutputFile(tmpdir / 'out_redir.txt')
    )

    assert (command.get_input_files() ==
            [InputFile(path.join(path.pardir, 'input_file.txt')),
             InputFile('in_redir.txt')])
    assert (command.get_output_files() ==
            [OutputFile(path.join(path.pardir, 'output_file.txt')),
             OutputFile(path.join(path.pardir, 'out_redir.txt'))])

    assert (command.shell_str() ==
            ' '.join((path.join(path.curdir, 'local_exe'),
                      'file.txt',
                      path.join(path.pardir, 'input_file.txt'),
                      path.join(path.pardir, 'output_file.txt'),
                      path.join(path.pardir, 'file2.txt'),
                      str(Path.home().root),
                      'arg1',
                      '<in_redir.txt',
                      '>' + path.join(path.pardir, 'out_redir.txt'))))

    command = Command(
        manager,
        GlobalCmd('mkdir'),
        work_dir=Path('inner'),
        args=[AbsoluteFile(Path.cwd() / 'new'),
              InputFile('file.txt'),
              OutputFile(path.join('inner', 'file2.txt')),
              InputFile(tmpdir / 'file3.txt')],
        stdout_redir=OutputFile(task_dir / 'inner' / 'file4.txt'),
        stderr_redir=NullFile()
    )

    assert (command.get_input_files() ==
            [InputFile('file.txt'),
             InputFile(path.join(path.pardir, 'file3.txt'))])
    assert (command.get_output_files() ==
            [OutputFile(path.join('inner', 'file2.txt')),
             OutputFile(path.join('inner', 'file4.txt'))])

    assert (command.shell_str() ==
            ' '.join(('cd inner &&',
                      shutil.which('mkdir'),
                      path.abspath(path.join(path.curdir, 'new')),
                      path.join(path.pardir, 'file.txt'),
                      'file2.txt',
                      path.join(path.pardir, path.pardir, 'file3.txt'),
                      '>file4.txt',
                      '2>' + path.devnull)))
