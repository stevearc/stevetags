#!/bin/bash -e

dl () {
    local name=$1
    local url=$2
    local args=
    if [ "$url" ]; then
        args="-O $name"
    else
        url="$name"
        name=$(basename "$name")
    fi
    if [ ! -e "$name" ]; then
        wget -O "$name" "$url"
    fi
}

main() {
    go get github.com/stevearc/pike
    pushd $(dirname $0) > /dev/null
    mkdir -p stevetags/static/lib
    pushd stevetags/static/lib > /dev/null
    if [ "$1" == "-r" ]; then
        rm -rf *
    fi

    dl https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.10.3/moment.min.js

    dl http://code.jquery.com/jquery-2.1.4.min.js
    local ng_version=1.3.15
    dl http://code.angularjs.org/$ng_version/angular.min.js
    dl http://code.angularjs.org/$ng_version/angular-touch.min.js
    dl http://code.angularjs.org/$ng_version/angular-route.min.js
    dl https://angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.min.js
    dl https://raw.githubusercontent.com/ftlabs/fastclick/3497d2e92ccc8a959c7efb326c0fc437302d5bcf/lib/fastclick.js
    dl https://raw.github.com/BinaryMuse/ngInfiniteScroll/1.0.0/build/ng-infinite-scroll.min.js

    local bs_version=3.1.1
    if [ ! -e bootstrap-$bs_version ]; then
        dl https://github.com/twbs/bootstrap/archive/v${bs_version}.zip
        unzip v${bs_version}.zip
        rm v${bs_version}.zip
        find bootstrap-${bs_version} -mindepth 1 -maxdepth 1 \( -not -name "fonts" -and -not -name "less" \) | xargs rm -r
    fi
    local fa_version=4.3.0
    if [ ! -e font-awesome-$fa_version ]; then
        dl http://fontawesome.io/assets/font-awesome-$fa_version.zip
        unzip font-awesome-$fa_version.zip
        rm font-awesome-$fa_version.zip
        find font-awesome-$fa_version -mindepth 1 -maxdepth 1 \( -not -name "fonts" -and -not -name "css" \) | xargs rm -r
    fi

    popd > /dev/null
    popd > /dev/null
}

main "$@"
