from enum import Enum, unique
from pathlib import Path
from .commands import Executable, GlobalCmd, ShellCmd, File, Command
from .commands import MakeDirCommand, EchoCommand, TouchCommand
from .repository import INTERNAL_PATH


def command_to_make(command):
    return '\t' + command.shell_str()


class MakefileError(Exception):
    pass


@unique
class RuleOptions(Enum):
    CHECK_SINGLE_TARGET = 1
    FORCE_SINGLE_TARGET = 2
    RULE_SILENT = 3
    RULE_IGNORE = 4


DEFAULT_OPTIONS = {RuleOptions.CHECK_SINGLE_TARGET}


class MakefileBase:
    def __init__(self, repo):
        self.repo = repo
        self.aliases = {}

    def alias(self, word, meaning):
        if word in self.aliases:
            raise KeyError('alias {} already defined'.format(word))
        self.aliases[word] = meaning

    def unalias(self, word):
        return self.aliases[word] if word in self.aliases else word

    def list_targets(self, rule):
        result = [self.unalias(rule.name)]
        for target in sorted(rule.get_targets()):
            target = self.unalias(target)
            if target not in (result[0], result[-1]):
                result += [target]
        return result

    def list_depends(self, rule):
        return sorted({self.unalias(dep) for dep in rule.get_depends()})


class RuleBase:
    def __init__(self, makefile, target_name, description=None,
                 options=DEFAULT_OPTIONS):
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
        for the_file in command.get_output_files():
            the_file = str(the_file)
            if the_file not in self.files:
                self.output_files.add(the_file)
                self.files.add(the_file)

        for the_file in command.get_input_files():
            the_file = str(the_file)
            if the_file not in self.files:
                self.input_files.add(the_file)
                self.files.add(the_file)

        for the_file in command.get_all_files():
            the_file = str(the_file)
            self.files.add(the_file)

    def add_command(self, cmdtype, *args, **kwargs):
        command = cmdtype(self.repo, *args, **kwargs)
        self._do_add_command(command)
        self.commands += [command]

    def add_depend(self, depend):
        if not (depend in self.input_files or depend in self.depends):
            self.depends.add(depend)

    def add_executable(self, exe_name, *args, **kwargs):
        self.add_command(Command, Executable(Path(exe_name)), *args, **kwargs)

    def add_global_cmd(self, cmd_name, *args, **kwargs):
        self.add_command(Command, GlobalCmd(Path(cmd_name)), *args, **kwargs)

    def add_shell_cmd(self, cmd_name, *args, **kwargs):
        self.add_command(Command, ShellCmd(Path(cmd_name)), *args, **kwargs)

    def get_targets(self):
        if RuleOptions.FORCE_SINGLE_TARGET in self.options:
            return {self.name}
        return self.output_files

    def get_depends(self):
        return self.input_files | self.depends

    def _unaliased_name(self):
        return self.makefile.unalias(self.name)

    def _do_dump(self):
        result = []
        header = '{}: {}'.format(' '.join(self.makefile.list_targets(self)),
                                 ' '.join(self.makefile.list_depends(self)))
        result += [header.rstrip()]
        for command in self.commands:
            result += [command_to_make(command)]
        return result

    def _do_end_dump(self):
        result = []
        if RuleOptions.RULE_IGNORE in self.options:
            result += ['.IGNORE: {}'.format(self._unaliased_name())]
        if RuleOptions.RULE_SILENT in self.options:
            result += ['.SILENT: {}'.format(self._unaliased_name())]
        return result

    def validate(self):
        if (RuleOptions.CHECK_SINGLE_TARGET in self.options and
                len(self.makefile.list_targets(self)) != 1):
            raise MakefileError('expected one target, found many')

    def dump(self):
        self.validate()
        return '\n'.join(self._do_dump() + self._do_end_dump()) + '\n'


class FileRule(RuleBase):
    def __init__(self, makefile, filename, options=DEFAULT_OPTIONS):
        super().__init__(makefile, filename, options=options)


class DynamicRule(RuleBase):
    def __init__(self, makefile, target_name, description=None,
                 options=DEFAULT_OPTIONS):
        super().__init__(makefile, target_name, description, options)
        self.name = target_name
        self.target_file = self.target_path() / target_name
        self.makefile.alias(self.name, str(self.target_file))

    def _do_dump(self):
        result = super()._do_dump()
        result += [command_to_make(MakeDirCommand(self.repo,
                                                  self.target_path(), True)),
                   command_to_make(TouchCommand(self.repo,
                                                File(self.target_file)))]
        return result

    def _do_end_dump(self):
        result = super()._do_end_dump()
        result += ['{}: {}'.format(self.name, self.target_file),
                   '.PHONY: {}'.format(self.name)]
        return result

    @staticmethod
    def target_path():
        return INTERNAL_PATH / 'make_targets'


class PhonyRule(RuleBase):
    def _do_end_dump(self):
        result = super()._do_end_dump()
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

    def __init_help_rule(self):
        self.help_rule.add_command(EchoCommand, 'Available commands:')

    def add_rule_description(self, name, description):
        self.help_rule.add_command(EchoCommand,
                                   '{:>20}: {}'.format(name, description))

    def dump(self):
        return '\n'.join((rule.dump() for rule in self.rules))

    def save_makefile(self):
        self.repo.open('Makefile', 'w').write(self.dump())

    def __init__(self, repo):
        super().__init__(repo)
        self.rules = []
        self.default_rule = self.add_phony_rule('default')
        self.help_rule = self.add_phony_rule('help')
        self.__init_help_rule()
        self.add_rule_description('help', 'Prints this help')
