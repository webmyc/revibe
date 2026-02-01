#!/usr/bin/env node

/**
 * Revibe npm wrapper
 * 
 * This is a thin Node.js shim that calls the Python revibe package.
 * It handles Python detection, package installation, and argument forwarding.
 */

const { execSync, spawn } = require('child_process');

// Check if Python 3 is available
function findPython() {
    const candidates = ['python3', 'python'];

    for (const cmd of candidates) {
        try {
            const version = execSync(`${cmd} --version 2>&1`, {
                encoding: 'utf8',
                stdio: ['pipe', 'pipe', 'pipe']
            });
            if (version.includes('Python 3.')) {
                // Verify it's at least 3.9
                const match = version.match(/Python 3\.(\d+)/);
                if (match && parseInt(match[1]) >= 9) {
                    return cmd;
                }
            }
        } catch {
            // Command not found or errored, try next
        }
    }
    return null;
}

// Check if revibe Python package is installed
function isRevibeInstalled(python) {
    try {
        execSync(`${python} -c "import revibe"`, {
            stdio: ['pipe', 'pipe', 'pipe']
        });
        return true;
    } catch {
        return false;
    }
}

// Install revibe Python package
function installRevibe(python) {
    console.log('📦 Installing revibe Python package...');

    // Try normal install first
    try {
        execSync(`${python} -m pip install revibe --quiet`, {
            stdio: 'inherit'
        });
        return true;
    } catch {
        // Try with --break-system-packages for newer Python/pip
        try {
            execSync(`${python} -m pip install revibe --quiet --break-system-packages`, {
                stdio: 'inherit'
            });
            return true;
        } catch {
            // Try user install
            try {
                execSync(`${python} -m pip install revibe --quiet --user`, {
                    stdio: 'inherit'
                });
                return true;
            } catch (e) {
                console.error('❌ Failed to install revibe Python package');
                console.error('   Try manually: pip install revibe');
                return false;
            }
        }
    }
}

// Main execution
function main() {
    // Find Python
    const python = findPython();

    if (!python) {
        console.error('❌ Revibe requires Python 3.9+');
        console.error('');
        console.error('   Install Python from: https://www.python.org/downloads/');
        console.error('   Or use pip directly: pip install revibe');
        process.exit(1);
    }

    // Check if revibe is installed
    if (!isRevibeInstalled(python)) {
        if (!installRevibe(python)) {
            process.exit(1);
        }
    }

    // Forward all arguments to the Python package
    const args = process.argv.slice(2);

    const child = spawn(python, ['-m', 'revibe', ...args], {
        stdio: 'inherit',
        env: process.env,
    });

    child.on('error', (err) => {
        console.error(`❌ Failed to run revibe: ${err.message}`);
        process.exit(1);
    });

    child.on('exit', (code) => {
        process.exit(code ?? 1);
    });
}

main();
