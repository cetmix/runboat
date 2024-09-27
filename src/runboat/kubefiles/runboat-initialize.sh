#!/bin/bash

#
# Clone repo and install all addons in the test database.
#

set -ex

bash /runboat/runboat-clone-and-install.sh

oca_wait_for_postgres

# Drop database, in case we are reinitializing.
dropdb --if-exists ${PGDATABASE}
dropdb --if-exists ${PGDATABASE}-baseonly

ADDONS=$(manifestoo --select-addons-dir ${ADDONS_DIR} --select-include "${INCLUDE}" --select-exclude "${EXCLUDE}" list --separator=,)

# Create the baseonly database if installation failed.
unbuffer $(which odoo || which openerp-server) \
  --data-dir=/mnt/data/odoo-data-dir \
  --db-template=template1 \
  -d ${PGDATABASE}-baseonly \
  -i base \
  --stop-after-init

# Try to install all addons, but do not fail in case of error, to let the build start
# so users can work with the 'baseonly' database.
if [[ -f "${ADDONS_DIR}/no_baseonly_repo" ]]; then
    echo "The 'no_baseonly_repo' file exists. Skipping the creation of the second database."
else
    unbuffer $(which odoo || which openerp-server) \
      --data-dir=/mnt/data/odoo-data-dir \
      --db-template=template1 \
      -d ${PGDATABASE} \
      -i ${ADDONS:-base} \
      --stop-after-init
fi
