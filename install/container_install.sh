#!/usr/bin/env bash
set -o errexit
if test $(ps h -o comm -p $$) = "sh"; then
    echo "Please use bash to execute this script."
    exit 1
fi

if [ ! -f "initialization.sh" ]; then
    echo "Cloning silverblog..."
    git clone https://github.com/SilverBlogTeam/SilverBlog.git --depth=1 silverblog
    cd silverblog/install
fi

echo "{\"install\":\"docker\"}" > install.lock

./install_python_dependency.sh

./check_python_version.py

./initialization.sh

cd ..
sed -i '''s/127.0.0.1/0.0.0.0/g' uwsgi.json

echo "Before you start SilverBlog for the first time, run the following command to initialize the configuration:"
echo "python3 manage.py setting"