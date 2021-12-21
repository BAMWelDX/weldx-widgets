"""Setup for weldx-widgets."""
import setuptools
from setuptools.command.egg_info import egg_info


class InstallWithCompile(egg_info):
    """Build messages catalog (.mo files) during egg_info."""

    def run(self):
        """Run it."""
        from babel.messages.frontend import compile_catalog

        compiler = compile_catalog(self.distribution)
        option_dict = self.distribution.get_option_dict("compile_catalog")
        compiler.domain = [option_dict["domain"][1]]
        compiler.directory = option_dict["directory"][1]
        compiler.use_fuzzy = True  # fixme: this should not be mandatory!
        compiler.run()

        super().run()


if __name__ == "__main__":
    setuptools.setup(
        cmdclass=dict(egg_info=InstallWithCompile),
        package_data={"": ["locale/*/*/*.mo", "locale/*/*/*.po"]},
    )
