#!/bin/bash
FOLDER=~/.ssh
FOLDER02=data/
FOLDER03=mnt/tmpfs
if [ -f "poetry.lock" ]; then
    rm poetry.lock
fi
if [ -f "pyproject.toml" ]; then
    rm pyproject.toml
fi
if [ -d "$FOLDER" ]; then
    cp -rvp ~/.ssh ssh/
else
    echo "Directory ./ssh does not exist!"
fi
if [ -d "$FOLDER02" ]; then
    echo "Directory data/ exist!"
else
    echo "Directory data/ does not exist!"
    mkdir data/
fi
if [ -d "$FOLDER03" ]; then
    echo "Directory mnt/tmpfs exist!"
else
    echo "Directory mnt/tmpfs does not exist!"
    mkdir mnt/tmpfs
    echo "nonono" > mnt/tmpfs/ows_runtime.map
fi
cp -rvp ../poetry.lock .

cp -rvp ../pyproject.toml .

docker-compose build 

docker-compose up -d 