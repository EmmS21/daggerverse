# JestTestRunner
A Dagger module to run unit tests implemented using Jest in a containerized environment on a NodeJS project

# What is Dagger
Dagger is a programmable tool that lets you replace your software project's artisanal scripts with a modern API and cross-language scripting engine.
Docs: https://docs.dagger.io/

# What is the purpose of this module
Enabling me to create a container with configurations similar to development and production environments and run tests. Ensuring tests are passing consistently in all environments

# How it works
use dagger call to call the functions built into this module

`dagger call test` will return, "This is a module to run Jest unit tests on a NodeJS application". Carry this out as a sanity check to ensure the module is working

`dagger call build-test` needs to be called with two arguments:
repo - this should be a string with a link to your Docker Image
tag - this should be the tag related to your Docker Image

test call:
`dagger call build-test --src=../../ --repo=emms21/interviewsageai --tag=latest`

