#!/bin/bash

timeout=10

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; returning ..."
    return 0
fi


notebook_repos=(
    # main demo notebooks
    https://github.com/nasa-fornax/fornax-demo-notebooks.git
)

# Branch to pull from, preferably a curated, deployed branch rather than the development default
deployed_branches=(
    deployed_notebooks
)

mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $NOTEBOOK_DIR ..."

for i in ${!notebook_repos[@]}; do
    repo=${notebook_repos[i]}
    branch=${deployed_branches[i]}
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`
    echo "++++ Updating $name from $repo ..."
    if [ -d $name ]; then
        # first ensure we can delete it
        find $name -type d -exec chmod 755 {} +
        find $name -type f -exec chmod 644 {} +
        # now delete
        rm -rf $name
    fi
    # get a fresh clone of the the repo
    git clone --branch $branch --single-branch --depth 1 $repo
    rm -rf $name/.git
    echo "+++++ Done with $name!"
done

# bring in the intro and release notes page
if test -f $JUPYTER_DIR/introduction.md && ! test -L $NOTEBOOK_DIR/introduction.md; then
    cp $JUPYTER_DIR/introduction.md $NOTEBOOK_DIR
fi
if test -f $JUPYTER_DIR/changes.md && ! test -L $NOTEBOOK_DIR/changes.md; then
    cp $JUPYTER_DIR/changes.md $NOTEBOOK_DIR
fi

# Now make the notebooks files read-only
cd $NOTEBOOK_DIR
for i in ${!notebook_repos[@]}; do
    repo=${notebook_repos[i]}
    branch=${deployed_branches[i]}
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`

    find $name -type f -exec chmod 444 {} +
done

# reset location
cd $HOME
