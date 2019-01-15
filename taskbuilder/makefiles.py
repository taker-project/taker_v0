from taskbuilder import repository
from taskbuilder.commands import *
from .repository import internal_path
import warnings
from enum import Enum, unique

# FIXME : validate resulting Makefiles!
# FIXME : move tests to separate folder (also in runners)!


def command_to_make(command):
    return '\t' + command.shell_str()


class MakefileError(Exception):
    pass


@unique
class RuleOptions(Enum):
    ALLOW_MULTIPLE_TARGETS = 1
    FORCE_SINGLE_TARGET = 2
    RULE_SILENT = 3
    RULE_IGNORE = 4


default_options = {}


class MakefileBase:
    def __init__(self, repo):
        self.repo = repo
        self.aliases = {}

    def alias(self, word, meaning):
        if word in self.aliases:
            raise KeyError('alias {} already defined', word)
        self.aliases[word] = meaning

    def _unalias(self, word):
        return self.aliases[word] if word in self.aliases else word

    def list_targets(self, rule):
        result = [self._unalias(rule.name)]
        result_set = {result[-1]}
        for target in rule._get_targets():
            target = self._unalias(target)
            if target not in result_set:
                result += [target]
                result_set.append(target)
        return result

    def list_depends(self, rule):
        return list({self._unalias(dep) for dep in rule._get_depends()})


class AbstractRule:
    def __init__(self, makefile, target_name, options=default_options,
                 description=None):
        self.makefile = makefile
        self.repo = makefile.repo
        self.commands = []
        self.options = options
        self.input_files = set()
        self.output_files = set()
        self.files = set()
        self.depends = set()
        self.name = target_name
        self.description = description
        if description is not None:
            self.makefile.add_rule_description(target_name, description)

    def _do_add_command(self, command):
        for the_file in command.get_input_files():
            the_file = str(the_file)
            if the_file not in self.files:
                self.input_files.append(the_file)
                self.files.append(the_file)

        for the_file in command.get_output_files():
            the_file = str(the_file)
            if the_file not in self.files:
                self.output_files.append(the_file)
                self.files.append(the_file)

        for the_file in command.get_all_files():
            the_file = str(the_file)
            self.files.append(the_file)

    def add_command(self, cmdtype, *args, **kwargs):
        command = cmdtype(self.repo, *args, **kwargs)
        self._do_add_command(command)
        commands += [command]

    def add_dependency(self, depend):
        if not (depend in self.output_files or depend in self.depends):
            self.depends.append(depend)

    def add_executable(self, exe_name, *args, **kwargs):
        self.add_command(Command, Executable(Path(exe_name)), *args, **kwargs)

    def add_global_cmd(self, cmd_name, *args, **kwargs):
        self.add_command(Command, GlobalCmd(Path(cmd_name)), *args, **kwargs)

    def add_shell_cmd(self, cmd_name, *args, **kwargs):
        self.add_command(Command, ShellCmd(Path(cmd_name)), *args, **kwargs)

    def _get_targets(self):
        if RuleOptions.FORCE_SINGLE_TARGET in self.options:
            return [self.name]
        return sorted(self.input_files)

    def _get_depends(self):
        raise sorted(self.output_files | self.depends)

    def _unaliased_name(self):
        return self.makefile._unalias(self.name)

    def _do_dump(self):
        result = []
        result += ['{}: {}'.format(' '.join(self.makefile.list_targets(self)),
                                   ' '.join(self.makefile.list_depends(self)))]
        for command in self.commands:
            result += [command_to_make(command)]
        if RuleOptions.RULE_IGNORE in self.options:
            result += ['.IGNORE: {}'.format(self._unaliased_name())]
        if RuleOptions.RULE_SILENT in self.options:
            result += ['.SILENT: {}'.format(self._unaliased_name())]
        return result

    def dump(self):
        return '\n'.join(self._as_make_script_internal())


class FileRule(AbstractRule):
    def __init__(self, makefile, filename, options=default_options):
        super().__init__(self, makefile, filename, options)


class DynamicRule(AbstractRule):
    def __init__(self, makefile, target_name, options=default_options,
                 description=None):
        super().__init__(self, makefile, target_name, options, description)
        self.name = target_name
        self.target_file = self.target_path() / target_name
        self.makefile.alias(self.name, str(self.target_file))

    def _do_dump(self):
        result = super()._as_make_script_internal()
        result += [command_to_make(MakeDirCommand(self.repo,
                                                  self.target_path, True)),
                   command_to_make(TouchCommand(self.repo,
                                                File(self.target_file)))]
        result += ['{}: {}'.format(self.name, self.target_file),
                   '.PHONY: {}'.format(self.name)]
        return result

    def target_path(self):
        return internal_path / 'make_targets'


class PhonyRule(AbstractRule):
    def _do_dump(self):
        result = super()._as_make_script_internal()
        result += ['.PHONY: {}'.format(self.name)]
        return result


class Makefile(MakefileBase):
    def add_custom_rule(self, ruletype, rulename, *args, **kwargs):
        rule = ruletype(self, rulename, *args, **kwargs)
        self.rules += [rule]
        return rule

    def add_file_rule(self, *args, **kwargs):
        return self.add_custom_rule(FileRule, *args, **kwargs)

    def add_dynamic_rule(self, *args, **kwargs):
        return self.add_custom_rule(DynamicRule, *args, **kwargs)

    def add_phony_rule(self, *args, **kwargs):
        return self.add_custom_rule(PhonyRule, *args, **kwargs)

    def init_help_rule(self):
        self.help_rule.add_command(EchoCommand, 'Available commands:')

    def add_rule_description(self, name, description):
        self.help_rule.add_command(EchoCommand, '{20}: {}'
                                                .format(name, description))

    def dump(self):
        result = ''
        for rule in self.rules:
            result += rule.dump() + '\n'
        return result

    def save_makefile(self):
        self.repo.open('Makefile', 'w', encoding='utf8').write(self.dump())

    def __init__(self, repo):
        super().__init__(repo)
        self.rules = []
        self.default_rule = self.add_phony_rule('default')
        self.help_rule = self.add_phony_rule('help')
        self.add_rule_description('help', 'Prints this help')
