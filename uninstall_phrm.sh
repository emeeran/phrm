#!/bin/zsh
# Uninstall PHRM Debian package and remove all related files and data

set -e

# Remove the Debian package
echo "Removing phrm package..."
sudo dpkg --purge phrm || sudo dpkg --remove phrm

# Remove installed files and directories
echo "Removing /usr/local/phrm..."
sudo rm -rf /usr/local/phrm

echo "Removing desktop shortcut..."
sudo rm -f /usr/share/applications/phrm.desktop

# Remove logs, uploads, and database if present
echo "Removing logs, uploads, and database from /usr/local/phrm if any..."
sudo rm -rf /usr/local/phrm/logs /usr/local/phrm/uploads /usr/local/phrm/instance/ /usr/local/phrm/.env

# Remove from current workspace if present
echo "Removing local logs, uploads, and database from workspace..."
rm -rf ./logs ./uploads ./instance/ ./phrm.db ./uninstall_phrm.sh

echo "PHRM and all related files have been removed."
