#!/bin/bash
# Create environments for the notebooks to run in
# Download the notebook repo and use the requirement files
set -e 
set -o pipefail

resolve_references() {
    local file="$1"
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^-r(.+)$ ]]; then
            ref_file="${BASH_REMATCH[1]}"
            if [[ -f "$ref_file" ]]; then
                resolve_references "$ref_file"
            fi
        else
            echo "$line"
        fi
    done < "$file"
}

cd /tmp/
git clone --depth 1 https://github.com/nasa-fornax/fornax-demo-notebooks.git

if [ -d build ]; then rm -rf build; fi
mkdir build
find fornax-demo-notebooks -type f -name "requirements_*txt" -exec cp {} build/ \;
cd build

for req in `ls requirements_*`; do
    # de-reference -r{filename}
    reqlow=${req,,}
    resolve_references "$req" > "${reqlow/requirements_/requirements-py-}"
done

rm requirements_*
# pin numpy<2.3; issue: https://github.com/nasa-fornax/fornax-demo-notebooks/issues/431
sed -i 's/numpy$/numpy<2.3/' requirements-py-ml_agnzoo.txt
bash /usr/local/bin/uv-env-install.sh 

cd /tmp/
rm -rf fornax-demo-notebooks build
uv cache clean