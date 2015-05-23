#!/bin/bash

trim() {
    local files="$1"
    # Trim whitespace at end of line
    echo "$files" | xargs sed -i -e 's/[[:blank:]]\+$//'
    # Delete blank lines at end of file
    echo "$files" | xargs sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}'
}

main() {
    local files=$(find stevetags -name gen -prune -o \
        \( -name "*.py" -or -name "*.js" -or -name "*.html" -or -name "*.coffee" -or -name "*.less" -or -name "*.jinja2" \) \
        -type f -print)

    trim "$files"

    local sql_files=$(find migration -name "*.sql" -type f -print)
    trim "$sql_files"
}

main "$@"
