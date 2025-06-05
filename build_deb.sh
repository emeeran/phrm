#!/bin/bash
set -euo pipefail

# Configuration
PACKAGE_NAME="phrm"
VERSION=$(python3 -c "from app import __version__; print(__version__)")
ARCHITECTURE="all"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="Personal Health Record Management System"
DEPENDENCIES="python3, python3-pip, python3-venv"

# Clean previous builds
cleanup() {
    echo "Cleaning up previous builds..."
    rm -rf debian/ ${PACKAGE_NAME}_*.deb ${PACKAGE_NAME}_*.changes ${PACKAGE_NAME}_*.buildinfo
}

# Create Debian package structure
create_debian_structure() {
    echo "Creating Debian package structure..."
    mkdir -p debian/DEBIAN
    mkdir -p debian/usr/lib/${PACKAGE_NAME}
    mkdir -p debian/usr/bin
    mkdir -p debian/etc/${PACKAGE_NAME}
}

# Generate control file
generate_control_file() {
    echo "Generating control file..."
    cat > debian/DEBIAN/control <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Architecture: ${ARCHITECTURE}
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
Depends: ${DEPENDENCIES}
EOF
}

# Copy application files
copy_application_files() {
    echo "Copying application files..."
    cp -r app/ debian/usr/lib/${PACKAGE_NAME}/
    cp run.py debian/usr/lib/${PACKAGE_NAME}/
    cp requirements.txt debian/usr/lib/${PACKAGE_NAME}/
    
    # Create executable symlink
    ln -s /usr/lib/${PACKAGE_NAME}/run.py debian/usr/bin/${PACKAGE_NAME}
}

# Set permissions
set_permissions() {
    echo "Setting permissions..."
    chmod -R 755 debian/DEBIAN
    find debian/ -type d -exec chmod 755 {} \;
    find debian/ -type f -exec chmod 644 {} \;
    chmod 755 debian/usr/bin/${PACKAGE_NAME}
    chmod 755 debian/usr/lib/${PACKAGE_NAME}/run.py
}

# Build the package
build_package() {
    echo "Building Debian package..."
    dpkg-deb --build debian/
    mv debian.deb ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb
    echo "Package built: ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
}

# Main execution
main() {
    cleanup
    create_debian_structure
    generate_control_file
    copy_application_files
    set_permissions
    build_package
}

main "$@"