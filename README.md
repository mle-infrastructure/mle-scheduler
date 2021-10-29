# Lightweight Cluster/Cloud VM Job Scheduling 🚂
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-launcher.svg?style=flat-square)](https://pypi.python.org/pypi/mle-launcher)
[![PyPI version](https://badge.fury.io/py/mle-monitor.svg)](https://badge.fury.io/py/mle-launcher)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/mle-launcher/blob/main/examples/getting_started.ipynb)
<a href="https://github.com/RobertTLange/mle-launcher/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/RobertTLange/mle-launcher/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

`mle-launcher` provides two core functionalities:

- **`MLEJob`**: Manage a single job.
- **`MLEQueue`**: Manage a queue of jobs.


## Development & Milestones for Next Release

You can run the test suite via `python -m pytest -vv tests/`. If you find a bug or are missing your favourite feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:. Here are some features I want to implement for the next release:

- [ ] Get rid of all `mle_config` pre-settings. Make them input to Job/Queue
- [ ] Get rid of all requirements?!
