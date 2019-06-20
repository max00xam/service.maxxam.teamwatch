#!/bin/bash
# nothing to see here, just a utility i use to create new releases ^_^
# edit from https://github.com/bettercap/bettercap/blob/master/release.sh

TO_UPDATE=(
    service.py
)

echo -n "Select current version: "
read CURRENT_VERSION
echo -n "Current version is $CURRENT_VERSION, select new version: "
read NEW_VERSION
echo "Creating version $NEW_VERSION ...\n"

if [ -z ${TO_UPDATE+x} ]; then
    git add *
    #echo -n "-"
else
    for file in "${TO_UPDATE[@]}"
    do
        echo "Patching $file ..."
        sed -i "s/$CURRENT_VERSION/$NEW_VERSION/g" $file
        git add $file
    done
fi

#git commit -m "Releasing v$NEW_VERSION"
#git push

#git tag -a v$NEW_VERSION -m "Release v$NEW_VERSION"
#git push origin v$NEW_VERSION

echo
echo "Released on github"

echo
echo "All done, v$NEW_VERSION released ^_^"
