from pathlib import Path

import make_lib as mk

########################################
# Programs
########################################

ADD_TXT_SUFFIX = 'add-txt-suffix-to-file-paths'

########################################
# Directories
########################################


SUB_DIR_CONFIGS = [
    ('scripts',
     [
         mk.SourceAndTarget(Path('scripts') / 'src' / ADD_TXT_SUFFIX,
                            Path(ADD_TXT_SUFFIX))
     ]),
]

if __name__ == '__main__':
    mk.main(SUB_DIR_CONFIGS)
