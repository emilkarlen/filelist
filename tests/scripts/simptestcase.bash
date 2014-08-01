# -*- shell-script -*-

###############################################################################
# Copyright (C) 2007  Emil Karlén (email: emilkarlen@aim.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
###############################################################################

PRJ_BIN_DIR=
PRJ_TOP_DIR=

###############################################################################
#
# --- EXTERNAL PROGRAMS USED (dependencies)
#
# For normal use:
#
#   * getopt
#   * mkdir
#   * cd
#   * ex
#   * cp
#   * find
#   * stat
#   * sort
#   * m4
#   * diff
#   * xmldiff
#
# For testing, also these:
#
#   * tee (used in testcase files)
#   * uniq
#
#
# --- FUNKTIONER
#
#
# *** showMsgStep...
#
#   Funktioner som visar ett meddelande om ett steg i testningen. Information
# om varje sådant steg ska loggas i loggfilerna för stdout och stderr.
#
# *** showMsgParse...
#
#   Funktioner som visar ett meddelande om parsningen av testfallsfilen.
# Loggningen ska ske till 'parse-testcase.logg'.
#
#
# --- VARIABLER
#
#
# *** sPgmXmldiff
#
#  A program that compares two xml files.  Exits with 0 if the files are
# identical, non-zero otherwise.
#
# - STRUKTURER
#
#   I flera fall behövs listor av program där ett program är ett sådant som kan
# anges i testfallsfilen. Ett sådant program har tre attribut:
#     * Type
#        enum:
#           * 'cmdline' (en kommandorad)
#           * 'interpret.source' (för typen interpret.source)
#           * 'interpret.file' (för typen interpret.file)
#           * 'REPLACE-ENVVARS' (enbart för check.prepare), programmet
#             för att byta ut värdena hos omgivningsvariabler som simptestcase
#             sätter.
#     * Interp
#        Används bara om Type='source'. Då lagras här interpretatorn som ska
#        användas för att interpretera den givna källkoden.
#     * Cmd
#        Om Type=cmdline: kommandoraden, det som kommer efter (sista) kolonet.
#        Om Type=source: källkodsfilen (absolut sökväg).
#
#   Här är en standard för att använda sådana listor: En lista består av tre
# array-variabler, en för varje attribut. Variablernas namn har ett gemensamt
# prefix, t ex "apgmTestRun". Svansen på namnet utgörs av attributens namn.
# attribut.
#   Indexen för elementen i listan fås genom att titta på ...Type. De andra
# attributen kan vara tomma för index som finns i ...Type (men så klart
# syntaktiskt korrekta).
#
#
# - VARIABLER SOM MOTSVARAR DATA KOMMANDORADSARGUMENTEN
#
#
# *** sPgmXmldiff
#
#
# *** bM4
#
#   If m4 preprocessing should be done.
#
# *** wslM4_options
#
#   Options to pass to m4 if m4 preprocessing should be done.
# Initialized to '--prefix-builtins --fatal-warnings'.
#
#
# - VARIABLER SOM MOTSVARAR DATA FRÅN TESTFALLSFILEN
#
#
# *** dirHome
#
#   =home
#
# *** sApplication
#
#   =application
#
# *** sName
#
#   =name
#
# *** aSetupInstall_src
# *** aSetupInstall_dst
#
#   =setup.install
#
# *** apgmSetupRun_Type
# *** apgmSetupRun_Interp
# *** apgmSetupRun_Cmd
#
#   =setup.run
#
# *** apgmPrecondType
# *** apgmPrecondInterp
# *** apgmPrecondCmd
#
#   =precond
#
# *** apgmTestRunType
# *** apgmTestRunInterp
# *** apgmTestRunCmd
#
#   =test.run
#
# *** apgmCheckPrepareType
# *** apgmCheckPrepareInterp
# *** apgmCheckPrepareCmd
# *** apgmCheckPrepareFlags
# *** apgmCheckPrepareArg1
#
#   =check.prepare
#
#   'apgmCheckPrepareFlags' and 'apgmCheckPrepareArg1' are used only for
# check.prepare.replace_SIMPTEST_envvars. Then they are set to the flags and
# argument#1, respectively.
#
# *** apgmCheckCustomType
# *** apgmCheckCustomInterp
# *** apgmCheckCustomCmd
#
#   =check.run
#
# *** aEnvCmds
#
#   =env
#   En array av kommandon som ska utföras innan testet körs, men efter att
#   simptestcases miljövariabler satts, för att sätta värden på miljövariabler.
#
# *** uieCheckExitCode
#
#  Unsigned Int Expression.
#  Initializeras till tomma värdet, vilket indikerar att kontrollen ska
#  hoppas över.
#  Börjar den med ! innebär testet INTE.
#  =check.exitcode.
#
# *** fileTestStdin
#
#  =test.stdin or /dev/null, if not set using test.stdin.
#
# *** fileCheckStdout, checktypeCheckStdout, flagsCheckStdout
#
#  =check.stdout[.empty].
#   checktypeCheckStdout anger vilken typ av kontroll som ska göras för
#   utdata från 'stdout':
#     tom - ingen kontroll
#     'empty'   - kontrollera att utan är tom.
#     'only-ws' - kontrollera att filen enbart innehåller white space (enl IFS)
#     'file'    - kontrollera att innehållet är det samma som innehållet i
#                 filen med namnet 'fileCheckStdout'.
#   'flagsCheckStdout' contains the flags. The only valid flag is 'replaced'.
#
# *** fileCheckStderr, checktypeCheckStderr,flagsCheckStderr
#
#  =check.stderr[.empty].
#   Se check.stdout!
#
# *** check_channel__{channel,checkType,lFlags,file}
#
#   =check.{stdout,stderr}
#
#   check_channel__channel[<idx>] is mandatory, so use it to retrieve the
#   used indexes.
#     * checkType - Type of check to perform.
#         - 'EMPTY'           - Check that the file is empty.
#         - 'WHITESPACE-ONLY' - Check that the contents is whitespace only.
#         - 'FILE'            - Check that the contents is the same as that
#                               of a named file.
#                               The name of the file is in
#                               check_channel__file[].
#
# *** aCheckCmpEq_Flags
# *** aCheckCmpEq_Src
# *** aCheckCmpEq_Dst
#
#  =check.compare.eq/flags:src:dst
#
# Note! aCheckCmpEq_Src is set to an ABSOLUT path by parseTestCase.
#       During the execution of the test - it must be checked for existance.
#
#
# - INTERNA VARIABLER
#
#
# *** bTest
#   Anger om programmet körs i testläge (test av sig självt) eller ej.
#
# *** cmdTest
#   Om programmet körs i testläge (bTest satt) anger den här variabeln vilket
#   testkommando som ska utföras.
#
# *** dirDataStd
#   Katalogen under temporära testroten där utdata från testprogrammet lagras.
#
# *** dirDataSources
#  Katalogen under temporära testroten där källkod för interpret.source-program
#  lagras.
#
# *** fileTestCase
#   Testfallsfilen eller "-" för /dev/stdin för stdin.
#
# *** TMP_ROOT
#   Rotkatalogen för temporära filer för testet.
#
# *** fileLoggOut,fileLoggErr
#   Namnen på loggfilerna för utdata från programmen till stdout respektive
#   stderr.
#
# *** fileLoggParseTc
#   Namnet på loggfilen för parsningen av testfallsfilen.
#
#
# --- KONSTANTER
#
#
# *** VERSION
#  Programmets versionsnummer. Skrivs ut med växeln --version.
#
#
# *** bKeep
#  Om testkatalogen ska lämnas kvar.
#
# *** bDebugPrint
#
#   If the output from the test commands should be printed (which
# meands that the execution of the commands should stop after these are
# executed - no checks are preformed, but cleanup is).
#
# *** bPrintLogs
#
#   If the contents of the logs should be printed to stdout and stderr as
#   program output instead of normal output.
#
# *** sUsage
#  Beskriver kommandots syntax.
#
# *** sLoggStepHdr
#  Formatsträng för 'printf' som används för att skriva rubriken för varje
#  steg i testet till loggfilerna. Innehåller både text och %s:ar.
#
# *** bAppendName  - Om testfallets namn ska skrivas på stdout.
# *** bVerb        - Set if verbal (or very verbal).
# *** bVerbVerb    - Set if very verbal.
# *** dirLoggsRoot - Om satt om loggar ska sparas, då är detta spara-katalogen.
# *** sTestProcId  - text som unikt identifierar testkörningen (=datum+PID ...)
#  Ska kunna användas i filnamn.
# *** sTestCaseId  - text som unikt identifierar testfallet (app+name ...)
#  Ska kunna användas som katalognamn.
#
# *** ifsOrig  - orginalvärdet för IFS. lagras för att kunna återställa IFS.
#
# *** exitkoder
#  * EXIT_CL_SYNTAX - fel användning
#  * EXIT_INTERNALERR - internt fel
#  * EXIT_FILE
#      En angiven fil finns inte. kan vara testfallsfilen som anges på
#      kommandoraden eller någon fil som refereras från testfallsfilen.
#  * EXIT_PARSE
#      Syntaxfel i testfallsfilen.
#  * EXIT_NONTEST_ERROR
#      Något av hjälpprogrammen avslutades med en felkod.
#  * EXIT_FAIL
#      Den returkod som returneras när ett test misslyckats.
#  * EXIT_PRECOND
#      Den returkod som returneras när ett testet misslyckas - inte kan utföras
#      - därför att ett precond-program returnerar falskt.
#  * PREPROCESSING_ERROR
#      The exist code returned when the program exits because of a non
#      successful preprocessing command.
#  * EXIT_SUCCESS
#      Den returkod som returneras när ett test lyckats.
#
###############################################################################

readonly sUsage='[-4egknvV] [LONGOPTION...] {<testcase file>|-}'

readonly sLoggStepHdr='------------------------------------------------------------
- %s
------------------------------------------------------------\n'

readonly msgInvalidTestUsage="Invalid test usage.
Try \`simptestcase -- test: --help' for help.\\n"
readonly msgTestHelp='Run the program for testning.
  --help  Show this help and exit.
  -c test-command
          Run specified test command. Possible tests commands are:
          env
            For each environment variable set by the testcase, print a line
            var=val
            where "var" is the name of the variable and "val" it'"'"'s value.
            The output is sorted by "var".
          env-cmds
            Print the shell commands constructed to set environment variables.
          m4
            If m4 preprocessing is used, this runs m4.  Otherwise, do nothing.
          stop-after-parse
            Exit successfully if the parsing of the testcase is successfull,
            owtherwise with an error. If successfull, no output is produced,
            if not, ouput may be generated to stderr.
          stop-after-setup
            Quit after the setup, just before the test should be run.
            This command does not autmatically keep the files in the
            test directory structure. Combine this testcommand with -k to do
            that!
          programs
            Print information about all programs read from the testcase file.
          print-check-compare-eq-flags
            Execute everything until check.compare.eq, then print the flags and
            exit.
'
readonly msgInvalidTestCommand='invalid test command:%s\n'
readonly cslTestCommands='m4,env,env-cmds,programs,stop-after-parse,stop-after-setup,print-check-compare-eq-flags'

readonly VERSION='simptestcase 2.2.4'

readonly EXIT_SUCCESS=0
readonly EXIT_CL_SYNTAX=1
readonly EXIT_FAIL=2
readonly EXIT_FILE=3
readonly EXIT_PARSE=4
readonly EXIT_PRECOND=5
readonly EXIT_NONTEST_ERROR=6
readonly EXIT_INTERNALERR=7
readonly PREPROCESSING_ERROR=8
readonly ifsOrig="$IFS"

sPgmXmldiff='xmldiff'

###############################################################################
# - doExit -
#
#   Avsluta programmet på korrekt vis, dvs radera det som ska raderas och
# spara det som ska sparas.
###############################################################################
function doExit # EXITCODE
{
    saveLoggs
    cleanupTestDirs
    exit ${1}
}

function showMsgInternalError # <step> <function> <msg>
{
    showMsgStepFinish 'INTERNAL ERROR' "$1" "internal error in function $2: $3"
}

###############################################################################
# -- printfExit<N> --
#
#   Prints a message and exists with code <N>.
#   All arguments are passed to `printf' for printing.
###############################################################################

function printfExit0
{
    printf "$@"
    exit 0
}

function printfExit1
{
    printf "$@"
    exit 1
}

#
# Visar felmeddelande om fel användning ("invokering") och avslutar.
#
function exitMsgInvoc # <msg>
{
    echo $(basename $0)":$1" >&2
    exit $EXIT_CL_SYNTAX
}

#
#   Visar ett meddelande som har med exekveringen av själva simptest att göra.
# T ex att det inte går att spara loggar därför att loggkatalogen är
# skrivskyddada.
#
function showMsgExecution # <msg>
{
    echo "$1" >&2
}

function showMsgCheckFail # <msg>
{
    [ "$bVerb" ] && echo "parsing testcase/checking:$1" >&2
    echo "$1" >> "$fileLoggParseTc"
}

function showMsgParseErr # <msg>
{
    [ "$bVerb" ] && echo "parsing testcase:$1" >&2
    echo "$1" >> "${fileLoggParseTc}"
}

function showPreprocessStepStart # any number of arguments
{
    local sMsg="preprocessing"
    if [ "${bVerb}" ]; then
	echo ${sMsg} >&2
    fi
    echo ${sMsg} >> "${fileLoggParseTc}"
}

function showMsgParseErrNotUInt # <value>
{
    showMsgParseErr "not an unsigned int:$1"
}

function showMsgParseErrNotFile # <file-name>
{
    showMsgParseErr "not a file:$1"
}

function showMsgParseErrMissingArgFor
{
    showMsgParseErr "missing argument for:$1"
}

function showMsgParseErrNotDir # <dir-name>
{
    showMsgParseErr "not a dir:$1"
}

function showMsgParseErrNotProgram # <thing-that-should-be-a-program>
{
    showMsgParseErr "not a program (use cmdline|cmdline/prepend-home):$1"
}

###############################################################################
# - showMsgStep -
#
# Arg: olika argument beroende på första argets. värde.
#  * BEGIN   <step> <data>
#  * ERROR   <step> <data>
#  * FAIL
#  * SUCCES
#
# A. Create a message of the form $1:$2:$3:...
# B. If "verbose" or "very verbose", print verbose message.
# C. Print normal message to the loggfiles.
###############################################################################
function showMsgStep # <result-string> [<step> <data>]
{
    # A #
    local msg=$(stepMsg "$@")
    # B #
    if [ "$bVerbVerb" ]; then
	printf -- "${sLoggStepHdr}" "${msg}" >&2
    elif [ "$bVerb" ]; then
	echo "${msg}" >&2
    fi
    # C #
    logMsg "${msg}"
}

###############################################################################
#   Constructs a step message that can be logged or printed.
# The message is printed to stdout.
# The message is constrcted by adding all argument separated by a colon:
#    $1:$2:$3...
###############################################################################
function stepMsg # <result-string> [<step> <data>]
{
    local msg="$1"
    shift
    while [ $# != 0 ] ; do
	msg="${msg}:$1"
	shift
    done
    echo "${msg}"
}

function showMsgStepBegin # <step> <data>
{
    showMsgStep "$@"
}

###############################################################################
#   Appends a message to the stdout and stderr log files.
###############################################################################
function logMsg # <msg>
{
    printf -- "${sLoggStepHdr}" "${1}" >> "${fileLoggOut}"
    printf -- "${sLoggStepHdr}" "${1}" >> "${fileLoggErr}"
}

###############################################################################
# - showMsgStepFinish -
#
#   Skriver ut utdata för sista steget i testet, om inte bPrintLogs är satt.
#
# Om tre argument givits betyder det att det tredje argumentet är data som
# kan säga något om felets orsak. Det ska då skrivas ut. Annars skrivs inte
# heller argument#2 - steget - ut, eftersom det redan har skrivits ut en gång
# med 'showMsgStepBegin'.
#
# Användning:
#  * SUCCESS
#  * {PARSE|FILE|NONTEST_ERROR|ERROR|FAIL|PRECOND|INTERNAL ERROR} <step> [<data>]
#
# 0. Return if bPrintLogs is set.
# A. Om vi är i verbalt läge och tre argument givits ska det treje argumentet
#    skrivas ut på stderr.
#    Skriv ut den strängen först så att den hamnar före den sista strängen
#    (om stdout och stderr båda går till samma ström - t ex terminalen).
# B. Skapar strängen som ska skrivas ut på stdout.
#    Strängen är densamma som argument#1 till funktionen. Om -n, dvs
#    'bAppendName' är satt - ska testfallets namn läggs till utdatan.
# C. Skriv ut meddelandet för stdout och loggar det.
#
function showMsgStepFinish # <result-string> [<step> [<data>]]
{
    # 0 #
    if [ -n "${bPrintLogs}" ]; then
	return
    fi
    # A #
    if [ "$bVerb" -a $# = 3 ]; then
	echo "$1:$2:$3" >&2
	data=":$3"
    else
	data=
    fi
    # B #
    local msg="$1"
    [ -n "$bAppendName" ] && msg="${msg}:$sTestCaseId"
    # C #
    echo "${msg}"
    logMsg "${msg}${data}"
}


###############################################################################
# Exits with exitcode ${PREPROCESSING_ERROR}.
# Prints "PREPROCESSING" to stdout and the preprocessing log.
# The arguments are also printed to the log.
###############################################################################
function preprocessError # <msg>
{
    echo 'PREPROCESSING' >> ${fileLoggParseTc}
    echo "${1}" >> ${fileLoggParseTc}
    echo 'PREPROCESSING'
    doExit ${PREPROCESSING_ERROR}
}


###############################################################################
# Tells if the given string WORDS contains _exactly_ the word WORD.
#
# A "word" is any nonempty sequence of non [[:space:]].
# WORDS is a sequence of words, separated by [[:space:]].
###############################################################################
function containsWord # WORDS WORD
{
    eval '[[ "$1" =~ (^|[[:space:]])('"$2"')([[:space:]]|$) ]]'
}


###############################################################################
# As containsword, but words are separated with a comma.
###############################################################################
function containsWordComma # WORDS WORD
{
    eval '[[ "$1" =~ (^|,)('"$2"')(,|$) ]]'
}


###############################################################################
#   Ger den absoluta sökvägen för ett filnamn. Om filnamnet själv börjar med
# / tas det som det är. Gör det inte det prependas dirDot ($1).
###############################################################################
function absFileName # <dirDot> <file-name>
{
    if [ ${2::1} = '/' ]; then
	echo "$2"
    else
	echo "$1/$2"
    fi
}

###############################################################################
# - realpathBash -
#
#   A function for getting an absolute path out of an possibly relative one.
#
#   * If the path does not begin with "/" it is considered to be relative to
# $PWD.
#   * The path must not exist as a file in the filesystem.
#   * Tries to get rid of as many "/." and "/.." as possible.
#
#
# -- CAUTION --
#
#
# * Only tested with 'CDPATH' unset.
# * If the process can't change to a directory, that directory is considered
#   non existing, and the function can do nothing to real-ize it.
#
#
# -- USAGE --
#
#
# * Argument: <path>
#   The function is not tested for paths containing successive slashes -
# directories must be separated by exactly one slash.
# * Exitcode:
#    0 - an path has been obtained and printed on stdout.
#    1 - the path is not semantically meaningful (not because of non-existing
#        files or directories). Nothing has been printed.
#        Example: /..
# * Output: stdout
#    If the path is semantically correct, the "realest" path is printed.
#
#
# -- IMPLEMENTATION --
#
#
#  "e"   ~ exists
#  "n-e" ~ not exists
#
# * p - a path, possibly including both dirname and basename parts.
# * d - dirname (the dirname part of a path)
# * b - basename (the basename part of a path, contains no /-s).
#
# Cases:
#  * A : /..              - ERROR, impossible path
#  * B : e p              - cd p, $PWD
#  * C : n-e b            - $PWD/b
#  * D : n-e /b           - /b
#  * E : n-e d/.          - realpathBash d
#  * F : n-e d/..
#            d2 = realpath d
#             * F.1 : d2 = /      - ERROR, impossible path
#             * F.2 : d2 = /b     - /
#             * F.3 : d2 = d3/..  - d2/.. (we can't do anything about the ..)
#             * F.4 : d2 = d3/b   - d3
#  * G : n-e d/b          - (realpathBash d)/b
#
###############################################################################

function realpathBash
{
    local b d rp_d
    # A #
    if [ "${1}" = '/..' ]; then
	return 1
    fi
    # B #
    pushd . > /dev/null
    if cd "${1}" 2> /dev/null; then
	echo "$PWD"
	popd > /dev/null
	return
    fi

    d=${1%/*}
    # C #
    if [ "${d}" = "${1}" ]; then
	echo "$PWD/${1}"
	return
    fi
    # D #
    if [ -z "${d}" ]; then
	echo "${1}"
	return
    fi

    b=${1#${d}/}
    case "$b" in
    # E #
	.)
	    realpathBash "$d"
	    return
	    ;;
    # F #
	..)
	    if rp_d=$(realpathBash "$d"); then
                # .1 #
		if [ "$rp_d" = '/' ]; then
		    return 1
		fi
                # .2 #
		if [ "${rp_d%/*}" = '' ]; then
		    echo '/'
		    return
		fi
		if [[ "$rp_d" == */.. ]]; then
                # .3 #
		    echo "$rp_d/.."
		    return
		else
                # .4 #
		    echo "${rp_d%/*}"
		    return
		fi
	    fi
	    ;;
    # G #
	*)
	    if rp_d=$(realpathBash "$d"); then
		echo "$rp_d/$b"
		return
	    else
		return 1
	    fi
	    ;;
    esac
}


###############################################################################
#   Creates the test directory structure.
#
# Sets: TMP_ROOT
# Sets: fileLoggOut
# Sets: fileLoggErr
# Sets: fileLoggParseTc
# Sets: dirDataStd
# Sets: dirDataSources
# Sets: dirTestCasePreprocessed
###############################################################################
function mkTestDirs
{
    TMP_ROOT=${SIMPTEST_TMP:-${TMPDIR}}
    TMP_ROOT=${TMP_ROOT:-/tmp}/simptestcase-${sTestProcId}

    mkdir --parents $TMP_ROOT
    mkdir ${TMP_ROOT}/logs
    mkdir ${TMP_ROOT}/data
    mkdir ${TMP_ROOT}/data/std
    mkdir ${TMP_ROOT}/data/custom
    mkdir ${TMP_ROOT}/sources
    mkdir ${TMP_ROOT}/test
    mkdir ${TMP_ROOT}/testcase

    dirDataStd="${TMP_ROOT}/data/std"
    dirDataSources="${TMP_ROOT}/sources"
    dirTestCasePreprocessed="${TMP_ROOT}/testcase"

    fileLoggOut="${TMP_ROOT}/logs/stdout.logg"
    fileLoggErr="${TMP_ROOT}/logs/stderr.logg"
    fileLoggParseTc="${TMP_ROOT}/logs/parse-testcase.logg"
}

###############################################################################
# - saveLoggs -
#
#   Sparar loggfiler under katalogen 'dirLoggsRoot', om den är satt.
#
# Läser: dirLoggsRoot
# Läser: sTestCaseId
# Läser: sTestProcId
#
# A. Om 'dirLoggsRoot' inte är satt ska loggar inte sparas.
# B. Skapa rotkatalogen om den inte finns. Avsluta om den existerar men
#    antingen inte är en katalog eller om vi inte kan skriva till den.
# C. Skapa underkatalogen, dvs rotkatalogen + sTestCaseId.
#    Sätt 'dir' till katalogen dit loggarna ska sparas.
# D. Kopiera loggfilerna.
# E. Skriv ut ett meddelande om att loggarna sparats.
###############################################################################
function saveLoggs
{
# A #
    [ -z "$dirLoggsRoot" ] && return
# B #
    dir=${dirLoggsRoot}
    if [ -e "$dir" ]; then
	if [ ! -d "$dir" ]; then
	    showMsgExecution "cannot save loggs:not a dir:$dir"
	    return 1
	fi
	if [ ! -w "$dirLoggsRoot" ]; then
	    showMsgExecution \
		"cannot save loggs:cannot write to dir:$dir"
	    return 1
	fi
    else
	if ! mkdir --parents $dirLoggsRoot ; then
	    showMsgExecution \
		"cannot save loggs:cannot mkdir:$dir"
	    return 1
	fi
    fi
# C #
    dir="$dir/$sTestCaseId"
    if [ -e "$dir" ]; then
	if [ ! -d "$dir" ]; then
	    showMsgExecution "cannot save loggs:not a dir:$dir"
	    return 1
	fi
	if [ ! -w "$dir" ]; then
	    showMsgExecution \
		"cannot save loggs:cannot write to dir:$dir"
	    return 1
	fi
    else
	if ! mkdir --parents "$dir" ; then
	    showMsgExecution \
		"cannot save loggs:cannot mkdir:$dir"
	    return 1
	fi
    fi
# D #
    for fn in $(ls "$TMP_ROOT/logs"); do
	cp -p $TMP_ROOT/logs/${fn} "${dir}/${sTestProcId}.$fn"
    done
# E #
    [ -n "$bVerb" ] && showMsgExecution "loggs saved as:${dir}/${sTestProcId}"
}

###############################################################################
#  Raderar testkatalogerna om inte 'bKeep'. Om 'bKeep' skrivs testkatalogens
# namn ut.
###############################################################################
function cleanupTestDirs
{
    if [ ! "$bKeep" ]; then
	[ "$TMP_ROOT" ] && rm -rf "${TMP_ROOT}"
    else
	echo "$TMP_ROOT"
    fi
}

###############################################################################
# A. Ett tommt uttryck betyder <ingen test>.
# B. Sätt ${3} till operatorn som ska användas för jämförelsen. Om
#    uttrycket inleds med ett utropstecken ska operatorn vara "!=", annars "=".
#    Ta också bort ett eventuellt utropstecken ur uttrycket.
# C. Utför jämförelsen och returnera svaret.
###############################################################################
function evalUiExpr # <expr> <uint>
{
# A #
    [ -z "$1" ] && return 0
# B #
    set "${1}" "${2}" '='
    if [ '!' = "${1::1}" ]; then
	set "${1:1}" "${2}" '!='
    fi
# C #
    if [ "$1" "$3" "$2" ]; then
	return 0
    else
	return 1
    fi
}


###############################################################################
#   Runs the sepcified program in a sub process.
#
# Argument: cmd-type:
#   * cmdline
#   * interpret.source
#   * interpret.file
###############################################################################
function runProgramInSubProc # <cmd-type> <interp> <cmd> [ CLA ]...
{
    case ${1} in
	cmdline)
	    shift ; shift
	    ( eval "$@" )
	    ;;
	interpret.source)
	    local interp="$2"
	    shift ; shift
	    echo "$*" > $dirDataSources/source.txt
	    ( $interp < $dirDataSources/source.txt )
	    ;;
	interpret.file)
	    shift
	    ( eval "$@" )
	    # ( eval ${2} ${3} )
	    ;;
    esac
}

###############################################################################
#   Runs the sepcified program in the current process.
#
# Argument: cmd-type:
#   * cmdline
#   * interpret.source
#   * interpret.file
###############################################################################
function runProgramInSameProc # <cmd-type> <interp> <cmd> [ CLA ]...
{
    #echo "type='$1'"
    #echo "interp='$2'"
    #echo "cmd='$3'"
    #exit
    case ${1} in
	cmdline)
	    shift ; shift
	    eval "$@" # run in the current process
	    ;;
	interpret.source)
	    local interp="$2"
	    shift ; shift
	    echo "$*" > $dirDataSources/source.txt
	    $interp < $dirDataSources/source.txt # run in the current process
	    ;;
	interpret.file)
	    shift
	    eval "$@" # run in the current process
	    # ( eval ${2} ${3} )
	    ;;
    esac
}

###############################################################################
# Replaces the values of exported Simptest envirnment variables with constants
# in the given file.
###############################################################################
function replace_SIMPTEST_envvars_in_file # FILE
{
    ex -s "${1}" <<EOF
%s:${SIMPTEST_STDOUT}:__SIMPTEST_STDOUT__:g
%s:${SIMPTEST_STDERR}:__SIMPTEST_STDERR__:g
%s:${SIMPTEST_HOME}:__SIMPTEST_HOME__:g
%s:${SIMPTEST_TESTROOT}:__SIMPTEST_TESTROOT__:g
x
EOF
}

###############################################################################
# - runReplace_SIMPTEST_envvars -
#
#   Executes replace-SIMPTEST-envvars.
#
# A. Do replacement for stdout.
# B. Do replacement for stderr.
# C. If a second argument is present and non-empty, do replacement in the
#    file named by this argument.
#    First evaluate the argument and check if the resulting string names a
#    plain file. Print errormessage and exit with EXIT_NONTEST_ERROR if it
#    doesn't.
###############################################################################
function runReplace_SIMPTEST_envvars # <flags> [<arg1>]
{
    # A #
    if containsWordComma "${1}" 'stdout' ; then
	showMsgStepBegin 'check.prepare' 'replace-SIMPTEST-envvars/stdout'
	export SIMPTEST_STDOUT_REPLACED="${SIMPTEST_STDOUT}.replaced"
	cp "${SIMPTEST_STDOUT}" "${SIMPTEST_STDOUT_REPLACED}"
	replace_SIMPTEST_envvars_in_file "${SIMPTEST_STDOUT_REPLACED}"
    fi
    # B #
    if containsWordComma "${1}" 'stderr' ; then
	showMsgStepBegin 'check.prepare' 'replace-SIMPTEST-envvars/stderr'
	export SIMPTEST_STDERR_REPLACED="${SIMPTEST_STDERR}.replaced"
	cp "${SIMPTEST_STDERR}" "${SIMPTEST_STDERR_REPLACED}"
	replace_SIMPTEST_envvars_in_file "${SIMPTEST_STDERR_REPLACED}"
    fi
    # C #
    if [ "${2}" ]; then
	showMsgStepBegin 'check.prepare' "replace-SIMPTEST-envvars:${2}"
	eval set -- ${2}
	if [ ! -f "${1}" ]; then
	    showMsgStepFinish 'NONTEST_ERROR' 'env' "not a file: ${1}"
	    exit ${EXIT_NONTEST_ERROR}
	fi
	replace_SIMPTEST_envvars_in_file "${1}"
    fi
}

###############################################################################
# Utför kontrollerna check.std{out,err}....
#
# Argument:
#   1 <step-name>
#   2 <check-type> (kan vara tom = ingen kontroll)
#   3 <generated file>
#   4 [<file with correct contents>] (if check-type = FILE|XMLFILE)
#
# A. Avsluta om ingen test ska göras.
# B. En test ska utföras - skriv ut rubrik.
# C. Utför kontrollen.
###############################################################################
function checkFileContents
{
# A #
    if [ "$2" = '' ]; then
	return
    fi
# B #
    if [ $2 = 'file' ]; then
	showMsgStepBegin "$1" "$4"
    else
	showMsgStepBegin "$1" "<$2>"
    fi
# C #
    case $2 in
	EMPTY)
	    if [ $(stat -c %s "$3") != 0 ]; then
		showMsgStepFinish 'FAIL' "$1"
		exit $EXIT_FAIL
	    fi
	    ;;
	WHITESPACE-ONLY)
	    while read line ; do
		if [ -n "$line" ]; then
		    showMsgStepFinish 'FAIL' "$1"
		    exit $EXIT_FAIL
		fi
	    done < "$3"
	    ;;
	FILE)
	    if ! diff "$4" "$3" \
		>> "${fileLoggOut}" 2>> "${fileLoggErr}" ; then
		showMsgStepFinish 'FAIL' "$1"
		exit $EXIT_FAIL
	    fi
	    ;;
	XMLFILE)
	    if ! ${sPgmXmldiff} "$4" "$3" \
		>> "${fileLoggOut}" 2>> "${fileLoggErr}" ; then
		showMsgStepFinish 'FAIL' "$1"
		exit $EXIT_FAIL
	    fi
	    ;;
	*)
	    showMsgInternalError "$1" 'checkFileContents' "invalid checktype:$2"
	    exit $EXIT_INTERNALERR
	    ;;
    esac
}

###############################################################################
# - checkCompareEq_fileContents -
#
#   Performs check.compare.eq/file-contents. Exits if any check fails.
#
# A. Log/print step-begin.
# B. If <src> is a file:
#    B.1. Fail if <dst> is not a file.
#    B.2. Fail if <src> and <dst> differ in contents.
#         If the flag "xml" is given, check using ${sPgmXmldiff}.
#         Otherwise, check using `diff'.
#         Error message depends on which comparison program is used.
# C. If <src> is a directory:
#    C.1. Fail if <dst> is not a directory.
#    C.2. Fail if any file under <src> does not have a corresponding file
#         under dst or the files differ in contents.
# D. Fail if <src> is neither a file nor a directory.
###############################################################################
function checkCompareEq_fileContents # SRC DST lFlags
{
    local fileSrc="$1"
    local fileDst="$2"
    # A #
    showMsgStepBegin 'check-compare-eq/file-contents'
    if [ -f "${fileSrc}" ]; then
	# B #
	# B1 #
	if [ ! -f "${fileDst}" ]; then
	    showMsgStepFinish 'FAIL' 'not a file' ":${fileDst}"
	    exit ${EXIT_FAIL}
	fi
	# B2 #
	local DIFFPGM='diff'
	local sDiffErrMsg='contents differ'
	if containsWordComma "${lFlags}" 'xml' ; then
	    DIFFPGM="${sPgmXmldiff}"
	    sDiffErrMsg='xml contents differ'
	fi
	if ! ${DIFFPGM} "${fileSrc}" "${fileDst}" \
	    >> "${fileLoggOut}" 2>> "${fileLoggErr}" ; then
	    showMsgStepFinish 'FAIL' "${sDiffErrMsg}"
	    exit ${EXIT_FAIL}
	fi
    elif [ -d "${fileSrc}" ]; then
	# C #
	# C1 #
	if [ ! -d "${fileDst}" ]; then
	    showMsgStepFinish 'FAIL' 'not a directory' ":${fileDst}"
	    exit ${EXIT_FAIL}
	fi
	# C2 #
	find "${fileSrc}" -type f -printf "%P\n" | while read fn; do
	    if ! diff -q "${fileSrc}/${fn}" "${fileDst}/${fn}" \
		>> "${fileLoggOut}" 2>> "${fileLoggErr}" ; then
		showMsgStepFinish 'FAIL' 'files differ' ":${fn}"
		exit ${EXIT_FAIL}
	    fi
	done
	[ $? != 0 ] && exit ${EXIT_FAIL}
    else
	# D #
	showMsgStepFinish 'FAIL' 'src is  neither a file nor a directory'
	exit ${EXIT_FAIL}
    fi
}

###############################################################################
# - checkCompareEq_dirContents -
#
#   Performs check.compare.eq/dir-contents. Exits if any check fails.
#
# A. Log/print step-begin.
# B. Fail if either <src> or <dst> is not a directory.
# D. Compare the directory-contents.
#    1. Compare the directories using `diff'.
#       Set sDiffExclude to the arguments to pass to diff for excluding the
#       given exclude patterns (which are $1, $2, ...).
#    2. If we are not dereferencing, we have to check that file types are
#       also identical (since this is not done by `diff').
#       Set sFindExclude to the arguments to pass to find for excluding the
#       given exclude patterns (which are $1, $2, ...).
#       1. Compare the types of the "root" directories.
#          (Would be better if step 2 could handle this case too.
#          Unfortunately, `stat' behaves differently on "x" and "x/" :( )
#       2. Compare the types of "sub" files.
###############################################################################
function checkCompareEq_dirContents # SOURCE DESTINATION [EXCLUDE-PATTERN...]
{
    local fileSrc="$1"
    local fileDst="$2"
    shift ; shift
    # A #
    showMsgStepBegin 'check-compare-eq/dir-contents'
    # B #
    if [ ! -d "${fileSrc}" ]; then
	showMsgStepFinish 'FAIL' 'not a directory' ":${fileSrc}"
	exit $EXIT_FAIL
    fi
    if [ ! -d "${fileDst}" ]; then
	showMsgStepFinish 'FAIL' 'not a directory' ":${fileDst}"
	exit $EXIT_FAIL
    fi
    # D #
    # 1 #
    sDiffExclude=''
    for pat; do
	sDiffExclude="${sDiffExclude} --exclude ${pat}"
    done
    if ! diff -r ${sDiffExclude} "${fileSrc}" "${fileDst}" \
      >> "${fileLoggOut}" 2>> "${fileLoggErr}" ; then
	showMsgStepFinish 'FAIL' 'the contents of src and dst differ'
	exit ${EXIT_FAIL}
    fi
    # 2 #
    sFindExclude=''
    for pat; do
	sFindExclude="${sFindExclude} ! -name ${pat}"
    done
    if ! containsWordComma "${lFlags}" 'dereference' ; then
	# 2.1 #
	if [ "$(stat --printf=%F "${fileSrc}")" != "$(stat --printf=%F "${fileDst}")" ]; then
	    showMsgStepFinish 'FAIL' "different types of files: \`${fileSrc}', \`${fileDst}'"
	    exit ${EXIT_FAIL}
	fi
	# 2.2 #
	find -P "${fileSrc}" -mindepth 1 ${sFindExclude} -printf "%P\n" | {
	    while read fn; do
		fSrc="${fileSrc}/${fn}"
		fDst="${fileDst}/${fn}"
		if [ "$(stat --printf=%F "${fSrc}")" != "$(stat --printf=%F "${fDst}")" ]; then
		    showMsgStepFinish 'FAIL' "different types of files: \`${fSrc}', \`${fDst}'"
		    exit ${EXIT_FAIL}
		fi
	    done
	}
    fi
}

###############################################################################
# 0. Store the flags in 'lFlags'. Evaluate $1 and $2 to get the final
#    filenames.
#    If not 1-non-home,src is relative SIMPTEST_HOME.
# A. Log/print step-begin.
# B. Fail if any of the files do not exist.
# C. If the flag is default, set it depending on wether src is a file or a
#    directory.
# D. If the test-command is 'print-check-compare-eq-flags', print the flags
#    and exit.
#    Print the flags, one per line, sorted.
# E. /file-contents
# F. /dir-contents
# G. For the remaining tests we use `stat', and we must give the flag -L to it
#    if we are dereferencing files. Set the variable 'deref' to this flag, or
#    empty, if we shall not dereference.
# H. /type
# I. /mtime
# J. /mode
###############################################################################
function checkCompareEq # <src> <dst> <flags>
{
    # 0 #
    local lFlags="$3"
    eval -- set "${1}" "${2}"
    local fileSrc="${1}"
    if ! containsWordComma "${lFlags}" '1-non-home'; then
	fileSrc="${SIMPTEST_HOME}/${fileSrc}"
    fi
    local fileDst="${2}"
    # A #
    showMsgStepBegin 'check-compare-eq'
    # B #
    if [ ! -e "${fileSrc}" ]; then
	showMsgStepFinish 'FAIL' 'src does not exist' "${fileSrc}"
	exit $EXIT_FAIL
    fi
    if [ ! -e "${fileDst}" ]; then
	showMsgStepFinish 'FAIL' 'dst does not exist' "${fileDst}"
	exit $EXIT_FAIL
    fi
    # C #
    if [ "${lFlags}" == '/' ] || containsWordComma "${lFlags}" 'default' ; then
	[ "${lFlags}" == '/' ] && lFlags=''
	if [ -f "${fileSrc}" ]; then
	    lFlags="${lFlags}${lFlags:+,}type,file-contents"
	elif [ -d "${fileSrc}" ]; then
	    lFlags="${lFlags}${lFlags:+,}type,file-contents,dir-contents"
	fi
    fi
    # D #
    if [ "${cmdTest}" = 'print-check-compare-eq-flags' ]; then
	IFS=','
	for x in ${lFlags}; do echo $x; done | sort
	exit 0
    fi
    # E #
    if containsWordComma "${lFlags}" 'file-contents' ]]; then
	checkCompareEq_fileContents "${fileSrc}" "${fileDst}" "${lFlags}"
    fi
    # F #
    if containsWordComma "${lFlags}" 'dir-contents' ]]; then
	IFS=','
	set ${lFlags}
	lExcludePatterns=''
	for flag; do
	    if [ "${flag::8}" = 'exclude=' ]; then
		lExcludePatterns="${lExcludePatterns} ${flag:8}"
	    fi
	done
	IFS="${ifsOrig}"
	checkCompareEq_dirContents "${fileSrc}" "${fileDst}" ${lExcludePatterns}
    fi
    # G #
    if containsWordComma "${lFlags}" 'dereference' ; then
	local deref='-L'
    else
	local deref=''
    fi
    # H #
    if containsWordComma "${lFlags}" 'type' ; then
	showMsgStepBegin 'check-compare-eq/type'
	local typeSrc=$(stat $deref --format='%F' "${fileSrc}")
	local typeDst=$(stat $deref --format='%F' "${fileDst}")
	if [ "${typeSrc}" != "${typeDst}" ]; then
	    showMsgStepFinish 'FAIL' 'file type mismatch' "${typeSrc}/${typeDst}"
	    exit $EXIT_FAIL
	fi
    fi
    # I #
    if containsWordComma "${lFlags}" 'mtime' ; then
	showMsgStepBegin 'check-compare-eq/mtime'
	local timeSrc=$(stat $deref --format='%y' "${fileSrc}")
	local timeDst=$(stat $deref --format='%y' "${fileDst}")
	if [ "${timeSrc}" != "${timeDst}" ]; then
	    showMsgStepFinish 'FAIL' 'mtime mismatch' "${timeSrc}/${timeDst}"
	    exit $EXIT_FAIL
	fi
    fi
    # J #
    if containsWordComma "${lFlags}" 'mode' ; then
	showMsgStepBegin 'check-compare-eq/mode'
	local modeSrc=$(stat $deref --format='%a' "${fileSrc}")
	local modeDst=$(stat $deref --format='%a' "${fileDst}")
	if [ "${modeSrc}" != "${modeDst}" ]; then
	    showMsgStepFinish 'FAIL' 'file mode mismatch' "${modeSrc}/${modeDst}"
	    exit $EXIT_FAIL
	fi
    fi
}

###############################################################################
# Executes the test command "env".
###############################################################################
function testCommandEnv
{
    local i cmd var

    for i in ${!aEnvCmds[@]} ; do
	if [[ "${aEnvCmds[$i]}" =~ ^unset' '([^=]+)$ ]]; then
	    echo ${BASH_REMATCH[1]}
	elif [[ "${aEnvCmds[$i]}" =~ ^([^=]+)= ]]; then
	    echo ${BASH_REMATCH[1]}
	fi
    done |
    sort | uniq |
    while read var ; do
	echo "$var=${!var}"
    done
}

###############################################################################
#   Print a table with all the programs that are read from the testcase.
# Used for debuging.
###############################################################################
function test_printPrograms
{
    local format='%-18s %-17s %-10s %s\n'
    printf "$format" 'Step' 'Type' 'Interp' 'Command'
    echo ----------------------------------------------------------------------
    {
	for i in ${!apgmSetupRun_Type[@]} ; do
	    printf "$format" setup[$i] ${apgmSetupRun_Type[$i]} \
		"${apgmSetupRun_Interp[$i]}" "${apgmSetupRun_Cmd[$i]}"
	done
	for i in ${!apgmPrecondType[@]} ; do
	    printf "$format" setup[$i] ${apgmPrecondType[$i]} \
		"${apgmPrecondInterp[$i]}" "${apgmPrecondCmd[$i]}"
	done
	for i in ${!apgmTestRunType[@]} ; do
	    printf "$format" test.run[$i] ${apgmTestRunType[$i]} \
		"${apgmTestRunInterp[$i]}" "${apgmTestRunCmd[$i]}"
	done
	for i in ${!apgmCheckPrepareType[@]} ; do
	    printf "$format" check.prepare[$i] ${apgmCheckPrepareType[$i]} \
		"${apgmCheckPrepareInterp[$i]}" "${apgmCheckPrepareCmd[$i]}"
	done
	for i in ${!apgmCheckCustomType[@]} ; do
	    printf "$format" check.custom[$i] ${apgmCheckCustomType[$i]} \
		"${apgmCheckCustomInterp[$i]}" "${apgmCheckCustomCmd[$i]}"
	done
	} |
    sed "s:$dirHome:__SIMPTEST_HOME__:g"
}

###############################################################################
# - testcaseComplete -
#
#   Tar reda på om det inlästa testfallet är komplett - om det går att utgöra
# något test med det.
#   En syntaktiskt korrekt testfallsfil kan anges utan att den är komplett.
#
# Retur:
#  0 - testfallet är komplett.
#  1 - testfallet är INTE komplett. Ett meddelande om varför har skrivits ut
#      på stdout.
#
# A. Minst ett testprogram måste ha angivits.
# B. Testfallet är korrekt. Returnera 0.
###############################################################################
function testcaseIsComplete
{
# A #
    if [ ! "${!apgmTestRunType[*]}" ]; then
	echo 'no test specified (with test.run)'
	return 1
    fi
# B #
    return 0
}

###############################################################################
function printTc
{
    #echo "application:$sApplication"
    #echo "name       :$sName"
    #echo "home       :$dirHome"
    #echo "setup      :${#apgmSetupRun_Type[*]}"
    for i in ${!apgmSetupRun_Type[@]} ; do
	echo "* setup[$i]"
	echo "    type:${apgmSetupRun_Type[$i]}"
	echo "  interp:${apgmSetupRun_Interp[$i]}"
	echo "     cmd:${apgmSetupRun_Cmd[$i]}"
    done
    for i in ${!apgmPrecondType[@]} ; do
	echo "* precond[$i]"
	echo "    type:${apgmPrecondType[$i]}"
	echo "  interp:${apgmPrecondInterp[$i]}"
	echo "     cmd:${apgmPrecondCmd[$i]}"
    done
    for i in ${!apgmTestRunType[@]} ; do
	echo "* test.run[$i]"
	echo "    type:${apgmTestRunType[$i]}"
	echo "  interp:${apgmTestRunInterp[$i]}"
	echo "     cmd:${apgmTestRunCmd[$i]}"
    done
    for i in ${!apgmCheckPrepareType[@]} ; do
	echo "* check.prepare[$i]"
	echo "    type:${apgmCheckPrepareType[$i]}"
	echo "  interp:${apgmCheckPrepareInterp[$i]}"
	echo "     cmd:${apgmCheckPrepareCmd[$i]}"
    done
    for i in ${!apgmCheckCustomType[@]} ; do
	echo "* check.custom[$i]"
	echo "    type:${apgmCheckCustomType[$i]}"
	echo "  interp:${apgmCheckCustomInterp[$i]}"
	echo "     cmd:${apgmCheckCustomCmd[$i]}"
    done

    for i in ${!aEnvCmds[@]} ; do
	echo "aEnvCmds[$i]=${aEnvCmds[$i]}"
    done

    #echo "exitcode   :$uieCheckExitCode"
    #echo "stdin      :$fileTestStdin"
    #echo "stdout     :$fileCheckStdout"
    #echo "stderr     :$fileCheckStderr"
    #pathdirs | uniq
}

###############################################################################
#   Syntax checks, parses and prints flags..
#
# Argument 1: key
# Argument 2: default flags value
# Argument 3: flags string
#
# Exitcode: !0 if syntax error.
#
#   "key" is only used for printing error messages.
#   If flags are given using a string beginning with /, these flags
# are printed to stdout. If only a / is given, then the flags is empty.
#   If no flags are given (the "flags string" is empty, not even
#   containing a single /), the "default flags value" is printed to stdout.
###############################################################################
function getFlags # key default flags
{

  if [[ "${3}" =~ ^(/([^/]*))?$ ]]; then
      # Syntax ok. Flaggorna = default eller BASH_REMATCH[2]
      if [ "${3}" ]; then
	  echo "${BASH_REMATCH[2]}"
      else
	  echo "${2}"
      fi
  else
      echo "${1} syntax error: invalid flags:${3}" >&2
      exitcode=1 # FIX $EXIT_PARSE
      echo "    getFlags: exitcode=$exitcode" >&2
      return 1
  fi
}

###############################################################################
# - parseEnv -
# Indata:
#   #1 : env-command
#   #2 : variable
#   #3 : value
#   #4 : lFlags
#
# Utdata:
#   0 - allt ok
#   $EXIT_PARSE - syntax-fel
#   $EXIT_FILE  - refererad fil existerar inte.
#
#
# Sätter: aEnvCmds
#
# A. Tar fram indexnummret för nästa lediga plats i arrayen för  miljökommandon
#    ('aEnvCmds').
# B. If the command is not 'unset', put the value in 'val'.
# C. Handle flags.
#    1. mkabspath
#    2. exists
# C. Tolka kommandot.
#   C.1. Om kontroller angivits med /<kontroll>, lägg den i 'check' och själva
#        kommandot i 'cmd'.
#   C.2. Om kommandot avslutas med '.mkabspath' ska 'home' prependas och
#        värdet göras om till en absolut sökväg med 'realpathBash'.
# D. Skapa ett kommando för att sätta miljövariabeln och lägg det i 'aEnvCmds'.
# E. Om kontroller ska utföras, utför dem.
###############################################################################

function parseEnv
{
    local cmd="${1}"
    local var="${2}"
    local val="${3}"
    local lFlags="${4}"
    local valBefore check sInfo
    local IFS="$ifsOrig"
# A #
    local n=${#aEnvCmds[*]}
# B #
    if [[ ${cmd} != 'unset' ]]; then
	if ! eval val="${val}"; then
	    showMsgParseErr "invalid value:$val"
	    return $EXIT_PARSE
	fi
    fi
    ### C ###
    # C1 #
    if containsWordComma "$lFlags" 'mkabspath' ; then
	if ! val=$(realpathBash "${dirHome}/${val}"); then
	    showMsgParseErr "mkabspath: invalid filename:${val}"
	    return $EXIT_FILE
	fi
    fi
    # C2 #
    if containsWordComma "${lFlags}" 'exists' ; then
	if [ ! -e "${val}" ]; then
	    showMsgParseErr "env: file does not exist:${val}"
	    return $EXIT_FILE
	fi
    fi
# D #
    case "${cmd}" in
	'set')
	    aEnvCmds[$n]="${var}=\"$val\"; export ${var}"
	    ;;
	'unset')
	    aEnvCmds[$n]="unset ${var}"
	    ;;
	'prepend')
	    aEnvCmds[$n]="${var}=\"${val}\${$var}\" ; export ${var}"
	    ;;
	'append')
	    aEnvCmds[$n]="${var}=\"\${$var}${val}\" ; export ${var}"
	    ;;
	'list.prepend')
	    aEnvCmds[$n]="${var}=\"${val}\${${var}:+:}\${$var}\" ; export ${var}"
	    ;;
	'list.append')
	    aEnvCmds[$n]="${var}=\"\${$var}\${${var}:+:}${val}\" ; export ${var}"
	    ;;
	*)
	    showMsgParseErr "invalid env command: ${cmd}"
	    return $EXIT_PARSE
    esac
    return 0
}

###############################################################################
# - parseProgram -
#
#   Parsar angivelsen av ett program.
#
#   För de programtyper som bara använder två fält: om ett tredje fält
# existerar (här <arg2> ($4)) betyder det att fält nummer två innehöll ett
# kolon som gjorde att fältet splittades i två delar. Detta måste återställas.
# Lägg därför det värde som det andra fältet egentligen ska ha i variabeln
# 'field2'.
#
#
# Returkoder för fel:
#  * EXIT_FILE  - angiven fil existerar inte
#  * EXIT_PARSE - felaktig syntax
#
# Indata:
#  arg1: array-prefix.
#    Programmet som läses in läggs i en "programlista" : en lista som består
#    av tre variabler med ett gemensamt prefix. Detta argument är det prefixet.
#    Suffixet för variabelnamnen är "Type", "Interp" och "Cmd".
###############################################################################

function parseProgram # <arrprefix> <pgmtype> <arg1> <arg2> <lFlags> <nNumCmdParts>
{
    local n arrname cmdSetNum cmdSetType cmdSetInterp cmdSetCmd ifsStore field2
    local IFS="${ifsOrig}"

    local sArrPrefix=${1}
    local pgmtype=${2}
    local sArg1=${3}
    local sArg2=${4}
    local lFlags=${5}
    local nNumCmdParts=${6}

    # Hämta antal element = index för nästa.
    arrname=${sArrPrefix}Type
    cmdSetNum='n=${#'${arrname}'[*]}'
    eval $cmdSetNum
    # Skapa kommandon för tilldelning av de olika arrayerna.
    cmdSetType="${sArrPrefix}Type[$n]="
    cmdSetInterp="${sArrPrefix}Interp[$n]="
    cmdArrNameCmd="${sArrPrefix}Cmd[$n]"
    cmdArrElemCmd="\${${cmdArrNameCmd}}"
    cmdSetCmd="${cmdArrNameCmd}="
    cmdAssignCmdToFn="fn=\"${cmdArrElemCmd}\""
    #echo "cmdSetType       :$cmdSetType"
    #echo "cmdSetInterp     :$cmdSetInterp"
    #echo "cmdSetCmd        :$cmdSetCmd"
    #echo "cmdArrNameCmd    :${cmdArrNameCmd}"
    #echo "cmdSetCmd        :${cmdSetCmd}"
    #echo "cmdAssignCmdToFn :${cmdAssignCmdToFn}"
    #echo "cmdArrElemCmd    :${cmdArrElemCmd}"
    #echo
    #return 0
    case "${pgmtype}" in
	cmdline)
	    case ${nNumCmdParts} in
		1)
		    showMsgParseErrNotProgram "program argument missing"
		    return ${EXIT_PARSE}
		    ;;
		3)
		    # Concatenate arguments to construct a single argument.
		    # (too many arguments is the result of a parsing problem using
		    # the current implementation)
		    sArg1="${sArg1}:${sArg2}"
		    nNumCmdParts=1
		    ;;
	    esac
	    eval ${cmdSetType}'cmdline'
	    if containsWordComma "$lFlags" 'prepend-home' ]]; then
		eval ${cmdSetCmd}"'${dirHome}/${sArg1}'"
                # Check that the first component of the above is a file.
		set -- ${!cmdArrNameCmd}
		#set -- ${sArg1}
		if [ ! -f "${1}" ]; then
		    showMsgParseErrNotFile "${1}"
		    return $EXIT_FILE
		fi
	    else
		eval ${cmdSetCmd}"'${sArg1}'"
	    fi
	    ;;
	interpret.source)
	    if [ ${nNumCmdParts} != 3 ]; then
		showMsgParseErrMissingArgFor "${pgmtype}:${sArg1}"
		return $EXIT_PARSE
	    fi
	    eval ${cmdSetType}'interpret.source'
	    eval ${cmdSetInterp}"'${sArg1}'"
	    eval ${cmdSetCmd}"'${sArg2}'"
	    ;;
	interpret.file)
	    if [ ${nNumCmdParts} != 3 ]; then
		showMsgParseErrMissingArgFor "${sArg1}:${sArg2}"
		return $EXIT_PARSE
	    fi
	    eval ${cmdSetType}'interpret.file'
	    eval ${cmdSetInterp}"'${sArg1}'"
	    if [ "${sArg2::1}" = '/' ]; then
		eval ${cmdSetCmd}"'${sArg2}'"
	    else
		eval ${cmdSetCmd}"'$dirHome/${sArg2}'"
	    fi
	    eval set ${cmdArrElemCmd}
	    if [ ! -f "${1}" ]; then
		showMsgParseErrNotFile "${1}"
		return $EXIT_FILE
	    fi
	    ;;
	*)
	    showMsgParseErrNotProgram "${pgmtype}"
	    return $EXIT_PARSE
	esac
}

###############################################################################
# - parseKey -
#
#   Parses the key-part - the "key" and the flags.
#
# Argument: 1 - complete key string (including flags).
#
# Sets: key, aCmdParts[0]
#    To the part before any /.
# Sets: lFlags
#    If there is a /: to the part after this (can be empty).
#    If there is no /: to / to indicate <default>.
#
# Exit code: 0 - ok
# Exit code: 1 - syntax error
###############################################################################
function parseKey # <string>
{
    if [[ "$1" =~ ^([^ /]+)(/([^/]*))?$ ]]; then
	key=${BASH_REMATCH[1]}
	aCmdParts[0]=${BASH_REMATCH[1]}
	if [ "${BASH_REMATCH[2]}" == '' ]; then
	    lFlags='/'
	else
	    lFlags="${BASH_REMATCH[3]}"
	fi
	return 0
    else
	return 1
    fi
}

###############################################################################
# Checks the number of command parts.  Logs an error message and sets
# 'exitcode' if it is wrong.
#
# Sets: exitcode
###############################################################################
function checkNumCmdParts # <# args expected> <# args given> <err msg>
{
    if [ ${1} != ${2} ]; then
	showMsgParseErr "${3}"
	exitcode=$EXIT_PARSE
	return 1
    fi
    return 0
}

###############################################################################
# - parseTestCase -
#
#   Läser in ett testfall från stdin.
#   Om fel inträffar rapporteras de och en felkod returneras. Även efter att
# ett fel har påträffats fortsätter parsningen så att flera felmeddelanden
# kan rapporteras - förhoppningsvis alla!
#
# Retur:
#  * 0 - OK
#  * EXIT_FILE - en eller flera fil/katalog finns inte. I övrigt korrekt
#    syntax.
#  * EXIT_PARSE - felaktig syntax. Dessutom kan en eller flera filer/kataloger
#    saknas. Eftersom ett syntaxfel anses som allvarligare än saknade filer och
#    kataloger returneras EXIT_PARSE istället för EXIT_FILE.
#
# Läser:
#  * fileTestCase
#  * dirHome
#
# Sätter: sTestCaseId
#
# IMPLEMENTATION
#
# *** Lokala variabler
#
#  * exitcode - den returkod som ska returneras
#  * nNumCmdParts - number of : separated parts: key, x, y.
#  * pvX      - Namnet på variabeln som ska tilldelas värdet i $x.
#  * pvY      - Namnet på variabeln som ska tilldelas värdet i $y.
#  * op
#    Operationen som ska utföas på variabeln $pvX.
#    'program' betyder läs program.
#    Tom betyder ersätt variabeln $pvX.
#    'append' betyder att värdet ska läggas till slutet av variabeln $pvX.
#    möjligtvis, om sAppSep är satt, med denna imellan.
#  * sAppSep  - Se 'op'.
#  * typeArg1
#  * typeArg2
#  * sSyntaxMsg
#  * xy
#    Om raden bara har två fält, men det andra fältet innehåller ett kolon har
#    fält#2 splittats i två delar, den ena i 'x' och den andra i 'y'. Lägg det
#    som ska vara fält#3 i 'xy' så att det kan användas, bl a skickas till
#    andra parsefunktioner.
#
# A. Initiera.
#   A1. Byt fältseparatorn till ":".
#   A2. Initiera returkoden. Sätt den till "allt ok".
# B. Läs varje rad i filen = varje nyckel (om ej tom rad eller kommentar).
#   B0. No command uses more than 2 arguments.  Therefore no command is
#       made up of more than 3 parts. Print error message and skip the command
#       if there are more than 3 parts.
#
#       Reconstruct the whole line from the parts key, x, y (with IFS
#       added), so that we can check for comment and empty lines.  These
#       should be skipped.
#   B1. Hoppa över tomma rader och kommentarer.
#   B2. Sätt 'key' och 'lFlags'.
#       'lFlags' sätts till
#           * tom sträng: om bra / angavs (inga flaggor)
#           * '/'       : om inget angavs, detta betyder <utgångsvärdet>
#                         (vilket bestäms individuellt av varje kommando)
#           * <x>       : <x> är flaggorna som angivits.
#   B3. Initiera statusvariabler.
#       * check.compare.eq
#          1. Check syntax - two arguments must be given: src and dst.
#          2. Check fileSrc. If the flag "1-non-home" is NOT given, fileSrc is
#             supposed to be relative $dirHome: $dirHome should be prepended
#             and the
#             result must be an existing file or directory. Otherwise, fileSrc
#             should be left as it is.
#             the test case home directory.
#             In case of error, set exitcode unless it is not already set.
#          3. Store the check in 'aCheckCmpEq_...'.
#             3.1. Get the next index in 'aCheckCmpEq_...'. Put it in 'i'.
#             3.2. Store 'lFlags', 'fileSrc', 'fileDst'.
#       * check.{stdout,stderr}
#          1. Set 'sChannelIndex' to the index we shall use for the array
#             check_channel_... The index should be 'stdout' or 'stderr'.
#          2. Set the flags default value = no default value.
#          3. Parse the subcommand. Set 'check_channel_checkType[...]'.
#             * file.eq
#               1. Check number of argumnets.
#               2. Set 'check_channel_file[...]'.
#                  If the flag 'prepend-home' is given, prepend dirHome and
#                  check that the result names an existing file.
#          4. Set 'check_channel_lFlags' and 'check_channel__channel'.
#             Do this last - when we know that the commands is a valid
#             command - so that 'check_channel__channel' only contains
#             elements for valid commands.
# D. Sätt 'sTestCaseId'.
# E. Returnera den felkod som lagrats i 'exitcode' (kan vara =0).
###############################################################################
function parseTestCase
{
    local exitcode lFlags pvX pvY bXIsFile typeArg1 typeArg2
    local sLine sSyntaxMsg tmp
    ### A ###
# A1 #
    local IFS=':'
# A2 #
    exitcode=0
    ### B ###
    # Can't use -a aCmdParts, bash bug!
    while read sCmdParts0 sCmdParts1 sCmdParts2; do
	unset aCmdParts
	aCmdParts[0]=${sCmdParts0}
	if [ "${sCmdParts1}" ]; then
	    aCmdParts[1]=${sCmdParts1}
	fi
	if [ "${sCmdParts2}" ]; then
	    aCmdParts[2]=${sCmdParts2}
	fi
	# B0 #
	nNumCmdParts=${#aCmdParts[@]}
	if [ ${nNumCmdParts} -gt 3 ]; then
	    showMsgParseErr "too many arguments (${nNumCmdParts}): ${aCmdParts[*]}"
	    exitcode=$EXIT_PARSE
	    continue
	fi
        # B2 #
	unset sKey lFlags
	if ! parseKey "${aCmdParts[0]}"; then
	    showMsgParseErr "syntax error in key: ${aCmdParts[0]}"
	    exitcode=$EXIT_PARSE
	    continue
	fi
        # B3 #
	pvX=
	op=
	sAppSep=
	typeArg1=
	sSyntaxMsg=

	case "${aCmdParts[0]}" in
	    application)
		sSyntaxMsg="application:<str>"
		pvX=sApplication
		typeArg1='str'
		unset typeArg2
		;;
	    name)
		sSyntaxMsg="name:<str>"
		pvX=sName
		typeArg1='str'
		unset typeArg2
		;;
	    home)
		sSyntaxMsg="home:<dir>"
		pvX=dirHome
		typeArg1='dir'
		unset typeArg2
		;;
	    env.*)
		parseEnv "${aCmdParts[0]:4}" "${aCmdParts[1]}" "${aCmdParts[2]}" "${lFlags}"
		st=$?
		[ $st != 0 -a $exitcode != $EXIT_PARSE ] && exitcode=$st
		continue
		;;
	    test.stdin)
		sSyntaxMsg="test.stdin/{prepend-home}:<str>"
		pvX=fileTestStdin
		typeArg1='file'
		unset typeArg2
		;;
	    check.exitcode)
		checkNumCmdParts 2 ${nNumCmdParts} 'check.exitcode shoud have 1 argument' \
		    || continue
		sSyntaxMsg="check.exitcode:<N>"
		pvX=uieCheckExitCode
		typeArg1='uintexpr'
		unset typeArg2
		;;
	    check.stdout.* | check.stderr.*)
		# 1 #
		local idx=${#check_channel__channel[@]}
		local ch=${aCmdParts[0]:6:6}
		# 2 #
		[ "${lFlags}" == '/' ] && lFlags=''
		# 3 #
		case "${aCmdParts[0]:13}" in
		    empty)
			checkNumCmdParts 1 ${nNumCmdParts} \
			    "${aCmdParts[0]::12}.empty shoud have no arguments" || continue
			check_channel__checkType[${idx}]='EMPTY'
			;;
		    whitespace-only)
			checkNumCmdParts 1 ${nNumCmdParts} \
			    "${aCmdParts[0]::12}.whitespace-only shoud have no arguments" || continue
			check_channel__checkType[${idx}]='WHITESPACE-ONLY'
			;;
		    file.eq)
			# 1 #
			checkNumCmdParts 2 ${nNumCmdParts} \
			    "${aCmdParts[0]::12}.file.eq shoud have 1 argument" || continue
			# 2 #
			if containsWordComma "${lFlags}" 'non-home' ; then
			    check_channel__file[${idx}]=${aCmdParts[1]}
			else
			    tmp="${dirHome}/${aCmdParts[1]}"
			    if [ ! -f "${tmp}" ]; then
				showMsgParseErr "${aCmdParts[0]}" "not a file: ${aCmdParts[1]}"
				exitcode=${EXIT_FILE}
				continue
			    fi
			    check_channel__file[${idx}]=${tmp}
			fi
			if containsWordComma "${lFlags}" 'xml' ; then
			    check_channel__checkType[${idx}]='XMLFILE'
			else
			    check_channel__checkType[${idx}]='FILE'
			fi
			;;
		    *)
			showMsgParseErr 'check.stdout' "invalid check: ${aCmdParts[0]}"
			exitcode=${EXIT_PARSE}
			continue
		esac
		# 4 #
		check_channel__channel[${idx}]=${ch}
		check_channel__lFlags[${idx}]=${lFlags}
		continue
		;;
	    check.compare.eq)
		## check.compare.eq ##
		# 1 #
		checkNumCmdParts 3 ${nNumCmdParts} 'check.compare.eq shoud have 2 arguments' \
		    || continue
		# 2 #
		fileSrc=${aCmdParts[1]}
		fileDst=${aCmdParts[2]}
		if containsWordComma ! "${lFlags}" "1-non-home" ; then
		    if [ ! -e "${dirHome}/${fileSrc}" ]; then
			showMsgParseErr "missing file under home:${fileSrc}"
			[ $exitcode != 0 ] && exitcode=$EXIT_FILE
		    else
			fileSrc="${dirHome}/${fileSrc}"
		    fi
		fi
		# 3 #
		# 3.1 #
		i=${#aCheckCmpEq_Flags[*]}
		let ++i
		# 3.2 #
		aCheckCmpEq_Flags[$i]="${lFlags}"
		aCheckCmpEq_Src[$i]="${fileSrc}"
		aCheckCmpEq_Dst[$i]="${fileDst}"
		continue
		;;
	    setup.install)
		if [ ${nNumCmdParts} == 1 ]; then
		    showMsgParseErr 'setup.install shoud have 1 or 2 arguments'
		    exitcode=$EXIT_PARSE
		    continue
		fi
		fileSrc=${aCmdParts[1]}
		fileDst=${aCmdParts[2]}
		# If not using 1-non-home, construct absolute path and check if the file exists.
		# If     using 1-non-home: leave the path as it is - it will be tested during
		#                          execution of the testcase..
		if ! containsWordComma "${lFlags}" "1-non-home" ; then
		    if [ ! -e "${dirHome}/${fileSrc}" ]; then
			showMsgParseErr "setup.install: missing file under home:${fileSrc}"
			[ $exitcode != 0 ] && exitcode=$EXIT_FILE
		    else
			fileSrc="${dirHome}/${fileSrc}"
		    fi
		fi
		i=${#aSetupInstall_src[*]}
		let ++i
		aSetupInstall_src[$i]="${fileSrc}"
		aSetupInstall_dst[$i]="${fileDst}"
		;;
	    setup.run.*)
		op='program'
		pgmtype=${aCmdParts[0]:10}
		#pgmtype="${aCmdParts[0]:10}"
		arrprefix='apgmSetupRun_'
		[ "${lFlags}" == '/' ] && lFlags=''
		;;
	    test.run.*)
		op='program'
		pgmtype="${aCmdParts[0]:9}"
		arrprefix='apgmTestRun'
		[ "${lFlags}" == '/' ] && lFlags=''
		;;
	    precond.run.*)
		op='program'
		pgmtype="${aCmdParts[0]:12}"
		arrprefix='apgmPrecond'
		[ "${lFlags}" == '/' ] && lFlags=''
		;;
	    check.prepare.*)
		aCmdParts[0]=${aCmdParts[0]:14}
		case "${aCmdParts[0]}" in
		    replace-SIMPTEST-envvars)
			tmp=${#apgmCheckPrepareType[*]}
			apgmCheckPrepareType[$tmp]='REPLACE-ENVVARS'
			[ "${lFlags}" == '/' ] && lFlags=''
			apgmCheckPrepareFlags[$tmp]=${lFlags}
			if [ ${nNumCmdParts} = 2 ]; then
			    apgmCheckPrepareArg1[$tmp]=${aCmdParts[1]}
			elif [ ${nNumCmdParts} -gt 2 ]; then
			    showMsgParseErr "check.prepare.replace_STIMPTEST_envvars: too many arguments"
			    exitcode=$EXIT_PARSE
			fi
			continue
			;;
		    run.*)
			op='program'
			pgmtype="${aCmdParts[0]:4}"
			arrprefix='apgmCheckPrepare'
			[ "${lFlags}" == '/' ] && lFlags=''
			;;
		    *)
			showMsgParseErr "invalid key:check.prepare.${aCmdParts[0]}"
			exitcode=$EXIT_PARSE
			continue
			;;
		esac
		;;
	    check.run.*)
		op='program'
		pgmtype="${aCmdParts[0]:10}"
		arrprefix='apgmCheckCustom'
		[ "${lFlags}" == '/' ] && lFlags=''
		;;
	    cleanup.run.*)
		op='program'
		pgmtype="${aCmdParts[0]:12}"
		arrprefix='apgmCleanup'
		[ "${lFlags}" == '/' ] && lFlags=''
		;;
	    *)
		showMsgParseErr "invalid key:${aCmdParts[0]}"
		exitcode=$EXIT_PARSE
		continue
		;;
	esac
	if [ "${op}" = 'program' ]; then
	    parseProgram ${arrprefix} "${pgmtype}" "${aCmdParts[1]}" "${aCmdParts[2]}" "${lFlags}" \
		${nNumCmdParts}
	    st=$?
	    [ $st != 0 -a $exitcode != $EXIT_PARSE ] && exitcode=$st
	    continue
	fi
	if [ $pvX ]; then
	    # En nyckel har kännts igen och ska behandlas.
	    # Kolla syntax.
	    if [  "${typeArg1}" -a -z "${aCmdParts[1]}" -o ! "${typeArg1}" -a -n "${aCmdParts[1]}" ] ||
		[ "${typeArg2}" -a -z "${aCmdParts[2]}" -o ! "${typeArg2}" -a -n "${aCmdParts[2]}" ]; then
		showMsgParseErr "${sSyntaxMsg}"
		return $EXIT_PARSE
	    fi
	    case $typeArg1 in
		str)
		    ;;
		uintexpr)
		    if [ "${aCmdParts[1]::1}" = '!' ]; then
			tmp="${aCmdParts[1]:1}"
			aCmdParts[1]='!'
		    else
			tmp="${aCmdParts[1]}"
			aCmdParts[1]=''
		    fi
		    if [[ ! "$tmp" =~ ^[0-9]+$ ]]; then
			showMsgParseErrNotUInt "$tmp"
			exitcode=$EXIT_PARSE
			continue
		    fi
		    aCmdParts[1]="${aCmdParts[1]}${tmp}"
		    ;;
		file)
		    aCmdParts[1]=$(absFileName "$dirHome" "${aCmdParts[1]}")
		    if [ ! -f "${aCmdParts[1]}" ]; then
			showMsgParseErrNotFile "${aCmdParts[1]}"
			[ $exitcode = 0 ] && exitcode=$EXIT_FILE
			continue
		    fi
		    dir=$(dirname "${aCmdParts[1]}")
		    file=$(basename "${aCmdParts[1]}")
		    aCmdParts[1]="$dir/$file"
		    ;;
		dir)
		    aCmdParts[1]=$(absFileName "$dirHome" "${aCmdParts[1]}")
		    if [ ! -d "${aCmdParts[1]}" ]; then
			showMsgParseErrNotDir "${aCmdParts[1]}"
			[ $exitcode = 0 ] && exitcode=$EXIT_FILE
			continue
		    fi
		    aCmdParts[1]=$(realpathBash "${aCmdParts[1]}")
		    ;;
		*)
		    showMsgInternalError 'parse' 'parseTestCase' "typeArg1=${typeArg1}"
		    return $EXIT_INTERNALERR
		    ;;
	    esac
	    # Set the variable !pvX to the value.
	    if [ "$op" = 'append' ]; then
		eval $pvX="\"${!pvX}$sAppSep${aCmdParts[1]}\""
	    else
		eval $pvX="\"${aCmdParts[1]}\""
	    fi
	    # Update SIMPTEST_HOME if the variable updated is dirHome.
	    if [ "${pvX}" = 'dirHome' ]; then
		export SIMPTEST_HOME=${dirHome}
	    fi
	fi
    done
# D #
    sTestCaseId="${sApplication}/${sName}"
# E #
    return $exitcode
}

###############################################################################
# - runTestCase -
#
#   Kör ett testfall.
#
#
# A. Change directory to the test directory.
# B. Sätt miljövariabler.
#    1. Sätt standardvariablerna.
#    2. Sätt miljövariabler angivna i testfallet.
# C. Utför testkommandot "env" om det har angivits.
#    Avsluta genom att ta bort de temporära testkatalogerna (även om CLAna
#    har angivit att de ska bevaras) och returnera 0.
# D. Utför 'setup'.
#    1. setup.install
#    2. setup.run
#    3. Om testkommandot är 'setup' ska vi avsluta här.
# E. Utför 'precond'.
# F. Utför 'test.run'.
#    Flera kommandon kan vara angivna. Alla ska köras som en gemensam process
#    med gemensam stdin, stdout och stderr.
#    F1. Loggning.
#    F2. Kör programmen i separat process.
#    F3. Spara exitkoden.
# G. Utför check.* (if not bDebugPrint is set).
#    1. Utför 'check.exitcode'.
#    2. Utför 'check.prepare'.
#    3. Utför 'check.{stdout,stderr}'.
#       Put the name of the variable holding the filename in 'pFileNameVar'.
#       Then we can handle check.stdout and check.stderr by common code.
#    4. Utför 'check.compare.eq'.
#    5. Utför 'check.custom'.
# H. Utför 'cleanup'.
# I. Testet har lyckats. Avsluta utan att skriva ut något (förr skrevs
#    "SUCCESS" ut här. Om det ska vara så igen ska det läggas in här.)
###############################################################################
function runTestCase
(
    ### A ###
    cd $TMP_ROOT/test
    ### B ###
    # 1 #
    export SIMPTEST_HOME="$dirHome"
    export SIMPTEST_TESTROOT=$TMP_ROOT/test
    export SIMPTEST_STDOUT=$TMP_ROOT/data/std/stdout
    export SIMPTEST_STDERR=$TMP_ROOT/data/std/stderr
    # 2 #
    showMsgStepBegin 'env'
    for i in ${!aEnvCmds[@]} ; do
	eval "${aEnvCmds[$i]}" 2>> "$fileLoggErr"
	if [ $? != 0 ]; then
	    showMsgStepFinish 'NONTEST_ERROR' 'env'
	    exit $EXIT_NONTEST_ERROR
	fi
    done
    ### C ###
    if [ "${cmdTest}" = 'env' ]; then
	testCommandEnv
	exit 0
    fi
    ### D ###
    # .1 #
    for i in ${!aSetupInstall_src[@]} ; do
	showMsgStepBegin 'setup.install' "${aSetupInstall_src[$i]}:${aSetupInstall_dst[$i]}"
	cp -rHLp ${aSetupInstall_src[$i]} ${aSetupInstall_dst[$i]:-.}
	if [ $? != 0 ]; then
	    showMsgStepFinish 'NONTEST_ERROR' 'setup'
	    exit $EXIT_NONTEST_ERROR
	fi
    done

    # .2 #
    for i in ${!apgmSetupRun_Type[@]} ; do
	showMsgStepBegin 'setup.run' "${apgmSetupRun_Cmd[$i]}"
	runProgramInSubProc "${apgmSetupRun_Type[$i]}" "${apgmSetupRun_Interp[$i]}" \
	    "${apgmSetupRun_Cmd[$i]}" 2>> "$fileLoggErr" >> "$fileLoggOut"
	if [ $? != 0 ]; then
	    showMsgStepFinish 'NONTEST_ERROR' 'setup'
	    exit $EXIT_NONTEST_ERROR
	fi
    done
    # .3 #
    if [ "$cmdTest" = 'stop-after-setup' ]; then
	exit
    fi

    ### E ###

    for i in ${!apgmPrecondType[@]} ; do
	showMsgStepBegin 'precond' "${apgmPrecondCmd[$i]}"
	runProgramInSubProc "${apgmPrecondType[$i]}" "${apgmPrecondInterp[$i]}" \
	    "${apgmPrecondCmd[$i]}" 2>> "$fileLoggErr" >> "$fileLoggOut"
	if [ $? != 0 ]; then
	    showMsgStepFinish 'PRECOND' 'precond'
	    exit $EXIT_PRECOND
	fi
    done

    ### F ###

    # .1 #
    showMsgStepBegin 'test.run'
    # .2 #
    (
	for i in ${!apgmTestRunType[@]}; do
	    type="${apgmTestRunType[$i]}"
	    interp="${apgmTestRunInterp[$i]}"
	    cmd="${apgmTestRunCmd[$i]}"
	    logMsg $(stepMsg 'test.run' "${cmd}")
	    runProgramInSameProc "$type" "$interp" "$cmd"
	done
    )  < "$fileTestStdin" > ../data/std/stdout 2> ../data/std/stderr
    # .3 #
    exitcode=$?

    ### G ###

    if [ ! "${bDebugPrint}" ]; then
        # .1 #
	if [ -n "${uieCheckExitCode}" ]; then
	    showMsgStepBegin 'check.exitcode' "${uieCheckExitCode}"
	    if ! evalUiExpr "$uieCheckExitCode" $exitcode ; then
		showMsgStepFinish 'FAIL' 'check.exitcode' $exitcode
		exit $EXIT_FAIL
	    fi
	fi
        # .2 #
	for i in ${!apgmCheckPrepareType[@]} ; do
	    if [ ${apgmCheckPrepareType[$i]} = 'REPLACE-ENVVARS' ]; then
		showMsgStepBegin 'check.prepare' 'replace-SIMPTEST-envvars'
		runReplace_SIMPTEST_envvars "${apgmCheckPrepareFlags[${i}]}" \
		    "${apgmCheckPrepareArg1[${i}]}"
	    else
		showMsgStepBegin 'check.prepare' "${apgmCheckPrepareCmd[$i]}"
		runProgramInSubProc \
		    "${apgmCheckPrepareType[$i]}"   \
		    "${apgmCheckPrepareInterp[$i]}" \
		    "${apgmCheckPrepareCmd[$i]}"    \
		    >> "$fileLoggOut" 2>> "$fileLoggErr"
	    fi
	    if [ $? != 0 ] ; then
		showMsgStepFinish 'NONTEST_ERROR' 'check.prepare'
		exit $EXIT_NONTEST_ERROR
	    fi
	done
        # .3 #
	local idx ch pFileNameVar sVarChPart
	for idx in ${!check_channel__checkType[@]}; do
	    ch=${check_channel__channel[${idx}]}
	    showMsgStepBegin "check.${ch}"
	    sVarChPart=$(echo ${ch} | tr [a-z] [A-Z])
	    pFileNameVar="SIMPTEST_${sVarChPart}"
	    if containsWordComma "${check_channel__lFlags[${idx}]}" 'replaced' ; then
		pFileNameVar="SIMPTEST_${sVarChPart}_REPLACED"
		if [ ! "${!pFileNameVar}" ]; then
		    showMsgStepFinish 'NONTEST_ERROR' "check.${ch}/replaced" \
			"replace-SIMPTEST-envvars/${ch} has not been run"
		    exit ${EXIT_NONTEST_ERROR}
		fi
	    fi
	    checkFileContents "check.${ch}" ${check_channel__checkType[${idx}]} \
		"${!pFileNameVar}" "${check_channel__file[${idx}]}"
	done
        # .4 #
	for i in ${!aCheckCmpEq_Flags[@]} ; do
	    checkCompareEq "${aCheckCmpEq_Src[$i]}" "${aCheckCmpEq_Dst[$i]}" \
		"${aCheckCmpEq_Flags[$i]}"
	done

        # .5 #
	for i in ${!apgmCheckCustomCmd[@]} ; do
	    showMsgStepBegin 'check.custom' "${apgmCheckCustomCmd[$i]}"
	    type="${apgmCheckCustomType[$i]}"
	    interp="${apgmCheckCustomInterp[$i]}"
	    cmd="${apgmCheckCustomCmd[$i]}"
	    runProgramInSubProc "$type" "$interp" "$cmd" \
		>> "$fileLoggOut" 2>> "$fileLoggErr"
	    if [ $? != 0 ] ; then
		showMsgStepFinish 'FAIL' 'check.custom'
		exit $EXIT_FAIL
	    fi
	done
    fi
    ### H ###
    for i in ${!apgmCleanupCmd[@]} ; do
	showMsgStepBegin 'cleanup' "${apgmCleanupCmd[$i]}"
	type="${apgmCleanupType[$i]}"
	interp="${apgmCleanupInterp[$i]}"
	cmd="${apgmCleanupCmd[$i]}"
	runProgramInSubProc "$type" "$interp" "$cmd" \
	    >> "$fileLoggOut" 2>> "$fileLoggErr"
    done
    ### I ###
    if [ -n "${bDebugPrint}" ]; then
	exit $exitcode
    fi
)

# A filter that removes all comments using the builtin `read'.
function stripCommentsAndEmptyLines
(
    IFS='#'
    while read sLine sComment; do
	[[ "${sLine}" =~ ^[[:blank:]]*$ ]] || echo "${sLine}"
    done
)

###############################################################################
#   Preprocess the test case file (m4 and uncommenting).
#   Do the m4 preprocessing with PWD as the directory where the test case file
# is (so that m4 file inclusion work - filenames should be relative this
# directory).
#   Exit with exitcode ${EXIT_NONTEST_ERROR} if preprocessing fails.
#
# Uses: bM4             - If m4 preprocessing should be done.
# Uses: wslM4_options   - Options to pass to m4 if m4 preprocessing should be
#                         done.
# Uses: fileLoggParseTc - Loggs mesages to this file.
#
# VARIABLES
#  * n
#    The next number for the file to produce.
#  * filePrevious
#    The filename of the file resulting from the previous step - the file
#    to process in this step.
#
# A. Produce the original file and set 'filePrevious' to it's name.
#    Initialize 'n' to 1.
# B. Do m4 preprocessing if this should be done.
#    1. Change directory to that of the test case file (if not reading
#       from stdin).  Push the current on the directory stack.
#    2. Set the filename and "start" the step.
#    3. If we are testing the preprocessing, do the preprocessing without
#       redirections of output and exit with the exit code from m4.
#    4. Run m4.
#    5. Pop back directory.
#    6. Update 'filePrevious'.
# C. Strip comments.
# D. Copy the previous file to final.simptestcase.  Also set 'fileTcFinal'
#    to the name of this last file.
###############################################################################
function preprocessTestCase # <test case file>
{
    local fileTc=${1}
    # A #
    local filePrevious=${dirTestCasePreprocessed}/original.simptestcase
    if [ "_${1}" == '_-' ]; then
	cp /dev/stdin ${filePrevious} 2>> ${fileLoggParseTc}
	[ $? != 0 ] && preprocessError 'cp'
    else
	cp ${fileTc} ${filePrevious} 2>> ${fileLoggParseTc}
	[ $? != 0 ] && preprocessError 'cp'
    fi
    local n=1
    # B #
    if [ ${bM4} ]; then
	# 1 #
	if [ "_${1}" != '_-' ]; then
	    pushd . > /dev/null
	    cd $(dirname "${1}")
	else
	    pushd . > /dev/null
	fi
	# 2 #
	local fileTcPostM4=${dirTestCasePreprocessed}/${n}-post-m4.simptestcase
	let ++n
	showPreprocessStepStart m4 $wslM4_options '<' "${filePrevious}" '>' "${fileTcPostM4}"
	# 3 #
	if [ "${cmdTest}" = 'm4' ]; then
	    m4 ${wslM4_options} < "${filePrevious}"
	    doExit $?
	fi
	# 4 #
	m4 ${wslM4_options} < "${filePrevious}" > "${fileTcPostM4}" 2>> ${fileLoggParseTc}
	[ $? != 0 ] && preprocessError 'm4'
	# 5 #
	popd > /dev/null
	# 6 #
	filePrevious=${fileTcPostM4}
    elif [ "${cmdTest}" = 'm4' ]; then
	doExit ${EXIT_SUCCESS}
    fi
    ### C ###
    local fileTcPostUncomment=${dirTestCasePreprocessed}/${n}-post-uncomment.simptestcase
    stripCommentsAndEmptyLines < ${filePrevious} > ${fileTcPostUncomment} 2>> ${fileLoggParseTc}
    [ $? != 0 ] && preprocessError 'strip-comments-and-empty-lines'
    let ++n
    filePrevious=${fileTcPostUncomment}
    # D #
    fileTcFinal=${dirTestCasePreprocessed}/final.simptestcase
    cp ${filePrevious} ${fileTcFinal} 2>> ${fileLoggParseTc}
}

###############################################################################
# - main -
###############################################################################

###############################################################################
#
# A. Read Command Line Arguments and set variables:
#       * sTestProcId
#       * dirHome
#       * fileTestCase
#       * bKeep
#       * bDebugPrint
#       * bAppendName
#       * bVerb
#       * dirLoggsRoot
#       * bM4           - If the testcase should be preprocessed by m4.)
#       * wslM4_options - Options to pass to m4 if it should be run.
#       * bNoPreproc
#    Quit if wrong usage or if the test case file (does not exist or is not
#    readable).
#   A.1. Initiera variabler.
#   A.1. Odefiniera CDPATH för 'realpathBash'.
#   A.1. Initiera diverse annat!
#   A.2. Använd getopt för att läsa CLAer, tolka dem med en while - case -
#        slinga.
#   A.3. Läs CLAer för testning om sådana angivits.
#   A.4. Avslutar om fel användning.
#        Ett argument - testfallsfilen - måste anges.
#   A.5. Sätt 'fileTestCase' och 'dirHome'
#        Om en absolut sökväg har angivits ska den användas som 'dirHome', om
#        en relativ har angivits ska den läggas till aktuell sökväg. Om ingen
#        katalog anges i sökvägen returnerar 'dirname' ".".
# B. Create the test temporary directory structure.
# C. Initialize variables.
# D. Preprocess the test case file. Generate the files in testcase.
#    Set 'fileTcFinal' to the absolute name of the preprocessed test case file.
#    Change directory to that of the test case file (if it is not stdin)
#    before preprocessing (needed for m4 file inclusion to work).
#    Change back to the original directory afterwards.
# E. Parse the test case and execute the env commands.
#    Läs testfallsfilen och utför testkommandot "env-cmds" om det ska göras.
#    1. Läs testfallsfilen, avsluta om inläsningen misslyckades.
#    2. Utför testkommandona 'env-cmds' eller 'programs' om något av dem
#        angivits.
# F. Kontrollera att testfallet innehåller tillräcklig information för att
#    utgöra ett test. Avsluta om det inte gör det.
# G. Utför testet.
# H. If bDebugPrint or bPrintLogs, print "non-normal output".
#    If bPrintLogs, print the logs, otherwise, if bDebugPrint, print stdout
#    and stderr from the test commands.
# I. Testet klart. Avsluta.
###############################################################################

### A ###

readonly opts="-o 4egknvV -l exec,version,m4,m4-options:,no-preproc,print-logs,xmldiff:"
readonly swGetoptTest="-n simptestcase -o c: -l help"

readonly sTestProcId=$(date +%y%m%d+%H%M)-$$

# A1.1 #

unset CDPATH

# A1.2 #

dirLoggsRoot=
bVerb=
bKeep=
bAppendName=
wslM4_options='--prefix-builtins --fatal-warnings'

# A.2 #

args=$(getopt -n $(basename $0) $opts -- "$@")

[ $? != 0 ] && exitMsgInvoc "$sUsage"

eval set -- "$args"

while [ "_${1}" != '_--' ] ; do
    case "${1}" in
	-g) dirLoggsRoot=${SIMPTEST_LOGS:-~/.simptest/logs} ;;
	-k) bKeep=1 ;;
	-n) bAppendName=1 ;;
	-e | --exec)
	    bDebugPrint=1 ;;
	--print-logs)
	    bPrintLogs=1 ;;
	-v)
	    if [ "$bVerb" ]; then
		bVerbVerb=1
	    else
		bVerb=1
	    fi
	    ;;
	-V | --version)
	    echo $VERSION
	    exit 0 ;;
	-4 | --m4)
	    bM4=1 ;;
	--m4-options)
	    wslM4_options=${2}; shift ;;
	--xmldiff)
	    sPgmXmldiff="${2}"; shift ;;
	--no-preproc)
	    bNoPreproc=1 ;;
    esac
    shift
done
shift
readonly bKeep bAppendName bVerb dirLoggsRoot

# A.3 #

if [ "$1" = 'test:' ]; then
    shift
    bTest=1
    args=$(getopt $swGetoptTest -- "$@")

    [ $? != 0 ] && printfExit "$msgInvalidTestUsage"
    eval set -- "$args"
    while [ "x$1" != 'x--' ]; do
	case "$1" in
	    --help)
		printfExit0 "$msgTestHelp" ;;
	    -c)
		if ! containsWordComma "$cslTestCommands" "$2" ; then
		    printfExit1 "$msgInvalidTestCommand" "$2"
		fi
		cmdTest=$2
		shift
	esac
	shift
    done
    shift
fi

# A.4 #

[ $# != 1 ] && exitMsgInvoc "$sUsage"

# A.5 #

fileTestCase="$1"
if [ "$fileTestCase" = '-' ]; then
    fileTestCase=/dev/stdin
    dirHome="$PWD"
else
    [ ! -f "$fileTestCase" ] && exitMsgInvoc "not a file: $fileTestCase"
    [ ! -r "$fileTestCase" ] && exitMsgInvoc "file not readable: $fileTestCase"
    dir=$(dirname "$fileTestCase")
    if [ "$dir" = '.' ]; then
	dirHome="$PWD"
    elif [ ${dir::1} = '/' ]; then
	dirHome="$dir"
    else
	dirHome=$(realpathBash "$PWD/$dir")
    fi
    unset dir
fi

### B ###

mkTestDirs

### C ###

sApplication=
sName=

declare -a apgmSetupRun_Type
declare -a apgmSetupRun_Interp
declare -a apgmSetupRun_Cmd

declare -a aSetupInstall_src
declare -a aSetupInstall_dst

declare -a apgmPrecondType
declare -a apgmPrecondInterp
declare -a apgmPrecondCmd

declare -a apgmTestRunType
declare -a apgmTestRunInterp
declare -a apgmTestRunCmd

declare -a apgmCheckPrepareType
declare -a apgmCheckPrepareInterp
declare -a apgmCheckPrepareCmd
declare -a apgmCheckPrepareFlags
declare -a apgmCheckPrepareArg1

declare -a apgmCheckCustomType
declare -a apgmCheckCustomInterp
declare -a apgmCheckCustomCmd

declare -a aCheckCmpEq_Flags
declare -a aCheckCmpEq_Src
declare -a aCheckCmpEq_Dst

declare -a check_channel__channel
declare -a check_channel__checkType
declare -a check_channel__lFlags
declare -a check_channel__file

declare -a aEnvCmds

uieCheckExitCode=
fileTestStdin=/dev/null
fileCheckStdout=
fileCheckStderr=


### D ###


if [ "${bNoPreproc}" ]; then
    fileTcFinal="${fileTestCase}"
else
    preprocessTestCase "${fileTestCase}"
fi


### E ###

# .1 #

parseTestCase < "${fileTcFinal}"
st=$?

if [ $st != 0 ]; then
    case $st in
	$EXIT_PARSE)
	    showMsgStepFinish 'PARSE' ;;
	$EXIT_FILE)
	    showMsgStepFinish 'FILE' ;;
    esac
    doExit $st
fi

# .2 #

case "${cmdTest}" in
    'env-cmds')
	for i in ${!aEnvCmds[@]} ; do
	    echo "${aEnvCmds[$i]}"
	done
	doExit 0
	;;
    'stop-after-parse')
	doExit 0
	;;
    'programs')
	test_printPrograms
	doExit 0
	;;
esac


### F ###


msg=$(testcaseIsComplete)
if [ $? != 0 ]; then
    showMsgParseErr "cannot run test:$msg"
    showMsgStepFinish 'PARSE'
    doExit $EXIT_PARSE
fi


### G ###


runTestCase
st=$?


### H ###


if [ -n "${bPrintLogs}" ]; then
    [ -e "${fileLoggOut}" ] && cat "${fileLoggOut}"
    [ -e "${fileLoggErr}" ] && cat "${fileLoggErr}" >&2
elif [ -n "${bDebugPrint}" ]; then
    [ -e ${dirDataStd}/stdout ] && cat ${dirDataStd}/stdout
    [ -e ${dirDataStd}/stderr ] && cat ${dirDataStd}/stderr >&2
fi


### I ###


if [ $st = ${EXIT_INTERNALERR} ]; then
    echo "(see logs for details)"
    echo "test root kept:$TMP_ROOT"
    exit ${EXIT_INTERNALERR}
else
    doExit $st
fi
