# patchelf-wrapper

[![PyPi version][pypi-image]][pypi-link]
[![Build status][ci-image]][ci-link]

**Note**: patchelf-wrapper was originally developed because many Linux
distributions at the time lacked patchelf in their distro package managers.
That's changed in the intervening years, so this project isn't particularly
relevant anymore. Instead, I recommend that you install patchelf through your
distro's package manager (or failing that, building from source).

---

**patchelf-wrapper** is a simple Python module that assists in the installation
of the [*patchelf*](https://nixos.org/patchelf.html) utility. It's intended for
use with PyPI-hosted Python projects that depend on patchelf. If you're an
end-user of patchelf, you should look elsewhere! (Perhaps your distro's package
manager?)

Currently, patchelf-wrapper installs **patchelf 0.11**.

## Usage

Ordinarily, you'll just want to set `'patchelf-wrapper'` as one of your
requirements (e.g. in `setup.py`). If installing directly, you can just use
`python setup.py install` or `python setup.py build` as usual; this respects all
the usual options, including automatically installing patchelf into the `bin`
dir of a virtualenv if one is active.

In addition, patchelf-wrapper contains the following setup commands beyond the
defaults:

* `check_patchelf`: Checks if patchelf is already installed on the system
* `build_patchelf`: Extract patchelf's source and build it
* `install_patchelf`: Install patchelf to the chosen location

## License

This project is licensed under the [BSD 3-clause license](LICENSE). Patchelf
itself is licensed under the GPL, version 3.

[pypi-image]: https://img.shields.io/pypi/v/patchelf-wrapper.svg
[pypi-link]: https://pypi.python.org/pypi/patchelf-wrapper
[ci-image]: https://github.com/jimporter/patchelf-wrapper/workflows/build/badge.svg
[ci-link]: https://github.com/jimporter/patchelf-wrapper/actions?query=workflow%3Abuild
