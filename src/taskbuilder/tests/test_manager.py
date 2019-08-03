from ...pytest_fixtures import repo_manager, config_manager
from taskbuilder import RepositoryManager, EchoCommand, InputFile, OutputFile


def test_manager(repo_manager):
    new_manager = RepositoryManager(search_dir=repo_manager.task_dir)
    assert new_manager.task_dir == repo_manager.task_dir
    del new_manager

    makefile = repo_manager.makefile
    repo = repo_manager.repo

    testrule = makefile.add_phony_rule('testrule', description='Test rule')
    testrule.add_command(EchoCommand, 'hello world', stdout_redir='file.txt')

    repo_manager.build('testrule')
    assert (repo.open('file.txt', 'r').read()) == 'hello world\n'

    file2_rule = makefile.add_file_rule('file2.txt')
    file2_rule.add_command(EchoCommand, 'then something happened...',
                           stdout_redir=OutputFile('file2.txt'))

    file3_rule = makefile.add_file_rule('file3.txt')
    file3_rule.add_command(EchoCommand, 'we learned to make...',
                           stdout_redir=OutputFile('file3.txt'))

    file4_rule = makefile.add_file_rule('file4.txt')
    file4_rule.add_shell_cmd('cat',
                             args=[InputFile('file2.txt'),
                                   InputFile('file3.txt')],
                             stdout_redir=OutputFile('file4.txt'))

    makefile.all_rule.add_depend(file4_rule)
    repo_manager.build()
    assert ((repo.open('file4.txt', 'r').read()) ==
            'then something happened...\nwe learned to make...\n')
