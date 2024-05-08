"""
A generated module for RunTests functions

This module provides functionality to run unit tests for NodeJS projects.

This module requires the absolute path to your working directory to be provided as the 'src' argument. This is necessary to mount the project directory into the Docker container where the tests will be executed.

The 'repo' argument specifies the Docker image associated with the project, and the 'tag' argument specifies the tag associated with the Docker image.

Example test call:
dagger call build-test --src=../../ --repo=test123/testImage --tag=latest

"""


import dagger
from dagger import dag, function, object_type 

@object_type
class RunTests:
    """
        Returns a description of the module.
    """
    @function
    def test(self) -> str:
        return "This is a module to run unit tests on a NodeJS application"

    """Builds and executes unit tests for the NodeJS project.

        Args:
            src (dagger.Directory): The absolute path to the project's working directory.
            repo (str): The Docker image associated with the project.
            tag (str): The tag associated with the Docker image.

        Returns:
            str: The result of running the unit tests.
    """
    @function
    async def build_test(self, src: dagger.Directory, repo: str, tag: str) -> str:
        image_address = f"docker.io/{repo}:{tag}"
        return await (
            dag.container()
            .from_(image_address)
            .with_mounted_directory("/app", src)
            .with_exec(["sh", "-c", "npm install @rollup/rollup-linux-arm64-gnu || true"])
            .with_exec(["sh", "-c", "npm run test 2>&1"])
            .stdout()
        )
            