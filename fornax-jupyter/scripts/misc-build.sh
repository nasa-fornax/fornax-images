#!/bin/bash

# Cateogry in the JL Launcher
CATEGORY=Tools

## -------------------------------------------------------- ##
# Patch vs-code extnesion so the icon shows up under Other
vsfile=`ls $JUPYTER_DIR/lib/python*/site-packages/jupyter_vscode_proxy/__init__.py`
if [ -f "$vsfile" ] && ! grep -q '"category":' "$vsfile"; then
    # Use awk to insert the line safely and maintain indentation
    awk -v cat_str="            \"category\": \"$CATEGORY\"," '
        /"title": "VS Code",/ {
            print $0
            print cat_str
            next
        }
        { print }
    ' "$vsfile" > "${vsfile}.tmp" && mv "${vsfile}.tmp" "$vsfile"
    
    echo "Patched category in vs-code extension."
fi
## -------------------------------------------------------- ##

## ------------------------------ ##
## Patch the Firefly category too
# This is done in the js static files
# It has the form: ?="Firefly" -> ?="$CATEGORY"
fname=`grep -rl --include="*.js" '="Firefly"' $JUPYTER_DIR/share/jupyter/labextensions/jupyter_firefly_extensions`
if [ -f "$fname" ]; then
    sed -i "s/\([a-zA-Z]\)=\"Firefly\"/\1=\"$CATEGORY\"/g" "$fname"
fi
## ------------------------------ ##

## Rebuild jupyter lab cache ##
## we need node
# curl -sSOL https://nodejs.org/dist/v24.18.0/node-v24.18.0-linux-x64.tar.xz
# tar -xf node-*.tar.xz
# nodedir=`ls -d $PWD/node-*x64/`
# export PATH=$nodedir/bin:$PATH
# jupyter lab clean
# jupyter lab build
# rm -rf $nodedir node-*xz
(timeout 20s start-notebook.py || true)
## ------------------------- ##

