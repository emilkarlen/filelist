# -*- coding: utf-8 -*-

from . import program_info


###############################################################################
# DESIGN
# --------------------------------------
# A file is processed by a FileParser:
#
# For each line:
# LineParser             -> [Processor]
# Processor              -> [ResultItem]
# ResultItem             -> str
###############################################################################


import copy
import sys
import os
import argparse
import re
import textwrap
import fnmatch
import stat
import subprocess
import shlex


###############################################################################
# - exit codes -
###############################################################################


EXIT_USAGE = 2
EXIT_INVALID_ARGUMENTS = 3
EXIT_SYNTAX = 4
EXIT_PRE_PROCESSING = 5
EXIT_FILE_DOES_NOT_EXIST = 8 + 0
EXIT_SHELL_COMMAND_EXECUTION_ERROR = 8 + 1
EXIT_TAGS_ERROR = 8 + 2


###############################################################################
# - utilities -
###############################################################################


def in_double_quotes(s: str):
    return "\"" + s + "\""


def in_source_quotes(s: str):
    return "`" + s + "'"


def write_lines(o_stream, lines):
    """Writes a list of lines with an added trailing newline, to a stream."""
    for line in lines:
        o_stream.write(line)
        o_stream.write(os.linesep)


###############################################################################
# - constants -
###############################################################################


# TODO Move this info to some kind of printer / settings.
ERROR_MESSAGE_INDENT_STRING = "  "

DEFAULT_INSTRUCTION_PREFIX = "@"

COMMAND_LINE_ARGUMENT_FOR_STDIN = "-"


###############################################################################
# - matcher utils -
###############################################################################


def constantly_matcher(result: bool):
    def f(x) -> bool:
        return result
    return f


def or_matcher(matchers: list):
    """
    A matcher that must match one of a given list of matchers.
    """
    num_matchers = len(matchers)
    if num_matchers == 0:
        return constantly_matcher(False)
    elif num_matchers == 1:
        return matchers[0]

    def f(x) -> bool:
        for matcher in matchers:
            if matcher(x):
                return True
        return False

    return f


def and_matcher(matchers: list):
    """
    A matcher that must match every one of a given list of matchers.
    """
    num_matchers = len(matchers)
    if num_matchers == 0:
        return constantly_matcher(True)
    elif num_matchers == 1:
        return matchers[0]

    def f(x) -> bool:
        for matcher in matchers:
            if not matcher(x):
                return False
        return True

    return f


def not_matcher(matcher):
    """
    A matcher that negates a matcher.
    """
    return lambda x: not(matcher(x))


###############################################################################
# - parsing utils -
###############################################################################


def parse_tags_list(string: str) -> list:
    return list(filter(lambda s: bool(s),
                       re.split(r"[\s,]+", string)))


###############################################################################
# - argparse -
###############################################################################


class ArgumentParsingException(Exception):
    """
    Indicates an invalid command line - a command line that the
    ArgumentParser cannot parse.
    """
    def __init__(self,
                 argument_parser: argparse.ArgumentParser,
                 error_message: str):
        self.argument_parser = argument_parser
        self.error_message = error_message


def raise_exception_instead_of_exiting_on_error(parser: argparse.ArgumentParser,
                                                arguments: list):
    """
    Corresponds to argparse.ArgumentParser.parse_args.

    But instead of exiting on error, a ArgumentParsingException is raised.
    """
    original_error_handler = argparse.ArgumentParser.error

    def error_handler(the_parser: argparse.ArgumentParser, the_message: str):
        raise ArgumentParsingException(the_parser, the_message)

    try:
        argparse.ArgumentParser.error = error_handler
        return parser.parse_args(arguments)
    finally:
        argparse.ArgumentParser.error = original_error_handler


###############################################################################
# - file positions -
###############################################################################


class SourceLine:
    """Information about a line in a source file."""
    def __init__(self,
                 line_number: int,
                 line_contents: str):
        self.number = line_number
        self.contents = line_contents


class SourceLineInFile:
    """Information about a line in a source file, including file name."""
    def __init__(self,
                 file_name: str,
                 line: SourceLine):
        self.file_name = os.path.normpath(file_name)
        self.line = line

    def err_msg_file_ref(self):
        return " ".join(["File",
                         "\"" + self.file_name + "\",",
                         "line",
                         str(self.line.number)])

    def err_msg_line_contents(self):
        return ERROR_MESSAGE_INDENT_STRING + in_source_quotes(self.line.contents)

    def err_msg_file_ref_with_source_line(self):
        return os.linesep.join([self.err_msg_file_ref(),
                                self.err_msg_line_contents()])


class IncludeFileChain:
    """Chain of files related via inclusions."""
    def __init__(self,
                 files: list):
        self._files = files

    @staticmethod
    def new_for_top_level_file():
        return IncludeFileChain([])

    def new_include(self,
                    source_line: SourceLineInFile):
        new_files = self._files.copy()
        new_files.append(source_line)
        return IncludeFileChain(new_files)

    def from_top_to_bottom(self):
        return self._files


class SourceReference:
    """A reference to a line in a source file, together with inclusion chain."""

    def __init__(self,
                 includes: IncludeFileChain,
                 source_line: SourceLineInFile):
        self.includes = includes
        self.source_line = source_line

    def as_include_file_chain(self):
        return self.includes.new_include(self.source_line)


###############################################################################
# - classes -
###############################################################################


class Tags:
    """
    The file-path tags part of an ResultItemsConstructionEnvironment.
    Each tag is a string.
    Tags stores a list of tags and implements some functionality for
    modifying and querying this list.
    """

    def __init__(self,
                 tags: list,
                 tags_stack: list):
        self._as_froze_set = frozenset(tags)
        self.tags_stack = tags_stack

    @staticmethod
    def new_empty():
        return Tags([], [])

    def frozen_tags(self) -> frozenset:
        return self._as_froze_set

    def stack(self) -> list:
        return self.tags_stack

    def push(self):
        self.tags_stack = [self.frozen_tags()] + self.tags_stack

    def pop(self):
        self.set_frozen_set(self.tags_stack.pop(0))

    def set(self,
            tags: list):
        self.set_frozen_set(frozenset(tags))

    def set_frozen_set(self,
                       tags: frozenset):
        self._as_froze_set = tags

    def add(self,
            tags: list):
        self._as_froze_set = self._as_froze_set.union(tags)

    def remove(self,
               tags):
        self._as_froze_set = self._as_froze_set.difference(tags)

    def clear(self):
        self._as_froze_set = frozenset()


class FileReferenceEnvironment:
    """Environment for making it easy to reference file-paths from the current working directory."""

    def __init__(self,
                 from_curr_dir: str,
                 from_top_level_file: str):
        self.fromCurrDir = from_curr_dir
        self.fromTopLevelFile = from_top_level_file

    @staticmethod
    def for_top_level_file(file_name: str):
        prefix = os.path.dirname(file_name)
        if prefix:
            prefix = prefix + os.sep
        return FileReferenceEnvironment(prefix,
                                        "")

    def new_for_directory(self, name_of_directory):
        if name_of_directory == ".":
            return self
        else:
            return self._new_for_appended_dir(name_of_directory)

    def for_included_file(self,
                          file_name_relative_include_file: str,
                          preserve_current_directory: bool):
        if preserve_current_directory:
            return self
        dir_delta = os.path.dirname(file_name_relative_include_file)
        if not dir_delta:  # file is in same directory
            return copy.copy(self)
        return self._new_for_appended_dir(dir_delta)

    def file_name_relative_current_dir_of_process(self,
                                                  file_name: str) -> str:
        if os.path.isabs(file_name):
            return file_name
        else:
            return self.fromCurrDir + file_name

    def file_name_relative_top_level_source_file(self,
                                                 file_name: str) -> str:
        if os.path.isabs(file_name):
            return file_name
        else:
            return self.fromTopLevelFile + file_name

    def _new_for_appended_dir(self,
                              dir_delta: str):
        if dir_delta[-1] != os.path.sep:
            dir_delta += os.path.sep
        return FileReferenceEnvironment(
            os.path.join(self.fromCurrDir,
                         dir_delta),
            os.path.join(self.fromTopLevelFile,
                         dir_delta))


class SetOperatorConfig:
    def __init__(self,
                 aliases: list,
                 operator):
        self.aliases = aliases
        self.operator = operator

    def get_operator(self,
                     negated: bool):
        if negated:
            return lambda l, r: not(self.operator(l, r))
        else:
            return self.operator


class TagsCondition:
    """
    A condition on the tags associated with a file.
    """

    def __init__(self,
                 operator_function,
                 right_operand: frozenset):
        self._operator_function = operator_function
        self._right_operand = right_operand

    @staticmethod
    def new_for_no_condition():
        return TagsCondition(lambda l, r: True,
                             frozenset())

    def is_satisfied_by(self,
                        tags: frozenset) -> bool:
        """Tests if the given tags satisfies the condition."""
        return self._operator_function(tags, self._right_operand)


class TagsConditionSetup:
    """
    Information about Tag Conditions.
    """

    OPERATORS = {
        "contains-any-of": SetOperatorConfig(["any-of"],
                                             lambda l, r: bool(l.intersection(r))),
        "contains-none-of": SetOperatorConfig(["none-of"],
                                              lambda l, r: l.isdisjoint(r)),
        "proper-subset": SetOperatorConfig([],
                                           lambda l, r: l < r),
        "subset": SetOperatorConfig([],
                                    lambda l, r: l <= r),
        "equals": SetOperatorConfig([],
                                    lambda l, r: l == r),
        "proper-superset": SetOperatorConfig([],
                                             lambda l, r: l > r),
        "superset": SetOperatorConfig([],
                                      lambda l, r: l >= r),
        "unequals": SetOperatorConfig([],
                                      lambda l, r: l != r),
    }

    DEFAULT_OPERATOR_NAME = "contains-any-of"

    def __init__(self):
        self._lookup_dict = dict()
        for key, value in self.OPERATORS.items():
            self._lookup_dict[key] = value
            for alias in value.aliases:
                self._lookup_dict[alias] = value

    def all_operator_names(self) -> iter:
        return self._lookup_dict.keys()

    def lookup(self, operator_name: str) -> SetOperatorConfig:
        return self._lookup_dict[operator_name]

    def condition_for(self,
                      operator_name: str,
                      negate_operator: bool,
                      right_operand: frozenset) -> TagsCondition:
        return TagsCondition(self._lookup_dict[operator_name].get_operator(negate_operator),
                             right_operand)

    @staticmethod
    def for_no_condition():
        return TagsCondition.new_for_no_condition()


class TagsSettingsForInclude:
    """
    Settings for how the INCLUDE instruction should handle tags.
    """
    def __init__(self,
                 do_export: bool,
                 do_import: bool):
        self.do_export = do_export
        self.do_import = do_import


class ResultItemsConstructionEnvironment:
    """
    ResultItemsConstructionEnvironment for executing instructions.
    """

    def __init__(self,
                 dir_env: FileReferenceEnvironment,
                 fail_on_non_existing_file: bool,
                 tags_condition: TagsCondition,
                 tags: Tags):
        self.file_ref_env = dir_env
        self.fail_on_non_existing_file = fail_on_non_existing_file
        self._tags_condition = tags_condition
        self._tags = tags

    def new_for_directory(self, name_of_directory):
        return ResultItemsConstructionEnvironment(
            self.file_ref_env.new_for_directory(name_of_directory),
            self.fail_on_non_existing_file,
            self._tags_condition,
            self._tags)

    def new_for_included_file(self,
                              file_name_relative_include_file: str,
                              preserve_current_directory: bool,
                              tags_settings: TagsSettingsForInclude):
        return ResultItemsConstructionEnvironment(
            self.file_ref_env.for_included_file(file_name_relative_include_file,
                                                preserve_current_directory),
            self.fail_on_non_existing_file,
            self._tags_condition,
            self._tags_for_included_file(tags_settings))

    def _tags_for_included_file(self,
                                tags_settings: TagsSettingsForInclude) -> Tags:
        if not tags_settings.do_export:
            if not tags_settings.do_import:
                return Tags.new_empty()
            else:
                self._tags = Tags.new_empty()
                return self._tags
        else:
            return self._tags if tags_settings.do_import else copy.deepcopy(self._tags)

    def tags(self) -> Tags:
        return self._tags

    def satisfies_tags_filter(self,
                              file_tags: frozenset) -> bool:
        return self._tags_condition.is_satisfied_by(file_tags)

    def current_tags_satisfies_tags_filter(self) -> bool:
        return self.satisfies_tags_filter(self.tags().frozen_tags())


###############################################################################
# - ResultItem:s -
###############################################################################


class TagsRenditionSettings:

    # TODO Maybe move - does not fit very well here.
    DEFAULT_TAGS_AND_PATH_SEPARATOR = ":"

    def __init__(self,
                 is_prepend: bool,
                 is_append: bool):
        self._is_prepend = is_prepend
        self._is_append = is_append

    @staticmethod
    def new_without_output():
        return TagsRenditionSettings(None)

    def is_output_tags(self) -> bool:
        return self._is_prepend or self._is_append

    def is_prepend(self) -> bool:
        return self._is_prepend

    def tags_and_path_separator(self) -> str:
        return self.DEFAULT_TAGS_AND_PATH_SEPARATOR

    def render_path(self,
                    tags: frozenset,
                    path: str):
        if not self.is_output_tags():
            return path
        return self._concatenate(self._render_tags_string(tags),
                                 path)

    def render_print_tags(self,
                          tags: frozenset):
        return self._render_tags_string(tags)

    @staticmethod
    def _render_tags_string(tags: frozenset) -> str:
        return " ".join(sorted(tags))

    def _concatenate(self,
                     tags_string: str,
                     path: str):
        components = []
        if self._is_prepend:
            components.append(tags_string)
        components.append(path)
        if self._is_append:
            components.append(tags_string)
        return self.tags_and_path_separator().join(components)


class RenditionSettings:
    """
    Settings for rendering the output.
    """
    def __init__(self,
                 file_names_are_relative_file_argument_location: bool,
                 include_existing_files: bool,
                 include_non_existing_files: bool,
                 normalize_paths: bool,
                 absolute_paths: bool,
                 tags_settings: TagsRenditionSettings,
                 suppress_non_path_output: bool):
        """
        :rtype : RenditionSettings
        """
        self.file_names_are_relative_file_argument_location = file_names_are_relative_file_argument_location
        self.include_existing_in_output = include_existing_files
        self.include_non_existing_files = include_non_existing_files
        self.normalize_paths = normalize_paths
        self.absolute_paths = absolute_paths
        self.tags_settings = tags_settings
        self.suppress_non_path_output = suppress_non_path_output

    def tags_settings(self) -> TagsRenditionSettings:
        return self.tags_settings


class RenditionEnvironment(ResultItemsConstructionEnvironment):
    """
    Environment used during the rendition of a ResultItem.
    """

    @staticmethod
    def for_top_level_file(file_name: str,
                           program_should_fail_on_non_existing_file: bool,
                           tags_condition: TagsCondition,
                           settings: RenditionSettings,
                           tags: Tags):
        return RenditionEnvironment(FileReferenceEnvironment.for_top_level_file(file_name),
                                    program_should_fail_on_non_existing_file,
                                    tags_condition,
                                    tags,
                                    settings)

    def __init__(self,
                 file_ref_env: FileReferenceEnvironment,
                 program_should_fail_on_non_existing_file: bool,
                 tags_condition: TagsCondition,
                 tags: Tags,
                 rendition_settings: RenditionSettings):
        ResultItemsConstructionEnvironment.__init__(self,
                                                    file_ref_env,
                                                    program_should_fail_on_non_existing_file,
                                                    tags_condition,
                                                    tags)
        self.rendition_settings = rendition_settings

    def render_file_path(self,
                         file_name: str,
                         tags: frozenset) -> str:
        path = self._render_file_name_according_to_settings(file_name)
        tags_settings = self.rendition_settings.tags_settings
        if tags_settings.is_output_tags():
            return tags_settings.render_path(tags, path)
        else:
            return path

    def _render_file_name_according_to_settings(self,
                                                file_name: str) -> str:
        if self.rendition_settings.file_names_are_relative_file_argument_location:
            ret_val = self.file_ref_env.file_name_relative_top_level_source_file(file_name)
        else:
            ret_val = self.file_ref_env.file_name_relative_current_dir_of_process(file_name)
        if self.rendition_settings.normalize_paths:
            ret_val = os.path.normpath(ret_val)
        if self.rendition_settings.absolute_paths:
            ret_val = os.path.abspath(ret_val)
        return ret_val


class ResultItem:
    """
    An item in a successful result, ready for rendering.

    The rendering is not allowed to raise exceptions related to
    the instruction that constructs this object.  I.e., all checks
    and parses must be done.
    """

    def include_in_output(self,
                          env: RenditionEnvironment) -> bool:
        """
        Tells if this item should be output.
        """
        raise NotImplementedError()

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        """
        The string to output if this item should be output.

        Not allowed to raise exceptions (except for implementation issues,
        of course).
        """
        raise NotImplementedError()


class ResultItemForOtherThanFilePath(ResultItem):
    """
    A ResultItem that is not a file-path.

    When suppression of non-path-output is turned on,
    then rendering of the item will produce no output.
    """

    def include_in_output(self,
                          env: RenditionEnvironment) -> bool:
        return not env.rendition_settings.suppress_non_path_output


class ParsingSettings:
    def __init__(self,
                 preprocessor_shell_command_or_none: str,
                 line_parsers: list,
                 instruction_parsers_dict: dict):
        """
        :param line_parsers: List of LineParser.

        :param instruction_parsers_dict: Maps instruction identifiers to
         parsers: str -> InstructionArgumentParser.
        """
        self.preprocessor_shell_command_or_none = preprocessor_shell_command_or_none
        self.line_parsers = line_parsers
        self.instruction_parsers_dict = instruction_parsers_dict

    def parser_for_instruction(self,
                               identifier: str):
        """
        :rtype InstructionArgumentParser
        """
        return self.instruction_parsers_dict[identifier]


class ResultItemsConstructor:
    """An iterable of ResultItem:s."""

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        """
        Gives an iterable of all ResultItem:s that this object represents.

        Can raise exceptions related to list-file parsing and file checking.
        """
        raise NotImplementedError()


###############################################################################
# - concrete ResultItem:s -
###############################################################################


class ResultItemForPrint(ResultItemForOtherThanFilePath):
    """
    An result item that prints a constant string.
    """
    def __init__(self,
                 string: str):
        self._string = string

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        return self._string


class ResultItemForFilePathExisting(ResultItem):
    """
    An result item that is a file-path who's corresponding file exists.
    """
    def __init__(self,
                 file_name: str,
                 tags: frozenset):
        """
        file_name : the name of the file as specified in the source file -
        i.e. it is relative the source file.
        """
        self.file_name = file_name
        self.tags = tags

    def include_in_output(self, env: RenditionEnvironment) -> bool:
        return env.rendition_settings.include_existing_in_output

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        return env.render_file_path(self.file_name,
                                    self.tags)


class ResultItemForFilePathNonExisting(ResultItem):
    """
    An result item that is a file-path who's corresponding file does not exists.
    """
    def __init__(self,
                 file_name: str,
                 tags: frozenset):
        """
        file_name : the name of the file as specified in the source file -
        i.e. it is relative the source file.
        """
        self.file_name = file_name
        self.tags = tags

    def include_in_output(self, env: RenditionEnvironment) -> bool:
        return env.rendition_settings.include_non_existing_files

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        return env.render_file_path(self.file_name,
                                    self.tags)


###############################################################################
# - Processor:s -
###############################################################################


class WithSourceReferenceMixin:
    """A mixin class for the property of having a IncludeFileChain."""
    def __init__(self,
                 source: SourceReference):
        self._source = source

    def source_reference(self):
        return self._source

    def render_source_line_chain(self, o_stream):
        for include in self._source.as_include_file_chain().from_top_to_bottom():
            o_stream.write(include.err_msg_file_ref_with_source_line())
            o_stream.write(os.linesep * 2)


class ResultItemConstructionExceptionBase(WithSourceReferenceMixin, Exception):
    """
    Base class for exceptions that indicates failure of an instruction
    to produce one of its ResultItem:s.
    """

    def __init__(self,
                 source: SourceReference,
                 exit_code: int):
        WithSourceReferenceMixin.__init__(self, source)
        self.exitCode = exit_code

    def render(self, o_stream):
        self.render_source_line_chain(o_stream)
        self.render_sub_class_specifics(self.source_reference().source_line,
                                        o_stream)

    def render_sub_class_specifics(self,
                                   source_line: SourceLineInFile,
                                   o_stream):
        """Implements the part that is specific per sub class."""
        raise NotImplementedError()


class Processor(ResultItemsConstructor):
    """
    Base class for instructions.

    An instruction produces an iterable of ResultItem:s.
    """
    def __init__(self, source: SourceReference):
        self.source = source

    def file_processor_if_this_is_a_processor_for_include(self,
                                                          parsing_settings: ParsingSettings,
                                                          env: ResultItemsConstructionEnvironment):
        """
        This method was introduced for implementing the command
        that prints the file inclusion hierarchy.
        :return: ProcessorForListFile. None, if this is not a processor for an include instruction.
        Otherwise, the ProcessorForListFile for the include instruction.
        """
        return None


class ProcessorForListFile(Processor):
    """A list of processors from a single file."""

    def __init__(self,
                 file_name: str,
                 file_name_relative_including_file: str,
                 source: SourceReference,
                 processors: list):
        Processor.__init__(self, source)
        self._file_name = file_name
        self._file_name_relative_including_file = file_name_relative_including_file
        self._processors = processors

    def file_name(self) -> str:
        return self._file_name

    def file_name_relative_including_file(self) -> str:
        return self._file_name_relative_including_file

    def processors(self) -> list:
        return self._processors

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        return ResultItemIterableForFile(parsing_settings,
                                         self._processors,
                                         env)


class ResultItemIterableForFile:
    def __init__(self,
                 parsing_settings: ParsingSettings,
                 instructions: list,
                 env: ResultItemsConstructionEnvironment):
        self.instructions = instructions
        self.parsing_settings = parsing_settings
        self.env = env
        self.curr_result_item_iterable = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.curr_result_item_iterable is None:
                if not self.instructions:
                    raise StopIteration
                instruction = self.instructions.pop(0)
                self.curr_result_item_iterable = instruction.result_item_iterable(self.parsing_settings,
                                                                                  self.env)
            try:
                return self.curr_result_item_iterable.__next__()
            except StopIteration:
                self.curr_result_item_iterable = None


###############################################################################
# - concrete instructions -
###############################################################################


class ResultItemConstructionForMissingFileException(ResultItemConstructionExceptionBase):
    """
    Indicates that a referenced file does not exist.
    """

    def __init__(self,
                 source: SourceReference,
                 file_name_relative_current_dir_of_process: str):
        ResultItemConstructionExceptionBase.__init__(self,
                                                     source,
                                                     EXIT_FILE_DOES_NOT_EXIST)
        self.file_name_relative_current_dir_of_process = file_name_relative_current_dir_of_process

    def render_sub_class_specifics(self,
                                   source_line: SourceLineInFile,
                                   o_stream):
        write_lines(o_stream,
                    [
                        "File does not exist: " +
                        in_source_quotes(self.file_name_relative_current_dir_of_process)
                    ])


###############################################################################
# - ProcessorForPrint -
###############################################################################


class ProcessorForPrint(Processor):
    """
    An instruction that resolves a single named file.
    """
    def __init__(self,
                 source: SourceReference,
                 string: str):
        Processor.__init__(self, source)
        self._string = string

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        return iter([ResultItemForPrint(self._string)])


###############################################################################
# - ProcessorForShell -
###############################################################################


class ResultItemConstructionForShellException(ResultItemConstructionExceptionBase):
    def __init__(self,
                 source: SourceReference,
                 called_process_error: subprocess.CalledProcessError):
        ResultItemConstructionExceptionBase.__init__(self,
                                                     source,
                                                     EXIT_SHELL_COMMAND_EXECUTION_ERROR)
        self._called_process_error = called_process_error

    def render_sub_class_specifics(self,
                                   source_line: SourceLineInFile,
                                   o_stream):
        write_lines(o_stream,
                    [
                        "Shell command failed.",
                        "Command exit code: " + str(self._called_process_error.returncode)
                    ])
        if self._called_process_error.output:
            write_lines(o_stream,
                        [
                            "Output from command:",
                            self._called_process_error.output,
                        ])


class ProcessorForShell(Processor):
    """
    An instruction that executes a shell command and interprets it's output a file names.
    """
    def __init__(self,
                 source: SourceReference,
                 command_line: str):
        Processor.__init__(self, source)
        self._command_line = command_line

    def result_item_iterable(self, parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        if not env.current_tags_satisfies_tags_filter():
            return iter([])
        try:
            cwd = env.file_ref_env.fromCurrDir
            if not cwd:
                cwd = "."
            output = subprocess.check_output(self._command_line,
                                             shell=True,
                                             cwd=cwd,
                                             universal_newlines=True)
            file_names = output.splitlines()
            return ResultItemIteratorForFilesFromFilePaths(self.source,
                                                           env,
                                                           iter(file_names)).__iter__()
        except subprocess.CalledProcessError as ex:
            raise ResultItemConstructionForShellException(self.source, ex)


###############################################################################
# - ProcessorForFile -
###############################################################################


class ResultItemIteratorForFilesFromFilePaths:
    """
    An iterator of ResultItemForFile, constructed from an iterable of file-names.

    Produces elements only for the files that passes all file conditions: tags-filtering, existence.

    All files are expected to be referenced from the same list-file.
    All files are expected to be given the same tags.
    """
    def __init__(self,
                 source: SourceReference,
                 env: ResultItemsConstructionEnvironment,
                 file_names_rel_list_file: iter):
        self._source = source
        self._env = env
        self._file_names_rel_list_file = file_names_rel_list_file
        self._tags = env.tags().frozen_tags()

    def __iter__(self):
        if not self._env.current_tags_satisfies_tags_filter():
            return iter([])
        else:
            return self

    def __next__(self):
        file_name = self._file_names_rel_list_file.__next__()
        file_path = self._env.file_ref_env.file_name_relative_current_dir_of_process(file_name)
        path_exists = os.path.exists(file_path)
        if path_exists:
            return ResultItemForFilePathExisting(
                self._env.file_ref_env.file_name_relative_top_level_source_file(file_name),
                self._tags)
        else:
            if self._env.fail_on_non_existing_file:
                raise ResultItemConstructionForMissingFileException(self._source, file_path)
            else:
                return ResultItemForFilePathNonExisting(
                    self._env.file_ref_env.file_name_relative_top_level_source_file(file_name),
                    self._tags)


class ProcessorForFilePath(Processor):
    """
    An instruction that resolves a single named file.
    """
    def __init__(self,
                 source: SourceReference,
                 file_name: str):
        Processor.__init__(self, source)
        self.file_name = file_name

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        return ResultItemIteratorForFilesFromFilePaths(self.source,
                                                       env,
                                                       iter([self.file_name])).__iter__()


###############################################################################
# - ProcessorForFind -
###############################################################################


class ListAndFindSettings:
    """
    Settings relevant to directory listing and find.

    The settings are on a "high level" - ready for use
    without further parsing.
    """
    def __init__(self,
                 relative_directory_name: str,
                 file_matcher,
                 sort: bool):
        self.relative_directory_name = relative_directory_name
        self.file_matcher = file_matcher
        self.sort = sort


class FileMatchInfo:
    """Mutable info about a file to match for inclusion in the result of the program.
    The info is mutable so that matchers can set information they need
    which may also be needed by later matchers.
    """
    def __init__(self,
                 path: str,
                 path_rel_dir_argument: str,
                 base_name: str):
        self._path = path
        self._path_rel_dir_argument = path_rel_dir_argument
        self._base_name = base_name
        self._stat_result = None

    def path(self):
        return self._path

    def base_name(self):
        return self._base_name

    def stat_result(self) -> os.stat_result:
        """Return not-None: reads info if not present."""
        if not self._stat_result:
            self._stat_result = os.stat(self.path())
        return self._stat_result


class ProcessorForFileSetBase(Processor):
    """
    An instruction that resolves the contents of a directory.
    """
    def __init__(self,
                 source: SourceReference,
                 settings: ListAndFindSettings):
        Processor.__init__(self, source)
        self.settings = settings
        self.env_for_dir = None

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        dir_path = env.file_ref_env.file_name_relative_current_dir_of_process(self.settings.relative_directory_name)
        if not os.path.isdir(dir_path):
            raise ResultItemConstructionForMissingFileException(self.source, dir_path)
        if not env.current_tags_satisfies_tags_filter():
            return iter([])
        self.env_for_dir = env.new_for_directory(self.settings.relative_directory_name)
        if self.settings.sort:
            return self._sorted_iterable(dir_path, env)
        else:
            return self._unsorted_iterable(dir_path, env)

    def _sorted_iterable(self,
                         dir_path: str,
                         env: ResultItemsConstructionEnvironment) -> iter:
        all_files = [self._new_file_match_info(file_name) for file_name in os.listdir(dir_path)]
        matching_base_names = list(map(FileMatchInfo.base_name,
                                   filter(self.settings.file_matcher,
                                          all_files)))
        # sort
        # Sorting here lets us sort on base_name, which is faster than sorting on
        # the complete result file name.
        matching_base_names.sort()
        file_paths = [self._new_file_result(base_name, env)
                      for base_name in matching_base_names]
        return iter(file_paths)

    def _unsorted_iterable(self,
                           dir_path: str,
                           env: ResultItemsConstructionEnvironment) -> iter:
        for file_base_name in os.listdir(dir_path):
            if not self.settings.file_matcher(self._new_file_match_info(file_base_name)):
                continue
            yield self._new_file_result(file_base_name, env)

    def _new_file_match_info(self, base_name: str) -> FileMatchInfo:
        raise NotImplementedError()

    def _new_file_result(self,
                         base_name: str,
                         env: ResultItemsConstructionEnvironment) -> ResultItemForFilePathExisting:
        return ResultItemForFilePathExisting(
            self.env_for_dir.file_ref_env.file_name_relative_top_level_source_file(base_name),
            env.tags().frozen_tags())


class ProcessorForFind(ProcessorForFileSetBase):
    """
    An instruction that resolves the contents of a directory.
    """
    def __init__(self,
                 source: SourceReference,
                 settings: ListAndFindSettings):
        ProcessorForFileSetBase.__init__(self, source, settings)


###############################################################################
# - ProcessorForDirectoryListing -
###############################################################################


class ProcessorForDirectoryListing(ProcessorForFileSetBase):
    """
    An instruction that resolves the contents of a directory.
    """
    def __init__(self,
                 source: SourceReference,
                 settings: ListAndFindSettings):
        ProcessorForFileSetBase.__init__(self, source, settings)

    def _sorted_iterable(self,
                         dir_path: str,
                         env: ResultItemsConstructionEnvironment) -> iter:
        all_files = [self._new_file_match_info(file_name) for file_name in os.listdir(dir_path)]
        matching_base_names = list(map(FileMatchInfo.base_name,
                                   filter(self.settings.file_matcher,
                                          all_files)))
        # sort
        # Sorting here lets us sort on base_name, which is faster than sorting on
        # the complete result file name.
        matching_base_names.sort()
        file_paths = [self._new_file_result(base_name, env)
                      for base_name in matching_base_names]
        return iter(file_paths)

    def _unsorted_iterable(self,
                           dir_path: str,
                           env: ResultItemsConstructionEnvironment) -> iter:
        for file_base_name in os.listdir(dir_path):
            if not self.settings.file_matcher(self._new_file_match_info(file_base_name)):
                continue
            yield self._new_file_result(file_base_name, env)

    def _new_file_match_info(self, base_name: str) -> FileMatchInfo:
        return FileMatchInfo(self.env_for_dir.file_ref_env.file_name_relative_current_dir_of_process(base_name),
                             base_name,
                             base_name)

    def _new_file_result(self,
                         base_name: str,
                         env: ResultItemsConstructionEnvironment) -> ResultItemForFilePathExisting:
        return ResultItemForFilePathExisting(
            self.env_for_dir.file_ref_env.file_name_relative_top_level_source_file(base_name),
            env.tags().frozen_tags())


###############################################################################
# - ProcessorForInclude -
###############################################################################


class ProcessorForInclude(Processor):
    """
    An instruction that resolves the contents of a list-file.
    """
    def __init__(self,
                 source: SourceReference,
                 file_name_relative_include_file: str,
                 preserve_current_directory: bool,
                 tag_include_settings: TagsSettingsForInclude):
        Processor.__init__(self, source)
        self._file_name_relative_including_file = file_name_relative_include_file
        self._preserve_current_directory = preserve_current_directory
        self._tag_include_settings = tag_include_settings
        self._env_for_file = None
        self._file_processor = None

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        (file_processor, env) = self._get_file_processor_and_env(parsing_settings, env)
        return file_processor.result_item_iterable(parsing_settings,
                                                   env)

    def file_processor_if_this_is_a_processor_for_include(self,
                                                          parsing_settings: ParsingSettings,
                                                          env: ResultItemsConstructionEnvironment):
        return self._get_file_processor_and_env(parsing_settings, env)

    def _get_file_processor_and_env(self,
                                    parsing_settings: ParsingSettings,
                                    current_env: ResultItemsConstructionEnvironment) -> tuple:
        if self._file_processor is None:
            self._set_file_processor_and_env(parsing_settings, current_env)
        return self._file_processor, self._env_for_file

    def _set_file_processor_and_env(self,
                                    parsing_settings: ParsingSettings,
                                    current_env: ResultItemsConstructionEnvironment):
        """
        Sets self._file_processor, self._env_for_file.

        Raises an exception if the file cannot be accessed correctly.
        """
        self._env_for_file = current_env.new_for_included_file(self._file_name_relative_including_file,
                                                               self._preserve_current_directory,
                                                               self._tag_include_settings)
        file_path = current_env.file_ref_env.file_name_relative_current_dir_of_process(
            self._file_name_relative_including_file)
        if not os.path.isfile(file_path):
            raise ResultItemConstructionForMissingFileException(self.source, file_path)
        file_parser = ListFileParser(parsing_settings,
                                     self.source.as_include_file_chain(),
                                     self._file_name_relative_including_file,
                                     file_path)
        lines_source = LinesSourceForIncludedFile(parsing_settings, file_path, self.source)
        self._file_processor = file_parser.apply(lines_source)


###############################################################################
# - InstructionArgumentParser:s -
###############################################################################


class InstructionSyntaxErrorException(WithSourceReferenceMixin, Exception):
    """A syntactic error in an instruction of a source file."""
    def __init__(self,
                 source: SourceReference,
                 description):
        WithSourceReferenceMixin.__init__(self, source)
        self.description = description

    def render(self, o_stream):
        self.render_source_line_chain(o_stream)
        write_lines(o_stream,
                    [
                        self.description
                    ])


class InstructionLineSyntaxErrorException(InstructionSyntaxErrorException):
    """Invalid syntax of a line that should contain an instruction."""
    def __init__(self,
                 source: SourceReference):
        description = "Invalid input line, cannot find instruction:"
        InstructionSyntaxErrorException.__init__(self,
                                                 source,
                                                 description)


class InstructionNameSyntaxErrorException(InstructionSyntaxErrorException):
    """Invalid name of an instruction of a source file."""
    def __init__(self,
                 source: SourceReference,
                 instruction_name: str):
        description = "Invalid instruction name " + in_source_quotes(instruction_name)
        InstructionSyntaxErrorException.__init__(self,
                                                 source,
                                                 description)


class InstructionArgumentSyntaxErrorException(InstructionSyntaxErrorException):
    """The arguments of an instruction are invalid."""
    def __init__(self,
                 source: SourceReference,
                 lines: list):
        description = os.linesep.join(lines)
        InstructionSyntaxErrorException.__init__(self,
                                                 source,
                                                 description)


class InstructionArgumentParserSyntaxErrorException(Exception):
    """
    A syntactic error in an Instruction Argument of a source file.

    This exception is internal to the File Parser and
    Option Parsers.

    This exception is raised by Argument Parsers, and handled by
    the parser, which re-raises it in the form of a
    InstructionSyntaxErrorException.
    """
    def __init__(self,
                 message_lines: list):
        self.message_lines = message_lines

    def message_lines(self):
            return self.message_lines


class InstructionArgumentParser:
    """
    Parses the argument-part of a line in a source file.
    """

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str) -> list:
        """
        Returns a list of Processor:s.

        Raises InstructionArgumentParserSyntaxErrorException in case of parsing error.
        """
        raise NotImplementedError()


class InstructionWithArgparseArgumentParser(InstructionArgumentParser):
    """Argument parser for instructions that uses argparse for parsing the arguments."""

    def __init__(self,
                 instruction_name: str):
        self.instruction_name = instruction_name

    def arg_parser(self) -> argparse.ArgumentParser:
        raise NotImplementedError()

    def _parse(self,
               arguments: list) -> argparse.Namespace:
        try:
            return raise_exception_instead_of_exiting_on_error(self.arg_parser(), arguments)
        except ArgumentParsingException as ex:
            raise InstructionArgumentParserSyntaxErrorException([ex.error_message])


class InstructionSubCommand:
    """
    A sub command of an instruction.
    """
    def __init__(self,
                 name: str,
                 aliases: list,
                 help_text: str):
        self.name = name
        self.aliases = aliases
        self.help_text = help_text

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        raise NotImplementedError()

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        """
        :return: List of Processor:s.
        """
        raise NotImplementedError()


class InstructionWithSubCommandsArgumentParser(InstructionWithArgparseArgumentParser):
    """Argument parser for instructions with sub commands."""

    def __init__(self,
                 sub_commands: list,
                 command_name_for_help_text: str,
                 title_for_help_text: str,
                 description_for_help_text: str):
        InstructionWithArgparseArgumentParser.__init__(self, command_name_for_help_text)
        self.sub_commands = sub_commands
        self._sub_command_parsers = {}
        self._parser = argparse.ArgumentParser(prog=command_name_for_help_text,
                                               add_help=False)
        self._set_sub_commands(self._parser, title_for_help_text, description_for_help_text)

    def arg_parser(self) -> argparse.ArgumentParser:
        return self._parser

    def sub_command_parsers(self) -> dict:
        """
        :return: Dict SUB-COMMAND -> argparse.ArgumentParser
        """
        return self._sub_command_parsers

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):

        prepared_args = self._split_command_line_and_make_first_string_uppercase(instruction_argument)
        args = self._parse(prepared_args)
        return args.func.execute(parsing_settings, source, args)

    def _set_sub_commands(self,
                          parser: argparse.ArgumentParser,
                          title_for_help_text: str,
                          description_for_help_text: str) -> argparse.ArgumentParser:
        subparsers = parser.add_subparsers(title=title_for_help_text,
                                           description=description_for_help_text)
        for sub_command in self.sub_commands:
            sub_parser = subparsers.add_parser(sub_command.name,
                                               add_help=False,
                                               aliases=sub_command.aliases,
                                               help=sub_command.help_text)
            sub_command.add_arguments(sub_parser)
            sub_parser.set_defaults(func=sub_command)
            self._sub_command_parsers[sub_command.name] = sub_parser
        return parser

    @staticmethod
    def _split_command_line_and_make_first_string_uppercase(command_line: str):
        commands = shlex.split(command_line)
        if commands:
            commands[0] = commands[0].upper()
        return commands


###############################################################################
# - InstructionArgumentParserForPrint -
###############################################################################


class InstructionArgumentParserForPrint(InstructionArgumentParser):
    """Parser for printing a string."""

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):
        return [ProcessorForPrint(source, instruction_argument)]


###############################################################################
# - InstructionArgumentParserForShell -
###############################################################################


class InstructionArgumentParserForShell(InstructionArgumentParser):
    """Parser for printing a string."""

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):
        stripped_arguments = instruction_argument.strip()
        if not stripped_arguments:
            raise InstructionArgumentParserSyntaxErrorException(["missing command-line"])
        return [ProcessorForShell(source, instruction_argument)]


###############################################################################
# - Tags -
###############################################################################


class ResultItemConstructionForPopEmptyStackException(ResultItemConstructionExceptionBase):
    """
    Indicates a POP command was used while the stack was empty.
    """

    def __init__(self,
                 source: SourceReference):
        ResultItemConstructionExceptionBase.__init__(self,
                                                     source,
                                                     EXIT_TAGS_ERROR)

    def render_sub_class_specifics(self,
                                   source_line: SourceLineInFile,
                                   o_stream):
        write_lines(o_stream,
                    [
                        "Pop of tags from empty stack."
                    ])


class ResultItemForTagsPrint(ResultItemForOtherThanFilePath):
    """
    An result item that prints tags.
    """
    def __init__(self,
                 tags: frozenset,
                 prefix: str,
                 suffix: str):
        self._tags = tags
        self._prefix = prefix
        self._suffix = suffix

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        return "".join([self._prefix,
                        env.rendition_settings.tags_settings.render_print_tags(self._tags),
                        self._suffix])


class ResultItemForTagsPrintStack(ResultItemForOtherThanFilePath):
    """
    An result item that prints tags.
    """
    def __init__(self,
                 stack: list,
                 prefix: str,
                 suffix: str):
        self._stack = [sorted(s) for s in stack]
        self._prefix = prefix
        self._suffix = suffix

    def rendition(self,
                  env: RenditionEnvironment) -> str:
        return "".join([self._prefix,
                        str(self._stack),
                        self._suffix])


class ProcessorForTagsAdd(Processor):
    """
    An instruction that adds tags in the environment.
    """
    def __init__(self,
                 source: SourceReference,
                 tags: list):
        Processor.__init__(self, source)
        self._tags = tags

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        env.tags().add(self._tags)
        return iter([])


class ProcessorForTagsPrint(Processor):
    """
    An instruction that adds tags in the environment.
    """
    def __init__(self,
                 source: SourceReference,
                 prefix: str,
                 suffix: str):
        Processor.__init__(self, source)
        self._prefix = prefix
        self._suffix = suffix

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        return iter([ResultItemForTagsPrint(env.tags().frozen_tags(),
                                            self._prefix,
                                            self._suffix)])


class ProcessorForTagsPrintStack(Processor):
    """
    An instruction that adds tags in the environment.
    """
    def __init__(self,
                 source: SourceReference,
                 prefix: str,
                 suffix: str):
        Processor.__init__(self, source)
        self._prefix = prefix
        self._suffix = suffix

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        return iter([ResultItemForTagsPrintStack(env.tags().stack(),
                                                 self._prefix,
                                                 self._suffix)])


class ProcessorForTagsPush(Processor):
    """
    An instruction that pushes the current tags to the tags stack.
    """
    def __init__(self,
                 source: SourceReference):
        Processor.__init__(self, source)

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        env.tags().push()
        return iter([])


class ProcessorForTagsPop(Processor):
    """
    An instruction that pops the current tags of the tags stack.
    """
    def __init__(self,
                 source: SourceReference):
        Processor.__init__(self, source)

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        if not env.tags().stack():
            raise ResultItemConstructionForPopEmptyStackException(self.source)
        env.tags().pop()
        return iter([])


class ProcessorForTagsRemove(Processor):
    """
    An instruction that removes tags in the environment.
    """
    def __init__(self,
                 source: SourceReference,
                 tags: list):
        Processor.__init__(self, source)
        self._tags = tags

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        if not self._tags:
            env.tags().clear()
        else:
            env.tags().remove(self._tags)
        return iter([])


class ProcessorForTagsSet(Processor):
    """
    An instruction that sets the tags in the environment.
    """
    def __init__(self,
                 source: SourceReference,
                 tags: list):
        Processor.__init__(self, source)
        self._tags = tags

    def result_item_iterable(self,
                             parsing_settings: ParsingSettings,
                             env: ResultItemsConstructionEnvironment):
        env.tags().set(self._tags)
        return iter([])


class TagsSubCommandForListOfTagsArgumentsBase(InstructionSubCommand):
    """
    Base class for sub commands for the tags instruction with.

    These commands has a single argument which is a list of tags.
    They also produces a single Processor, which constructor takes
    the list of tags.
    """
    def __init__(self,
                 name: str,
                 aliases: list,
                 help_text: str,
                 processor_class):
        InstructionSubCommand.__init__(self, name, aliases, help_text)
        self.processor_class = processor_class

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        parser.add_argument("tags",
                            nargs="*",
                            metavar="TAG")

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        return [self.processor_class(source,
                                     self.parse_tags_list(args.tags))]

    @staticmethod
    def parse_tags_list(list_split_on_white_space: list) -> list:
        return parse_tags_list(" ".join(list_split_on_white_space))


class TagsSubCommandForPrint(InstructionSubCommand):
    """
    The tags PRINT sub command
    """

    DESCRIPTION = "Prints the current set of tags listed in alphanumeric order."

    def __init__(self,
                 name: str,
                 aliases: list):
        InstructionSubCommand.__init__(self,
                                       name,
                                       aliases,
                                       self.DESCRIPTION)

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        parser.add_argument("-p", "--prefix",
                            metavar="STRING",
                            nargs=1,
                            default=[""],
                            help="""\
                            Print the given string before the tags. (Use quotes to include space.)""")
        parser.add_argument("-s", "--suffix",
                            metavar="STRING",
                            nargs=1,
                            default=[""],
                            help="""\
                            Print the given string after the tags. (Use quotes to include space.)""")

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        return [ProcessorForTagsPrint(source,
                                      args.prefix[0],
                                      args.suffix[0])]


class TagsSubCommandForPrintStack(InstructionSubCommand):
    """
    The tags PRINT-STACK sub command
    """

    DESCRIPTION = "Prints the tags stack."

    def __init__(self,
                 name: str,
                 aliases: list):
        InstructionSubCommand.__init__(self,
                                       name,
                                       aliases,
                                       self.DESCRIPTION)

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        parser.add_argument("-p", "--prefix",
                            metavar="STRING",
                            nargs=1,
                            default=[""],
                            help="""\
                            Print the given string before the stack. (Use quotes to include space.)""")
        parser.add_argument("-s", "--suffix",
                            metavar="STRING",
                            nargs=1,
                            default=[""],
                            help="""\
                            Print the given string after the stack. (Use quotes to include space.)""")

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        return [ProcessorForTagsPrintStack(source,
                                           args.prefix[0],
                                           args.suffix[0])]


class TagsSubCommandForPush(InstructionSubCommand):
    """
    The tags PUSH sub command
    """
    def __init__(self,
                 name: str,
                 aliases: list):
        InstructionSubCommand.__init__(self,
                                       name,
                                       aliases,
                                       """Pushes the current tags on the stack of tags.
                                       The current tags are unaffected.""")

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        pass

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        return [ProcessorForTagsPush(source)]


class TagsSubCommandForPop(InstructionSubCommand):
    """
    The tags POP sub command
    """
    def __init__(self,
                 name: str,
                 aliases: list):
        InstructionSubCommand.__init__(self,
                                       name,
                                       aliases,
                                       "Pops tags from the tags stack and sets the current tags to these tags.")

    def add_arguments(self,
                      parser: argparse.ArgumentParser):
        pass

    def execute(self,
                parsing_settings: ParsingSettings,
                source: SourceReference,
                args: argparse.Namespace) -> list:
        return [ProcessorForTagsPop(source)]


class TagsSubCommandForSet(TagsSubCommandForListOfTagsArgumentsBase):
    def __init__(self,
                 name: str,
                 aliases: list):
        TagsSubCommandForListOfTagsArgumentsBase.__init__(
            self,
            name,
            aliases,
            "Sets the current set of tags to the given tags.",
            ProcessorForTagsSet)


class TagsSubCommandForAdd(TagsSubCommandForListOfTagsArgumentsBase):
    def __init__(self,
                 name: str,
                 aliases: list):
        TagsSubCommandForListOfTagsArgumentsBase.__init__(
            self,
            name,
            aliases,
            "Adds the given tags to the current set of tags.",
            ProcessorForTagsAdd)


class TagsSubCommandForRemove(TagsSubCommandForListOfTagsArgumentsBase):
    def __init__(self,
                 name: str,
                 aliases: list):
        TagsSubCommandForListOfTagsArgumentsBase.__init__(
            self,
            name,
            aliases,
            "Removes the given tags to the current set of tags. If no tags are given, then all tags are removed.",
            ProcessorForTagsRemove)


class InstructionArgumentParserForTags(InstructionWithSubCommandsArgumentParser):
    """Parser for the tag instruction."""

    def __init__(self,
                 command_name_for_help_text: str):
        InstructionWithSubCommandsArgumentParser.__init__(
            self,
            [
                TagsSubCommandForAdd("ADD", []),
                TagsSubCommandForPop("POP", []),
                TagsSubCommandForPrint("PRINT", []),
                TagsSubCommandForPrintStack("PRINT-STACK", []),
                TagsSubCommandForPush("PUSH", []),
                TagsSubCommandForRemove("REMOVE", ["RM"]),
                TagsSubCommandForSet("SET", []),
            ],
            command_name_for_help_text,
            "Tags sub commands",
            """\
            Manages a set of tags that will be associated with file-paths.
            Each file-path is associated with the "current" set of tags.
            Some of the sub commands modify this "current" set of tags.
            Each "tag" is a string without whitespace or comma.""")


###############################################################################
# - InstructionArgumentParserForDirectoryListing -
###############################################################################


def wildcard_matcher(wildcard: str):
    """A mather that matches on Unix-style wildcards."""
    try:
        regex_string = fnmatch.translate(wildcard)
        regex = re.compile(regex_string)
    except:
        raise InstructionArgumentParserSyntaxErrorException(["Invalid wildcard: " + in_source_quotes(wildcard)])

    def f(file: FileMatchInfo) -> bool:
        return regex.match(file.base_name())
    return f


def regex_matcher(regex_string: str):
    """A mather that matches on Regular Expressions."""
    try:
        regex = re.compile(regex_string)
    except:
        raise InstructionArgumentParserSyntaxErrorException(["Invalid regular expression: " +
                                                             in_source_quotes(regex_string)])

    def f(file: FileMatchInfo) -> bool:
        return regex.search(file.base_name()) is not None
    return f


class FileType:
    """
    Specifies a condition on the type of a file.
    The condition is parsed from a string, making the class
    suitable for us by an ArgumentParser.
    """

    TYPES = {
        "f": stat.S_ISREG,
        "d": stat.S_ISDIR,
    }

    def __init__(self, s: str):
        try:
            self.mode_predicate = self.TYPES[s]
        except KeyError:
            valid_types = ", ".join(self.TYPES.keys())
            raise InstructionArgumentParserSyntaxErrorException(["Invalid file type: " + in_source_quotes(s),
                                                                 "Valid types are " + valid_types + "."])

    def new_matcher(self):
        return file_type_matcher(self)


def file_type_matcher(expected_type: FileType):
    def f(file: FileMatchInfo) -> bool:
        return expected_type.mode_predicate(file.stat_result()[stat.ST_MODE])
    return f


def list__parse_file_type_matcher(list_args: argparse.Namespace) -> list:
    matchers = [file_type[0].new_matcher()
                for file_type in list_args.type]
    return [or_matcher(matchers)] if matchers else []


def list__parse_include_name_matchers_new_new(list_args: argparse.Namespace) -> list:
    or_list = []
    or_list.extend([wildcard_matcher(shell_pattern) for shell_pattern in list_args.patterns])
    or_list.extend([regex_matcher(regex[0]) for regex in list_args.regex_list])

    return [or_matcher(or_list)] if or_list else []


def list__parse_excludes(list_args: argparse.Namespace) -> list:
    name_matchers = []
    name_matchers.extend([wildcard_matcher(wildcard[0])
                          for wildcard in list_args.exclude_pattern_list])
    name_matchers.extend([regex_matcher(regex[0])
                          for regex in list_args.exclude_regex_list])
    return [not_matcher(or_matcher(name_matchers))]\
        if name_matchers\
        else []


class InstructionArgumentParserForDirectoryListing(InstructionWithArgparseArgumentParser):
    """Parser for listing files in a directory."""

    DESCRIPTION = """
    Prints paths of the files inside a directory.

    DIRECTORY is the directory to list-files in.
    Use . for the directory of the list-file.

    Arguments uses shell-style syntax for quoting, etc.
    """

    def __init__(self,
                 instruction_name: str):
        InstructionWithArgparseArgumentParser.__init__(self, instruction_name)
        self._parser = self._construct_argparser(instruction_name)

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):
        list_settings = self._parse_argument(instruction_argument)
        return [ProcessorForDirectoryListing(source, list_settings)]

    def arg_parser(self) -> argparse.ArgumentParser:
        return self._parser

    def _parse_argument(self,
                        instruction_argument: str) -> ListAndFindSettings:
        arguments = shlex.split(instruction_argument)
        if not arguments:
            msg = "A directory must be given (use '.' for current directory)."
            raise InstructionArgumentParserSyntaxErrorException([msg])
        directory = arguments[0]

        args = self._parse(arguments[1:])
        matcher = self._parse_matcher(args)
        return ListAndFindSettings(directory,
                            matcher,
                            args.sort)

    _TOP_LEVEL_ANDS = [list__parse_file_type_matcher,
                       list__parse_include_name_matchers_new_new,
                       list__parse_excludes]

    def _parse_matcher(self,
                       args: argparse.Namespace):
        and_list = []
        for constructor in self._TOP_LEVEL_ANDS:
            and_list.extend(constructor(args))
        return and_matcher(and_list)

    def _construct_argparser(self, instruction_name_for_help_text: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=instruction_name_for_help_text + " DIRECTORY",
                                         add_help=False,
                                         description=self.DESCRIPTION)
        parser.add_argument("patterns",
                            metavar="PATTERN",
                            nargs="*",
                            help="""\
                            A condition of the files in the directory to include,
                            in terms of a Unix like shell-style wildcard.

                            (E.g. the constructs "*, ?, [abc],[!abc]".)
                            Each PATTERN is applied to the base-name of the files in the
                            directory.
                            If no PATTERN is given, then there is no condition on the
                            file name.
                            If PATTERNs are given, then the condition on the file name
                            is to match at least one of these.
                            """)
        parser.add_argument("-r", "--regex",
                            metavar="REG-EX",
                            nargs=1,
                            dest="regex_list",
                            action="append",
                            default=[],
                            help="""\
                            A condition of the files in the directory to include,
                            in terms of a regular expression.

                            This option can be used multiple times. Each file that matches
                            ANY of the REG-EX will be included.

                            Each REG-EX is applied to the base-name of the files in the
                            directory.

                            The REG-EX is considered to match a file name if it matches
                            any part of the file-name.
                            To limit matches to file-names who's whole name matches the REG-EX,
                            begin and end REG-EX with '^' and '$', respectively.
                            """)
        parser.add_argument("-e", "--exclude",
                            metavar="PATTERN",
                            nargs=1,
                            dest="exclude_pattern_list",
                            action="append",
                            default=[],
                            help="""\
                            Excludes all files who's name matching the given pattern.""")
        parser.add_argument("-E", "--exclude-regex",
                            metavar="REG-EX",
                            nargs=1,
                            dest="exclude_regex_list",
                            action="append",
                            default=[],
                            help="""\
                            Excludes all files who's name matching the given regular expression.""")
        parser.add_argument("-t", "--type",
                            nargs=1,
                            metavar="TYPE",
                            default=[],
                            action="append",
                            type=FileType,
                            help="""\
                            Include only files who's type is the given.
                            "f" for regular file.
                            "d" for directory.

                            If used more than once, they are OR:ed.""")
        parser.add_argument("-s", "--sort",
                            action="store_const",
                            const=True,
                            default=False,
                            help="Makes the output being sorted in alphabetical order.")
        return parser


class InstructionArgumentParserForFind(InstructionWithArgparseArgumentParser):
    """Parser for finding files à la Unix find."""

    DESCRIPTION = """
    Prints paths of the files at arbitrary depth inside a hierarchical directory structure.

    DIRECTORY is the directory to list-files in.
    Use . for the directory of the list-file.

    Arguments uses shell-style syntax for quoting, etc.
    """

    def __init__(self,
                 instruction_name: str):
        InstructionWithArgparseArgumentParser.__init__(self, instruction_name)
        self._parser = self._construct_argparser(instruction_name)

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):
        list_settings = self._parse_argument(instruction_argument)
        return [ProcessorForDirectoryListing(source, list_settings)]

    def arg_parser(self) -> argparse.ArgumentParser:
        return self._parser

    def _parse_argument(self,
                        instruction_argument: str) -> ListAndFindSettings:
        arguments = shlex.split(instruction_argument)
        if not arguments:
            msg = "A directory must be given (use '.' for current directory)."
            raise InstructionArgumentParserSyntaxErrorException([msg])
        directory = arguments[0]

        args = self._parse(arguments[1:])
        matcher = self._parse_matcher(args)
        return ListAndFindSettings(directory,
                                   matcher,
                                   args.sort)

    _TOP_LEVEL_ANDS = [list__parse_file_type_matcher,
                       list__parse_include_name_matchers_new_new,
                       list__parse_excludes]

    def _parse_matcher(self,
                       args: argparse.Namespace):
        and_list = []
        for constructor in self._TOP_LEVEL_ANDS:
            and_list.extend(constructor(args))
        return and_matcher(and_list)

    def _construct_argparser(self, instruction_name_for_help_text: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=instruction_name_for_help_text + " DIRECTORY",
                                         add_help=False,
                                         description=self.DESCRIPTION)
        parser.add_argument("patterns",
                            metavar="PATTERN",
                            nargs="*",
                            help="""\
                            A condition of the files in the directory to include,
                            in terms of a Unix like shell-style wildcard.

                            (E.g. the constructs "*, ?, [abc],[!abc]".)
                            Each PATTERN is applied to the base-name of the files in the
                            directory.
                            If no PATTERN is given, then there is no condition on the
                            file name.
                            If PATTERNs are given, then the condition on the file name
                            is to match at least one of these.
                            """)
        parser.add_argument("-r", "--regex",
                            metavar="REG-EX",
                            nargs=1,
                            dest="regex_list",
                            action="append",
                            default=[],
                            help="""\
                            A condition of the files in the directory to include,
                            in terms of a regular expression.

                            This option can be used multiple times. Each file that matches
                            ANY of the REG-EX will be included.

                            Each REG-EX is applied to the base-name of the files in the
                            directory.

                            The REG-EX is considered to match a file name if it matches
                            any part of the file-name.
                            To limit matches to file-names who's whole name matches the REG-EX,
                            begin and end REG-EX with '^' and '$', respectively.
                            """)
        parser.add_argument("-e", "--exclude",
                            metavar="PATTERN",
                            nargs=1,
                            dest="exclude_pattern_list",
                            action="append",
                            default=[],
                            help="""\
                            Excludes all files who's name matching the given pattern.""")
        parser.add_argument("-E", "--exclude-regex",
                            metavar="REG-EX",
                            nargs=1,
                            dest="exclude_regex_list",
                            action="append",
                            default=[],
                            help="""\
                            Excludes all files who's name matching the given regular expression.""")
        parser.add_argument("-t", "--type",
                            nargs=1,
                            metavar="TYPE",
                            default=[],
                            action="append",
                            type=FileType,
                            help="""\
                            Include only files who's type is the given.
                            "f" for regular file.
                            "d" for directory.

                            If used more than once, they are OR:ed.""")
        parser.add_argument("-s", "--sort",
                            action="store_const",
                            const=True,
                            default=False,
                            help="Makes the output being sorted in alphabetical order.")
        return parser


class InstructionArgumentParserForInclude(InstructionWithArgparseArgumentParser):

    DESCRIPTION = """
    Includes the contents of a given list-file.
    File-paths inside the included list-file are relative the
    location of that list-file (unless options are used to change this).
    """

    def __init__(self,
                 instruction_name: str):
        InstructionWithArgparseArgumentParser.__init__(self, instruction_name)
        self._parser = self._construct_argparser(instruction_name)

    def apply(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              instruction_argument: str):
        args = self._parse_argument(instruction_argument)
        tag_include_settings = TagsSettingsForInclude(not args.do_not_export_tags,
                                                      not args.do_not_import_tags)
        return [ProcessorForInclude(source,
                                    args.file[0],
                                    args.preserve_current_directory,
                                    tag_include_settings)]

    def arg_parser(self) -> argparse.ArgumentParser:
        return self._parser

    def _parse_argument(self,
                        instruction_argument: str) -> argparse.Namespace:
        return self._parse(shlex.split(instruction_argument))

    def _construct_argparser(self, instruction_name_for_help_text: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=instruction_name_for_help_text,
                                         add_help=False,
                                         description=self.DESCRIPTION)
        parser.add_argument("file",
                            metavar="FILE",
                            nargs=1,
                            help="A readable file, who's name is relative the including file.")
        parser.add_argument("-I", "--do-not-import-tags",
                            action="store_const",
                            const=True,
                            default=False,
                            help="Do not import any modifications of the tags state from the included file.")
        parser.add_argument("-E", "--do-not-export-tags",
                            action="store_const",
                            const=True,
                            default=False,
                            help="""Do not export the tags state to the included file.
                            The included file will have an emtpy tags state, just as if it was
                            the first processed file.
                            Add the option to not import tag modifications if you want to
                            preserve the tags state in the including file.""")
        parser.add_argument("-p", "--preserve-current-directory",
                            action="store_const",
                            const=True,
                            default=False,
                            help="""Let the current directory for the included file
                            be the same as for the including file.""")
        return parser


###############################################################################
# - LineParser -
###############################################################################


class LineParser:
    """
    Parses an input line.
    """

    def parse(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              striped_line: str) -> list:
        """
        Returns None if the parser cannot parser the line.
        Otherwise, a list of Processors.
        This list may be empty.
        """
        raise NotImplementedError()


class LineParserForIgnoredLine(LineParser):

    ignored_line_re_string = "\s*(#.*)?$"
    ignored_line_re = re.compile(ignored_line_re_string)

    @staticmethod
    def is_comment_line(line: str) -> bool:
        return bool(LineParserForIgnoredLine.ignored_line_re.match(line))

    def parse(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              striped_line: str) -> list:
        if self.ignored_line_re.match(striped_line):
            return []
        else:
            return None


class LineParserForInstruction(LineParser):

    _name_and_argument_except_prefix_groups_re_string = "(\w+)\s*(.*)"

    def __init__(self,
                 instruction_prefix: str):
        self.name_and_argument_groups_re_string = instruction_prefix +\
            self._name_and_argument_except_prefix_groups_re_string
        self.name_and_argument_groups_re = re.compile(self.name_and_argument_groups_re_string)

    def parse(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              striped_line: str) -> list:

        name_and_argument_match = re.match(self.name_and_argument_groups_re,
                                           striped_line)
        if not name_and_argument_match:
            return None
        (name, argument) = (name_and_argument_match.group(1),
                            name_and_argument_match.group(2))
        try:
            parser = parsing_settings.parser_for_instruction(name.upper())
            return parser.apply(parsing_settings, source, argument)
        except KeyError:
            raise InstructionNameSyntaxErrorException(
                source,
                name)
        except InstructionArgumentParserSyntaxErrorException as ex:
            raise InstructionArgumentSyntaxErrorException(source,
                                                          ex.message_lines)


class LineParserForFilePath(LineParser):
    """
    This parser assumes that all other parsers have failed.
    This means that the line MUST be a file-path.
    So this parsers succeeds unconditionally.
    """
    def parse(self,
              parsing_settings: ParsingSettings,
              source: SourceReference,
              striped_line: str) -> list:

        return [ProcessorForFilePath(source, striped_line)]


###############################################################################
# - FileParser -
###############################################################################


class LinesSource:
    """
    Iterable of lines. E.g. a file or stdin.
    """
    def __iter__(self):
        raise NotImplementedError()


class ListFileParser:
    """
    Parses a source list-file into a ProcessorForListFile object.
    """

    @staticmethod
    def for_top_level(parsing_settings: ParsingSettings,
                      file_name: str):
        return ListFileParser(parsing_settings,
                              IncludeFileChain.new_for_top_level_file(),
                              file_name,
                              file_name)

    # Mutable state.
    # Having these here avoids having to pass them around to almost every
    # method.
    # The values are set by the top level method (apply), so that
    # can access them.
    # Only the apply method is allowed to modify this state.
    line_number = -1
    line = None
    line_stripped = None

    def __init__(self,
                 parsing_settings: ParsingSettings,
                 includes: IncludeFileChain,
                 file_name_relative_including_file: str,
                 file_name: str):
        self._includes = includes
        self._parsing_settings = parsing_settings
        self.file_name_relative_including_file = file_name_relative_including_file
        self.file_name = file_name

    def apply(self,
              lines_source: LinesSource) -> ProcessorForListFile:
        self.line_number = 0
        processors = []
        for line in lines_source:
            self.line = line  # TODO behövs verkligen denna??
            self.line_stripped = line
            self.line_number += 1
            processors += self._processors_for_line()
        return ProcessorForListFile(self.file_name,
                                    self.file_name_relative_including_file,
                                    self._source_reference(),
                                    processors)

    def _processors_for_line(self) -> list:
        for line_parser in self._parsing_settings.line_parsers:
            list_of_processors = line_parser.parse(self._parsing_settings,
                                                   self._source_reference(),
                                                   self.line_stripped)
            if list_of_processors is not None:
                return list_of_processors
        raise InstructionLineSyntaxErrorException(self._source_reference())

    def _source_reference(self) -> SourceReference:
        return SourceReference(self._includes,
                               self._source_info())

    def _source_info(self) -> SourceLineInFile:
        return SourceLineInFile(self.file_name,
                                SourceLine(self.line_number,
                                           self.line))


###############################################################################
# - Command -
###############################################################################


class PreprocessorException(Exception):
    def __init__(self,
                 called_process_error: subprocess.CalledProcessError):
        self._called_process_error = called_process_error

    def render(self, o_stream):
        write_lines(o_stream,
                    [
                        "Preprocessor failed.",
                        "Command exit code: " + str(self._called_process_error.returncode)
                    ])
        if self._called_process_error.output:
            write_lines(o_stream,
                        [
                            "Output from preprocessor:",
                            self._called_process_error.output,
                        ])


class LinesSourceForFileBase(LinesSource):
    def __init__(self,
                 parsing_settings: ParsingSettings):
        self._parsing_settings = parsing_settings

    def _open_file(self):
        raise NotImplementedError()

    def __iter__(self):
        if self._parsing_settings.preprocessor_shell_command_or_none:
            raw_lines = self._raw_lines_from_processed_file(self._parsing_settings.preprocessor_shell_command_or_none)
        else:
            raw_lines = self._raw_lines_directly_from_file()
        return self._from_raw_lines(raw_lines)

    def _raw_lines_directly_from_file(self):
        # Read all lines from the file so that we can close it before
        # opening any included files.
        # This prevents exhausting the number of open files.
        open_file = self._open_file()
        raw_lines = open_file.readlines()
        open_file.close()
        return raw_lines

    def _raw_lines_from_processed_file(self,
                                       preprocessor_shell_command: str):
        open_file = self._open_file()
        try:
            output = subprocess.check_output(preprocessor_shell_command,
                                             shell=True,
                                             universal_newlines=True,
                                             stdin=open_file)
        except subprocess.CalledProcessError as ex:
            raise PreprocessorException(ex)
        open_file.close()
        raw_lines = output.splitlines()
        return raw_lines

    @staticmethod
    def _from_raw_lines(raw_lines: list):
        lines = []
        for lineWithPossibleNewLine in raw_lines:
            lines.append(lineWithPossibleNewLine.strip("\n").rstrip())
        return iter(lines)


class LinesSourceForFileArgument(LinesSourceForFileBase):
    """
    A LinesSource for file arguments on the command line.
    """
    def __init__(self,
                 parsing_settings: ParsingSettings,
                 file_name: str):
        LinesSourceForFileBase.__init__(self, parsing_settings)
        self._file_name = file_name

    def _open_file(self):
        try:
            return open(self._file_name,
                        mode="r")
        except OSError:
            msg = error_header_line("Cannot open file: " +
                                    in_double_quotes(self._file_name))
            write_lines(sys.stderr,
                        [msg])
            sys.exit(EXIT_INVALID_ARGUMENTS)


class LinesSourceForStdin(LinesSourceForFileBase):
    """
    A LinesSource for file arguments on the command line.
    """
    def __init__(self,
                 parsing_settings: ParsingSettings):
        LinesSourceForFileBase.__init__(self, parsing_settings)

    def _open_file(self):
        return sys.stdin


class LinesSourceForNamedFileBase(LinesSourceForFileBase):
    def __init__(self,
                 parsing_settings: ParsingSettings,
                 file_name: str):
        LinesSourceForFileBase.__init__(self, parsing_settings)
        self._file_name = file_name

    def _open_file(self):
        return self._open(self._file_name)

    def _open(self, file_name: str):
        raise NotImplementedError()


class LinesSourceForIncludedFile(LinesSourceForNamedFileBase):
    """
    A LinesSource for files used by the include instruction.
    """
    def __init__(self,
                 parsing_settings: ParsingSettings,
                 file_name: str,
                 source: SourceReference):
        LinesSourceForNamedFileBase.__init__(self, parsing_settings, file_name)
        self._source = source

    def _open(self, file_name: str):
        try:
            return open(file_name, mode="r")
        except OSError:
            raise ResultItemConstructionForMissingFileException(self._source, file_name)


class FileExistenceHandlingSettings:

    def __init__(self,
                 include_existing_in_output: bool,
                 program_should_fail_on_non_existing: bool,
                 include_non_existing_in_output: bool):
        self.include_existing_in_output = include_existing_in_output
        self.program_should_fail_on_non_existing = program_should_fail_on_non_existing
        self.include_non_existing_in_output = include_non_existing_in_output

    @staticmethod
    def new_fail_on_non_existing():
        return FileExistenceHandlingSettings(True, True, False)

    @staticmethod
    def new_ignore_non_existing():
        return FileExistenceHandlingSettings(True, False, False)

    @staticmethod
    def new_include_non_existing():
        return FileExistenceHandlingSettings(True, False, True)

    @staticmethod
    def new_only_non_existing():
        return FileExistenceHandlingSettings(False, False, True)


class FileExistenceHandlingModeOptionParser:
    """Parses the Command Line Option for handling of files depending on existence."""

    _DEFAULT_KEY = "fail"

    _MODES = {
        "fail": (FileExistenceHandlingSettings.new_fail_on_non_existing(),
                 "A missing file causes the program to fail (with exit status " +
                 str(EXIT_FILE_DOES_NOT_EXIST) + ")."),
        "ignore": (FileExistenceHandlingSettings.new_ignore_non_existing(),
                   "Missing files are not included in the output."),
        "include": (FileExistenceHandlingSettings.new_include_non_existing(),
                    "Missing files are included in the output just as existing files."),
        "only": (FileExistenceHandlingSettings.new_only_non_existing(),
                 "Output only missing files."),
    }

    def mode_keys(self) -> list:
        return self._MODES.keys()

    def default_key(self) -> str:
        return self._DEFAULT_KEY

    def keys_help_text(self) -> str:
        return " ".join([in_double_quotes(key) + ": " + val[1]
                         for key, val in self._MODES.items()])

    def lookup(self,
               valid_key: str) -> FileExistenceHandlingSettings:
        return self._MODES[valid_key][0]


class Command:
    """
    Abstract The top-level representation of what the program should do.

    Concrete sub-classes must implement process_file.
    """
    def execute(self,
                file_names: list,
                forward_tags: bool,
                stdin_paths_are_relative_empty: list,
                program_should_fail_on_non_existing_file: bool,
                tags_condition: TagsCondition,
                rendition_settings: RenditionSettings,
                parsing_settings: ParsingSettings):
        file_number = 1
        for file_name in file_names:
            lines_source = self._line_source_for(parsing_settings, file_name)
            parsing_and_rendition_file_name = self._parsing_and_rendition_file_name(stdin_paths_are_relative_empty,
                                                                                    file_name)
            file_parser = ListFileParser.for_top_level(parsing_settings,
                                                       parsing_and_rendition_file_name)
            file_processor = file_parser.apply(lines_source)
            tags = Tags.new_empty()
            if file_number > 1 and forward_tags:
                tags = env.tags()
            env = RenditionEnvironment.for_top_level_file(parsing_and_rendition_file_name,
                                                          program_should_fail_on_non_existing_file,
                                                          tags_condition,
                                                          rendition_settings,
                                                          tags)
            self.process_list_file(file_number, file_processor, parsing_settings, env)
            file_number += 1

    @staticmethod
    def _line_source_for(parsing_settings: ParsingSettings,
                         file_name: str):
        if file_name == COMMAND_LINE_ARGUMENT_FOR_STDIN:
            return LinesSourceForStdin(parsing_settings)
        else:
            return LinesSourceForFileArgument(parsing_settings, file_name)

    def process_list_file(self,
                          file_number: int,
                          file_processor: ProcessorForListFile,
                          parsing_settings: ParsingSettings,
                          env: RenditionEnvironment):
        raise NotImplementedError()

    @staticmethod
    def _parsing_and_rendition_file_name(stdin_paths_are_relative_empty: list,
                                         file_name):
        if file_name == COMMAND_LINE_ARGUMENT_FOR_STDIN and stdin_paths_are_relative_empty:
            return os.path.join(stdin_paths_are_relative_empty[0],
                                COMMAND_LINE_ARGUMENT_FOR_STDIN)
        else:
            return file_name


class ProgramMainFunctionalityCommand(Command):
    """
    Command that implements the main functionality of this program.
    """
    def process_list_file(self,
                          file_number: int,
                          file_processor: ProcessorForListFile,
                          parsing_settings: ParsingSettings,
                          env: RenditionEnvironment):
        for result_item in file_processor.result_item_iterable(parsing_settings,
                                                               env):
            if result_item.include_in_output(env):
                print(result_item.rendition(env))


class Node:
    """
    Type for trees used for printing the inclusion hierarchy.
    """
    def __init__(self,
                 name: str,
                 sub_nodes: list):
        self._name = name
        self._sub_nodes = sub_nodes

    def name(self):
        return self._name

    def sub_nodes(self):
        return self._sub_nodes


class TreePrinter:
    """
    Base class for printers that prints a hierarchy of nodes
    in an indented layout.

    Prints the tree directly on a given output.
    """

    def print(self,
              tree: Node):
        raise NotImplementedError()


class TreePrinterForSimpleLayout(TreePrinter):

    def __init__(self):
        self._indent = 0
        self._indent_string = " "

    def print(self,
              tree: Node):
        self._print_name(tree.name())
        self._indent += 1
        for node in tree.sub_nodes():
            self.print(node)
        self._indent -= 1

    def _print_name(self,
                    name: str):
        print(self._indent_string * self._indent + name)


class TreePrinterForPrettyLayout(TreePrinter):

    INVISIBLE_INDENT = "    "
    I = "│   "
    T = "├── "
    L = "└── "

    def __init__(self):
        self._higher_levels_indents = []

    def print(self,
              tree: Node):
        self._print_name("", tree.name())
        self._print_sub_nodes_of(tree)

    def _print_sub_nodes_of(self, node: Node):
        remaining_sub_nodes = copy.copy(node.sub_nodes())
        while remaining_sub_nodes:
            sub_node = remaining_sub_nodes.pop(0)
            self._print_tree(not bool(remaining_sub_nodes),
                             sub_node)

    def _print_tree(self,
                    is_last_sibling: bool,
                    tree: Node):
        parent_connector = self.L if is_last_sibling else self.T
        self._print_name(parent_connector, tree.name())

        parent_indent = self.INVISIBLE_INDENT if is_last_sibling else self.I
        self._higher_levels_indents.append(parent_indent)
        self._print_sub_nodes_of(tree)
        del self._higher_levels_indents[-1]

    def _print_name(self,
                    prefix: str,
                    name: str):
        print("".join(self._higher_levels_indents) + prefix + name)


class PrintInclusionHierarchyCommand(Command):

    def __init__(self,
                 printer: TreePrinter,
                 print_file_names_relative_including_file: bool,
                 separate_file_trees_by_empty_line: bool):
        self._printer = printer
        self._print_file_names_relative_including_file = print_file_names_relative_including_file
        self._separate_file_trees_by_empty_line = separate_file_trees_by_empty_line

    def process_list_file(self,
                          file_number: int,
                          file_processor: ProcessorForListFile,
                          parsing_settings: ParsingSettings,
                          env: RenditionEnvironment):
        if self._separate_file_trees_by_empty_line and file_number != 1:
            print()
        tree = self.tree_for_file(file_processor,
                                  parsing_settings,
                                  env)
        self._printer.print(tree)

    def tree_for_file(self,
                      file_processor: ProcessorForListFile,
                      parsing_settings: ParsingSettings,
                      env: RenditionEnvironment) -> Node:
        sub_nodes = []
        for processor in file_processor.processors():
            file_processor_and_env = processor.file_processor_if_this_is_a_processor_for_include(parsing_settings,
                                                                                                 env)
            if file_processor_and_env is not None:
                sub_node = self.tree_for_file(file_processor_and_env[0],
                                              parsing_settings,
                                              file_processor_and_env[1])
                sub_nodes.append(sub_node)
        return Node(self.file_name_for(file_processor),
                    sub_nodes)

    def file_name_for(self,
                      file_processor: ProcessorForListFile):
        if self._print_file_names_relative_including_file:
            return file_processor.file_name_relative_including_file()
        else:
            return file_processor.file_name()


###############################################################################
# - configuration of instructions -
###############################################################################


class InstructionDescription:
    """Detailed description of an instruction."""
    def render_as_lines(self,
                        wrapper: textwrap.TextWrapper) -> list:
        """Renders the description as a list of lines."""
        raise NotImplementedError()


class InstructionDescriptionExplicit(InstructionDescription):
    """Detailed description of an instruction."""
    def __init__(self,
                 one_line_description: str,
                 arguments_syntax: str,
                 arguments: list,
                 long_description: str):
        """
        :param one_line_description:
        :param arguments_syntax: One-line description of arguments, à la -h
        :param arguments: List of (argument-name,argument-description)
        """
        self.one_line_description = one_line_description
        self.arguments_syntax = arguments_syntax
        self.arguments = arguments
        self.long_description = long_description

    def render_as_lines(self,
                        wrapper: textwrap.TextWrapper) -> list:
        """Renders the description as a list of lines."""
        ret_val = []
        ret_val += self._render_arguments_syntax(wrapper)
        ret_val += self._render_one_line_description(wrapper)
        ret_val += self._render_arguments(wrapper)
        ret_val += self._render_long_description(wrapper)
        return ret_val

    def _render_arguments_syntax(self,
                                 wrapper: textwrap.TextWrapper) -> list:
        syntax = self.arguments_syntax
        if not syntax:
            syntax = "<none>"
        return wrapper.wrap("Arguments: " + syntax)

    def _render_one_line_description(self, wrapper):
        return wrapper.wrap(self.one_line_description)

    def _render_arguments(self, wrapper):
        ret_val = []
        for (identifier, description) in self.arguments:
            ret_val += wrapper.wrap(identifier + " - " + textwrap.dedent(description))
        return ret_val

    def _render_long_description(self, wrapper):
        if self.long_description:
            return wrapper.wrap(textwrap.dedent(self.long_description))
        else:
            return []


class ArgparseParserHelpTextMixin:

    SUB_COMMAND_DETAILS_INDENT = "  "

    @staticmethod
    def string_as_lines(wrapper: textwrap.TextWrapper,
                        lines_string: str):
        return [wrapper.initial_indent + line
                for line in lines_string.splitlines()]

    @staticmethod
    def string_as_lines_add_indent_to_non_first_line(wrapper: textwrap.TextWrapper,
                                                     lines_string: str):
        lines = lines_string.splitlines()
        ret_val = []
        if lines:
            indent = wrapper.initial_indent
            ret_val.append(wrapper.initial_indent +
                           lines[0])
            indent += InstructionDescriptionForInstructionWithSubCommands.SUB_COMMAND_DETAILS_INDENT
            ret_val.extend([indent + line
                            for line in lines[1:]])
        return ret_val


class InstructionDescriptionForInstructionWithArgparseParser(InstructionDescription, ArgparseParserHelpTextMixin):

    def __init__(self,
                 parser: InstructionWithArgparseArgumentParser):
        self._parser = parser

    def render_as_lines(self,
                        wrapper: textwrap.TextWrapper) -> list:
        return self.string_as_lines(wrapper,
                                    self._parser.arg_parser().format_help())


class InstructionDescriptionForInstructionWithSubCommands(InstructionDescription, ArgparseParserHelpTextMixin):
    """Detailed description of an instruction that has sub commands."""

    def __init__(self,
                 parser: InstructionWithSubCommandsArgumentParser):
        self._parser = parser

    def render_as_lines(self,
                        wrapper: textwrap.TextWrapper) -> list:
        ret_val = self.string_as_lines(wrapper,
                                     self._parser.arg_parser().format_help())
        for sub_command in sorted(self._parser.sub_command_parsers().keys()):
            ret_val.extend([""])
            arg_parser = self._parser.sub_command_parsers()[sub_command]
            ret_val.extend(self.string_as_lines_add_indent_to_non_first_line(wrapper,
                                                                             arg_parser.format_help()))

        return ret_val

    @staticmethod
    def string_as_lines(wrapper: textwrap.TextWrapper,
                        lines_string: str):
        return [wrapper.initial_indent + line
                for line in lines_string.splitlines()]

    @staticmethod
    def string_as_lines_add_indent_to_non_first_line(wrapper: textwrap.TextWrapper,
                                                     lines_string: str):
        lines = lines_string.splitlines()
        ret_val = []
        if lines:
            indent = wrapper.initial_indent
            ret_val.append(wrapper.initial_indent +
                           lines[0])
            indent += InstructionDescriptionForInstructionWithSubCommands.SUB_COMMAND_DETAILS_INDENT
            ret_val.extend([indent + line
                            for line in lines[1:]])
        return ret_val


class InstructionConfiguration:
    """Complete information about an instruction."""

    def __init__(self,
                 long_name: str,
                 name_aliases: list,
                 description: InstructionDescription,
                 argument_parser: InstructionArgumentParser):
        self.long_name = long_name
        self.name_aliases = name_aliases
        self.description = description
        self.argument_parser = argument_parser

    @staticmethod
    def for_instruction_with_sub_commands(name_aliases: list,
                                          argument_parser: InstructionWithSubCommandsArgumentParser):
        return InstructionConfiguration(argument_parser.instruction_name,
                                        name_aliases,
                                        InstructionDescriptionForInstructionWithSubCommands(argument_parser),
                                        argument_parser)

    @staticmethod
    def for_instruction_with_argparser(name_aliases: list,
                                       argument_parser: InstructionWithArgparseArgumentParser):
        return InstructionConfiguration(argument_parser.instruction_name,
                                        name_aliases,
                                        InstructionDescriptionForInstructionWithArgparseParser(argument_parser),
                                        argument_parser)

    def render_as_lines(self,
                        wrapper: textwrap.TextWrapper) -> list:
        """Renders the description as a list of lines."""
        saved_initial_indent = wrapper.initial_indent
        ret_val = []
        ret_val += self._render_name_line(wrapper)
        wrapper.initial_indent = wrapper.subsequent_indent
        ret_val += self.description.render_as_lines(wrapper)
        wrapper.initial_indent = saved_initial_indent
        ret_val += [""]
        return ret_val

    def _render_name_line(self, wrapper):
        return wrapper.wrap(self.long_name + " " + str(self.name_aliases))


description_of_print = InstructionDescriptionExplicit(
    "Outputs the argument.",
    "[STRING]",
    [("STRING",
     """\
     String to be printed.
     Extends to the end of line.
     Comment characters are not treated as comments, but is
     included in the printed string.
     """)
     ],
    """\
    If STRING is not given, then an empty line is printed.
    """
)

description_of_shell = InstructionDescriptionExplicit(
    "Retrieve file names by executing a shell command.",
    "COMMAND-LINE",
    [("COMMAND-LINE",
     """\
     A command line passed to, and executed by the shell.
     """)
     ],
    """\
    Gives the contents of the line following the instruction name
    to the shell for execution.
    Each line of the output from this command is treated as if
    it was a file-path on a line of the list-file itself.
    """
)

blank_line = ""

description_header_of_program_paragraphs = [
    "Prints a list of file-paths given list-files containing file-path specifications.",
    "",
    """\
    This is a tool for maintaining a distributed list of files
    that can be accessed via one ore more top level list-files.
    """,
    blank_line,
    """\
    The printed paths are all relative the same location - the
    current working directory,
    so that they can be easily accessed.
    """,
    blank_line,
    """\
    A file-path specification is just a file-name that is relative the
    location of the list-file.
    """,
    """\
    The file-path specifications can be distributed across several list-files,
    via an inclusion instruction. The file-paths in each
    included list-file is relative the location of the included list-file.
    """,
    blank_line,
    """\
    File-path can be "tagged" via a special instruction (see below).
    Via options the program can be set to output only files who's tags
    match a given condition.
    """,
    blank_line,
    "A list-file is line oriented.",
    "There are three types of lines:",
    "1. ignored (white-space or comment)",
    "2. instruction",
    "3. file-path specification",
    blank_line,
    """\
    Comments begin with a # and continue to the end of line.
    The # may be preceded by any sequence of white-space.
    """,
    blank_line,
    "Comments are only allowed on comment lines (i.e., not at the end of lines).",
    blank_line,
    "An instruction has the form: @INSTRUCTION_NAME [ARGUMENT...]",
    "Instruction lines may not contain comments.",
    """\
    INSTRUCTION_NAME is case insensitive, and may have one or more aliases.
    """,
    """\
    The syntax and meaning of ARGUMENT depend on the instruction.
    """,
    "(Below is a list of instructions.)",
    blank_line,
    "A file-path specification is just the file-path itself.",
    "The path is relative the location of the list-file it appears in.",
    blank_line,
    "NOTES",
    """\
    1. This program is designed to only work with file names
    that does not contain new-lines.
    """,
    blank_line,
    """\
    instructions:
    """
]


def system_line_parsers(instruction_prefix: str):
    return [LineParserForIgnoredLine(),
            LineParserForInstruction(instruction_prefix),
            LineParserForFilePath()]


instruction_configurations = [
    InstructionConfiguration.for_instruction_with_argparser(
        ["F"],
        InstructionArgumentParserForFind("FIND")),
    InstructionConfiguration.for_instruction_with_argparser(
        ["I"],
        InstructionArgumentParserForInclude("INCLUDE")),
    InstructionConfiguration.for_instruction_with_argparser(
        ["L", "LS"],
        InstructionArgumentParserForDirectoryListing("LIST")),
    InstructionConfiguration(
        "PRINT",
        ["P"],
        description_of_print,
        InstructionArgumentParserForPrint()),
    InstructionConfiguration(
        "SHELL",
        [],
        description_of_shell,
        InstructionArgumentParserForShell()),
    InstructionConfiguration.for_instruction_with_sub_commands(
        ["T"],
        InstructionArgumentParserForTags("TAGS")),
]


def instruction_configurations_lines(wrapper: textwrap.TextWrapper) -> list:
    lines = []
    for i_config in instruction_configurations:
        lines += i_config.render_as_lines(wrapper)
    return lines


def program_description():
    top_level_wrapper = textwrap.TextWrapper(initial_indent="",
                                             subsequent_indent="")

    instruction_wrapper = textwrap.TextWrapper(initial_indent="  ",
                                               subsequent_indent="    ")

    lines = []
    for paragraph in description_header_of_program_paragraphs:
        if paragraph:
            lines += top_level_wrapper.wrap(textwrap.dedent(paragraph))
        else:
            lines.append(os.linesep)
    lines += instruction_configurations_lines(instruction_wrapper)
    return os.linesep.join(lines)


def instruction_identifier_to_parser_dict() -> dict:
    """
    Gives a dictionary with mappings for all valid instruction identifiers -
    long names and aliases.

    Returns a dict : INSTRUCTION-IDENTIFIER -> InstructionArgumentParser
    """
    ret_val = {}
    for i_conf in instruction_configurations:
        ret_val[i_conf.long_name] = i_conf.argument_parser
        for alias in i_conf.name_aliases:
            ret_val[alias] = i_conf.argument_parser
    return ret_val


###############################################################################
# - main -
###############################################################################


def error_header_line(s: str):
    return os.path.basename(__file__) + ": " + s


def exit_usage(msg: str):
    write_lines(sys.stderr,
                [error_header_line(msg)])
    sys.exit(EXIT_USAGE)


class CommandLineParseResult:

    def __init__(self,
                 command: Command,
                 instruction_prefix: str,
                 file_names: list,
                 forward_tags: bool,
                 stdin_paths_are_relative_or_empty: list,
                 tags_condition: TagsCondition,
                 file_existence_handling_settings: FileExistenceHandlingSettings,
                 rendition_settings: RenditionSettings,
                 preprocessor_shell_command: str):
        self.command = command
        self.instruction_prefix = instruction_prefix
        self.file_names = file_names
        self.forward_tags = forward_tags
        self.stdin_paths_are_relative_or_empty = stdin_paths_are_relative_or_empty
        self.file_existence_handling_settings = file_existence_handling_settings
        self.tags_condition = tags_condition
        self.rendition_settings = rendition_settings
        self.preprocessor_shell_command = preprocessor_shell_command

    def exit_if_invalid(self):
        """
        Performs some (rather arbitrary) checks of values,
        and exits if an error is found.
        """

        self.check_stdin_is_given_at_most_once()
        self.check_instruction_prefix()

    def check_stdin_is_given_at_most_once(self):
        stdin_list = list(filter(lambda x: x == COMMAND_LINE_ARGUMENT_FOR_STDIN,
                                 self.file_names))
        if len(stdin_list) > 1:
            exit_usage("stdin ('" +
                       COMMAND_LINE_ARGUMENT_FOR_STDIN +
                       "') as file argument can be given at most once.")

    def check_instruction_prefix(self):
        if LineParserForIgnoredLine.is_comment_line(self.instruction_prefix):
            exit_usage("The instruction prefix may not match as a comment line.")


def parse_tags_condition(tags_condition_setup: TagsConditionSetup,
                         right_operand_or_empty: list,
                         operator_name: str,
                         negate_operator: bool) -> TagsCondition:

    if right_operand_or_empty:
        operand_string = right_operand_or_empty[0]
        if operand_string and not operand_string.isspace():
            r = frozenset(parse_tags_list(operand_string))
        else:
            r = frozenset()
        return tags_condition_setup.condition_for(operator_name,
                                                  negate_operator,
                                                  r)
    else:
        return tags_condition_setup.for_no_condition()


def format_operator_str(operator_name):
    parts = [operator_name]
    aliases = TagsConditionSetup.OPERATORS[operator_name].aliases
    if aliases:
        parts.append("(alias: " + ", ".join(aliases) + ")")
    return " ".join(parts)


def filter_tags_operators_list_for_help_text():
    return ", ".join([format_operator_str(o)
                      for o in sorted(TagsConditionSetup.OPERATORS.keys())])


def parse_command_line() -> CommandLineParseResult:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=program_description())
    filter_tags_long_option = "--filter-tags"
    filter_tags_operator_long_option = "--operator-for-filter-tags"
    filter_tags_negate_operator_long_option = "--negate-operator-for-filter-tags"
    tags_condition_setup = TagsConditionSetup()
    all_filter_operator_names = tags_condition_setup.all_operator_names()

    stdin_paths_are_relative_long_option = "--stdin-paths-are-relative"

    file_existence_handling_mode_parser = FileExistenceHandlingModeOptionParser()

    parser.add_argument("files",
                        metavar="FILE",
                        nargs="*",
                        help="""A list-file.
                        '-' means stdin. '-' can be used at most once.
                        File-paths from stdin are assumed to be relative the current working directory,
                        unless """ +
                        stdin_paths_are_relative_long_option +
                        """ is used. """)
    parser.add_argument("--instruction-prefix",
                        nargs=1,
                        default=[DEFAULT_INSTRUCTION_PREFIX],
                        help="""\
                        Sets the prefix for lines that contain an instruction
                        (as opposed to file-paths).

                        The default is """ + DEFAULT_INSTRUCTION_PREFIX + ".")
    parser.add_argument("-m", "--missing-file-handling",
                        metavar="MODE",
                        dest="file_existence_mode",
                        nargs=1,
                        choices=file_existence_handling_mode_parser.mode_keys(),
                        default=[file_existence_handling_mode_parser.default_key()],
                        help="""\
                        Determines how file-paths that do not correspond to an existing
                        file are handled.

                        The default mode is """ +
                        in_double_quotes(file_existence_handling_mode_parser.default_key()) +
                        """. List of modes: """ +
                             file_existence_handling_mode_parser.keys_help_text())
    parser.add_argument("-f", "--relative-file-argument-location",
                        default=False,
                        action="store_true",
                        help="""\
                        File-paths are relative the location of the FILE argument.
                        Without this option, file names are relative
                        the location of the invocation of the program.
                        """)
    parser.add_argument("-n", "--normalize-paths",
                        default=False,
                        action="store_true",
                        help="""\
                        Normalizes paths.
                        E.g.: A//B, A/B/, A/./B and A/foo/../B all become A/B.
                        This string manipulation may change the meaning of
                        a path that contains symbolic links.
                        """)
    parser.add_argument("-a", "--absolute-paths",
                        default=False,
                        action="store_true",
                        help="""\
                        Make paths absolute = non-relative.
                        Paths start with a "/".
                        """)
    parser.add_argument(stdin_paths_are_relative_long_option,
                        metavar='DIR',
                        nargs=1,
                        help="""\
                        Specifies the directory which paths read from stdin should be relative to.

                        The default is the current working directory.
                        """)
    parser.add_argument("-S", "--suppress-non-path-output",
                        default=False,
                        action="store_true",
                        help="""\
                        Suppresses all output other than file-paths.
                        E.g., PRINT instructions will have no effect.
                        """)
    parser.add_argument("-t", "--prepend-tags",
                        default=False,
                        action="store_true",
                        help="""\
                        For each file, print it's tags before it.
                        The tags and the path are separated by \"""" +
                        TagsRenditionSettings.DEFAULT_TAGS_AND_PATH_SEPARATOR + "\"")
    parser.add_argument("-T", "--append-tags",
                        default=False,
                        action="store_true",
                        help="""\
                        For each file, print it's tags after it.
                        The tags and the path are separated by \"""" +
                        TagsRenditionSettings.DEFAULT_TAGS_AND_PATH_SEPARATOR + "\"")
    parser.add_argument("-F", filter_tags_long_option,
                        metavar="SET-OF-TAGS",
                        nargs=1,
                        help="""\
                        A set of tags.
                        Tags are separated by white space and commas.
                        Empty tags are ignored.

                        Output only those file-paths who's tags satisfy
                        a condition with the given set of tags. """ +
                        filter_tags_operator_long_option +
                        " and " + filter_tags_negate_operator_long_option +
                        """ determines how this set is used in the condition.""")
    parser.add_argument("-O", filter_tags_operator_long_option,
                        metavar="SET-OPERATOR",
                        nargs=1,
                        choices=all_filter_operator_names,
                        default=[TagsConditionSetup.DEFAULT_OPERATOR_NAME],
                        help="""\
                        The operator that is used by the tags-filter.
                        It is applied as <FILE-TAGS> SET-OPERATOR <TAGS-FROM-FILTER>,
                        where <FILE-TAGS> are the tags associated with
                        the file-path in the list;
                        and <TAGS-FROM-FILTER> is the tags specified by """ +
                        filter_tags_long_option + """.

                        """ + filter_tags_negate_operator_long_option +
                        """ negates the meaning of the operator.

                        Note that the tags filter is only applied if """ +
                        filter_tags_long_option + """
                        is given.
                        The default operator is """ +
                        TagsConditionSetup.DEFAULT_OPERATOR_NAME +
                        """.

                        Operators are: """ + filter_tags_operators_list_for_help_text() +
                        """.""")
    parser.add_argument("-N", filter_tags_negate_operator_long_option,
                        default=[],
                        const=None,
                        action="append_const",
                        help="""\
                        Negates the filter tags condition.

                        May be used multiple times.

                        This is useful if the all file-paths needs to be handled,
                        but the handling depends on weather the file-path satisfies
                        the filter or not. (Note that the program must be executed two times
                        for this.)""")
    parser.add_argument("--forward-tags",
                        default=False,
                        action="store_true",
                        help="""\
                        The current tags at the end of a file on the command line,
                        is forwarded to the following file on the command line.""")
    parser.add_argument("--preprocessor",
                        metavar="PROCESSOR",
                        nargs=1,
                        help="""\
                        Process each file-list with the given processor, before it is interpreted as a list-file.
                        Both files on the command line and files included by the include-instruction are pre-processed.
                        The processor is given the list-file via stdin, and must output it's result
                        on stdout.""")
    parser.add_argument("-i", "--print-inclusion-hierarchy",
                        action="store_const",
                        dest="command",
                        const=PrintInclusionHierarchyCommand(TreePrinterForSimpleLayout(), False, False),
                        default=ProgramMainFunctionalityCommand(),
                        help="""\
                        Prints the file inclusion hierarchy.
                        The normal output is suppressed.""")
    parser.add_argument("-I", "--print-inclusion-hierarchy-pretty",
                        action="store_const",
                        dest="command",
                        const=PrintInclusionHierarchyCommand(TreePrinterForPrettyLayout(), True, True),
                        help="""\
                        Prints the file inclusion hierarchy,
                        in a pretty layout.
                        The normal output is suppressed.""")
    parser.add_argument("--version",
                        action="version",
                        version="%(prog)s " + program_info.VERSION_STRING)
    args = parser.parse_args()
    tags_condition = parse_tags_condition(tags_condition_setup,
                                          args.filter_tags,
                                          args.operator_for_filter_tags[0],
                                          (len(args.negate_operator_for_filter_tags) % 2) == 1)
    file_existence_handling_settings = file_existence_handling_mode_parser.lookup(args.file_existence_mode[0])
    rendition_settings = RenditionSettings(args.relative_file_argument_location,
                                           file_existence_handling_settings.include_existing_in_output,
                                           file_existence_handling_settings.include_non_existing_in_output,
                                           args.normalize_paths,
                                           args.absolute_paths,
                                           TagsRenditionSettings(args.prepend_tags,
                                                                 args.append_tags),
                                           args.suppress_non_path_output)
    return CommandLineParseResult(args.command,
                                  args.instruction_prefix[0],
                                  args.files,
                                  args.forward_tags,
                                  args.stdin_paths_are_relative,
                                  tags_condition,
                                  file_existence_handling_settings,
                                  rendition_settings,
                                  args.preprocessor)


def main():
    parse_result = parse_command_line()
    parse_result.exit_if_invalid()
    try:
        parse_result.command.execute(parse_result.file_names,
                                     parse_result.forward_tags,
                                     parse_result.stdin_paths_are_relative_or_empty,
                                     parse_result.file_existence_handling_settings.program_should_fail_on_non_existing,
                                     parse_result.tags_condition,
                                     parse_result.rendition_settings,
                                     ParsingSettings(parse_result.preprocessor_shell_command,
                                                     system_line_parsers(parse_result.instruction_prefix),
                                                     instruction_identifier_to_parser_dict()))
    except InstructionSyntaxErrorException as ex:
        ex.render(sys.stderr)
        sys.exit(EXIT_SYNTAX)

    except ResultItemConstructionExceptionBase as ex:
        ex.render(sys.stderr)
        sys.exit(ex.exitCode)

    except PreprocessorException as ex:
        ex.render(sys.stderr)
        sys.exit(EXIT_PRE_PROCESSING)
