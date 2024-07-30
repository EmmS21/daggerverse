"""A generated module for Vcstockbrain functions

This module has been generated via dagger init and serves as a reference to
basic module structure as you get started with Dagger.

Two functions have been pre-created. You can modify, delete, or add to them,
as needed. They demonstrate usage of arguments and return types using simple
echo and grep commands. The functions can be called from the dagger CLI or
from one of the SDKs.

The first line in this comment block is a short description line and the
rest is a long description with more detail on the module's purpose or usage,
if appropriate. All modules should have a short description.
"""

import dagger
from dagger import dag, function, object_type


@object_type
class Vcstockbrain:
    @function
    async def run(self) -> str:
        """Returns a container that echoes whatever string argument is provided"""
        sectors_of_interest = "Health Care, Information Technology, Financials, and Energy"
        period = 2
        top = 5
        stocks_data = await dag.get_stocks().stocks(sectors_of_interest, period, top)
        return stocks_data

    @function
    async def update(self, directory_arg: dagger.Directory, pattern: str) -> str:
        """Returns lines that match a pattern in the files of the provided Directory"""
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_mounted_directory("/mnt", directory_arg)
            .with_workdir("/mnt")
            .with_exec(["grep", "-R", pattern, "."])
            .stdout()
        )
