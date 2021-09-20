#!/bin/bash

echo ${TOKEN} > token.txt

gh auth login --with-token < token.txt