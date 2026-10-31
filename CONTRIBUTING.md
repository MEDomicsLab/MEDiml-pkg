# Contributing to MEDiml

Thank you for your interest in MEDiml! Contributions of all kinds are welcome: bug reports, feature requests,
documentation improvements and code. By participating in this project, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting issues

Bugs and feature requests are tracked on the [GitHub issue tracker](https://github.com/MEDomicsLab/MEDiml-pkg/issues).
Before opening an issue, please check that it has not already been reported. When reporting a bug, please include:

- The MEDiml version (`pip show MEDiml`), your Python version and your operating system.
- The steps to reproduce the problem, ideally with a minimal code example and the extraction settings file used.
- The full error message and traceback.

Please do not share patient data in issues. If the problem depends on the data, describe it (modality, format,
dimensions) or reproduce it on a public dataset such as the [IBSI](https://theibsi.github.io/) phantoms.

## Seeking support

- Read the [documentation](https://mediml.readthedocs.io/), in particular the
  [FAQs](https://mediml.readthedocs.io/en/latest/FAQs.html) and the
  [tutorials](https://mediml.readthedocs.io/en/latest/tutorials.html).
- If your question is not answered there, open an [issue](https://github.com/MEDomicsLab/MEDiml-pkg/issues) describing
  what you are trying to do, or contact the team at medomics.info@gmail.com.

## Contributing code

1. Fork the repository and create a branch from `dev` (the development branch, `main` holds the released versions).
2. Install the package in editable mode with its dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -e . --no-deps
   ```

3. Make your changes, following the style of the surrounding code (Google-style docstrings, type hints).
4. Add or update the tests in the `tests/` folder and make sure they pass:

   ```bash
   pytest
   ```

5. Update the documentation in the `docs/` folder if your change affects the users.
6. Open a pull request against the `dev` branch, describing the change and referencing the related issue.
   The continuous integration must pass, and the pull request will be reviewed by a maintainer before being merged.

Changes to image processing, filtering or feature computation must keep MEDiml compliant with the IBSI standards.
Please run the IBSI notebooks in `notebooks/ibsi/` to check that the benchmark values are still reproduced.
