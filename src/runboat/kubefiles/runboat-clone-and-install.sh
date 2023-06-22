#!/bin/bash

set -exo pipefail

# Remove initialization sentinel and data, in case we are reinitializing.
rm -fr /mnt/data/*

# Remove addons dir, in case we are reinitializing after a previously
# failed installation.
rm -fr $ADDONS_DIR
# Download the repository at git reference into $ADDONS_DIR.
# We use curl instead of git clone because the git clone method used more than 1GB RAM,
# which exceeded the default pod memory limit.
mkdir -p $ADDONS_DIR
cd $ADDONS_DIR
# Check if repo is private and use token to download
set +x
if [[ "${REPO_IS_PRIVATE}" == true ]]; then
    echo "Repo is private"
    if [[ -z "${RUNBOAT_GITHUB_TOKEN}" ]]; then
        echo "RUNBOAT_GITHUB_TOKEN is not set"
        exit
    else
        echo "Downloading RUNBOAT_GIT_REPO"
        curl -sSL https://${RUNBOAT_GITHUB_TOKEN}@github.com/${RUNBOAT_GIT_REPO}/tarball/${RUNBOAT_GIT_REF} | tar zxf - --strip-components=1
    fi
else
    curl -sSL https://github.com/${RUNBOAT_GIT_REPO}/tarball/${RUNBOAT_GIT_REF} | tar zxf - --strip-components=1
fi

# Clone Odoo Enterprise addons
ODOO_EE=runboat.ee
if test -f "$ODOO_EE"; then
    curl -sSL https://${RUNBOAT_GITHUB_TOKEN}@github.com/cetmix/enterprise/tarball/${ODOO_VERSION} | tar zxf - --strip-components=1 -C ${ADDONS_PATH}
fi

# Install additional repos. NB: will be cloned in the same repo as addons. Use with care!
ADDITIONAL_REPOS=github.json
if test -f "$ADDITIONAL_REPOS"; then
    mkdir tmp-addons
    cd tmp-addons
    # Clone GithubClpner
    mkdir -p cetmix-python-utils
    curl -sSL https://${RUNBOAT_GITHUB_TOKEN}@github.com/cetmix/cetmix-python-utils/tarball/main | tar zxf - --strip-components=1 -C ./cetmix-python-utils
    python3 ./cetmix-python-utils/cetmix_github_cloner.py -t ${RUNBOAT_GITHUB_TOKEN} ../github.json && rm -rf ./cetmix-python-utils
    # Build setup
    find . -type d -maxdepth 2 -exec setuptools-odoo-make-default --addons-dir={} --odoo-version-override=14.0 \;
    find . -mindepth 2 -maxdepth 2 -type d -not -name '.*' -exec cp -rv {} ../ \;
    cd ../ && rm -rf tmp-addons
    ls -lah .
fi

set -x
# Install.
INSTALL_METHOD=${INSTALL_METHOD:-oca_install_addons}
if [[ "${INSTALL_METHOD}" == "oca_install_addons" ]] ; then
    oca_install_addons
elif [[ "${INSTALL_METHOD}" == "editable_pip_install" ]] ; then
    pip install -e .
else
    echo "Unsupported INSTALL_METHOD: '${INSTALL_METHOD}'"
    exit 1
fi

# Keep a copy of the venv that we can re-use for shorter startup time.
cp -ar /opt/odoo-venv/ /mnt/data/odoo-venv

touch /mnt/data/initialized
