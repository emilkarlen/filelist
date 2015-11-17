# -*- shell-script --*-

function exit_code # CODE MESSAGE ...
{
    local code=$1
    shift
    echo "$(basename $0): $*" >&2
    exit $code
}

function exit_error # MESSAGE ...
{
    exit_code 2 "$*"
}

function check_name # TEST-NAME
{
    if [[ "$1" =~ [/.:] ]]; then
	exit_error "Test name cannot include any of '/.: ': \`$1'"
    fi
    if [[ "$1" =~ [[:space:]] ]]; then
	exit_error "Test name cannot include space: \`$1'"
    fi
}

function log # MESSAGE
{
    echo "$(basename $0): $*" >&2
}

MV='git mv'

readonly USAGE='[-h] [-m MOVE-COMMAND] FROM TO

Renames a Simptest Test Case from FROM to TO.

Options:
  -h
     Display this help and exit.

  -m MOVE-COMMAND
     Sets the command used for moving files, default is "mv".
     Must be a command that accepts two arguments SRC DST.
     Example is to use "git mv" for moving git-managed files.

Both names are the complete base-name of the test-files.
(No directory-components are allowd.)

Files are searched for under the current directory.
So, YOU MUST STAND IN THE DIRECTORY CONTAINING ALL FILES FOR THE TEST.

The program DOES:
 1. Replace the string FROM with the string TO in all "related files".
 2. Renames all "related files" - FROM is replaced with TO in the base-names.

"Related files" are those whos basename is FROM.*'

while getopts "hm:" o; do
    case "${o}" in
        h)
	    exit_code 0 "$USAGE"
            ;;
        m)
            MV="${OPTARG}"
            ;;
        *)
            exit_error "$USAGE"
            ;;
    esac
done
shift $((OPTIND-1))

if [ $# != 2 ]; then
    exit_error "$USAGE"
fi

readonly from="$1"
readonly to="$2"

check_name "$from"
check_name "$to"

log 'Replacing test-name in files ...'
find . -name "$from"'.*' | while read fn; do
    log ex -s -c "%s:$from:$to:g" -c x $fn
        ex -s -c "%s:$from:$to:g" -c x $fn
done
log 'Renaming files ...'
find . -name "$from"'.*' | while read fn; do
    dst=${fn/$from/$to}
    log $MV $fn $dst
        $MV $fn $dst
done