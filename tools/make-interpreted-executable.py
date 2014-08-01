# -*- coding: utf-8 -*-


import sys
import os
import stat
import argparse


program_description = """\
    Constructs an executable file that is executed by an interpreter.

    The executable is constructed by concatenating the parts of it.

    The first part must be a part that contains the operating systems special
    instruction to interpret the file using the specified interpreter.
"""

EXEC_MODE = stat.S_IRUSR | stat.S_IWUSR |\
            stat.S_IXUSR | stat.S_IRGRP |\
            stat.S_IWGRP | stat.S_IXGRP |\
            stat.S_IROTH | stat.S_IXOTH


class AnError(Exception):
    def __init__(self,
                 msg: str):
        Exception.__init__(self)
        self._msg = msg

    def msg(self) -> str:
        return self._msg


class Action:
    def apply(self,
              file):
        raise NotImplementedError()


class AppendInterpreterAction(Action):
    def __init__(self,
                 interpreter: str):
        self._interpreter = interpreter

    def apply(self,
              file):
        file.write("#! ")
        file.write(self._interpreter)
        file.write(os.linesep)


class AppendSourceAction(Action):
    def __init__(self,
                 file_name: str):
        self._file_name = file_name

    def apply(self,
              file):
        source_file = open(self._file_name)
        file.writelines(source_file.readlines())
        source_file.close()


class Instructions:
    def __init__(self,
                 output: str,
                 interpreter: str,
                 sources: list):

        if not output:
            raise AnError("No output file specified.")

        if not interpreter:
            raise AnError("No interpreter file specified.")

        self._output = output

        self._actions = []
        self._actions.append(AppendInterpreterAction(interpreter))
        for source in sources:
            self._actions.append(AppendSourceAction(source))

    def actions(self) -> list:
        return self._actions

    def output_file_name(self) -> str:
        return self._output


def parse_command_line() -> Instructions:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=program_description)

    parser.add_argument("-i", "--interpreter",
                        metavar="INTERPRETER",
                        nargs=1,
                        default=[None],
                        help="""The absolute path of the interpreter
                        that should interpret the constructed file.""")
    parser.add_argument("-o", "--output",
                        metavar="FILE",
                        default=[None],
                        nargs=1,
                        help="""The name of the executable to be constructed.""")
    parser.add_argument("-s", "--source",
                        metavar="FILE",
                        nargs=1,
                        action="append",
                        dest="sources",
                        default=[],
                        help="""The name of a source file that should be part of the executable.""")
    args = parser.parse_args()

    return Instructions(args.output[0],
                        args.interpreter[0],
                        [s[0] for s in args.sources])


def construct(instructions: Instructions):
    output_file = open(instructions.output_file_name(),
                       mode="w")
    for action in instructions.actions():
        action.apply(output_file)
    output_file.close()
    os.chmod(instructions.output_file_name(),
             EXEC_MODE)


def main():
    try:
        instructions = parse_command_line()
        construct(instructions)
    except AnError as ex:
        sys.stderr.write(__file__)
        sys.stderr.write(": ")
        sys.stderr.write(ex.msg())
        sys.stderr.write(os.linesep)
        sys.exit(2)


main()
