# DXLHistorian

DXL Historian is a passive [OpenDXL](https://www.opendxl.com/) event listener that records any received messages to an Elasticsearch instance. The project targets `Python 2.7.*` series. The software is not yet stable at this time and largely expects you to know what you're doing.

## Installation & operation

### Installation

The historian service is distributed as a Python package. The recommended installation method at this time is to install the package using [pip](https://pip.pypa.io/en/stable/). The software is currently only distributed in this way and not available from any package repository.

To install the package globally, invoke the following in the project root directory: `pip install .` This will install the `dxlhistorian` package globally. The service can then be invoked by calling `python -m dxlhistorian ...`. For further information about command line configuration and usage call `python -m dxlhistorian -h`.

Note that two utility scripts `./infra/scripts/install.sh` and `./infra/scripts/uninstall.sh` are included along with the distribution that can be used to install and uninstall the service. Note that these scripts work system wide and as such may require super user privileges.

#### Installation with utility script

* Run `./infra/scripts/install.sh` from the distribution root as a super user
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `/etc/dxlhistorian/config/dxlclient.config` would be available
* Modify configuration in `/etc/dxlhistorian/config/dxlhistorian.config` to match your environment
* The `dxlhistorian` service will be available to manage with `systemctl`

#### Uninstallation with utility script

* Stop the service
* Disable the service (optional)
* Run `./infra/scripts/uninstall.sh` from the distribution root as a super user

#### Upgrading an existing installation

No ready-made upgrade scripts are provided at this time. Manual upgrades using `pip` are advised. The general idea is to
first install the newer version of the `robobluekit` package and then update the `dxlhistorian`.

If any new configuration was added, the configuration files are required to be edited manually.

### Operation

After installation the Historian service requires configuration for the DXL client & itself. The DXL client configuration can be obtained in the [traditional way](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) not covered here.  

An example Historian configuration file is included in the `./config` directory as `./config/dxlhistorian.config`. The configuration syntax is same as the one used by the DXLClient.

The following example illustrates operation using the default settings:

* Create a new directory to act as the working directory for the Historian service
* Create a sub directory in the working directory called `config`
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `./config/dxlclient.config` will be available in the working directory
* Create the service config file `dxlhistorian.config` based on the example found in the project directory (`<root>/config/dxlhistorian.config`)
* Edit the configuration file to reflect your environment
* Start the service with `python -m dxlhistorian ` in the working directory.

During startup the service will notify of failures to start. For use with Debian based systems an installation script has been included in `infra/scripts/install.sh`. The service is managed using systemd and the unit file is installed to `/etc/systemd/system` as `/etc/systemd/system/dxlhistorian.service`.
The service is capable of running as a non privileged user given that the configuration directory has proper privileges.


#### Logging

The Historian service logs using the standard Python logging library. Behaviour of the logger can be configured using
the logging configuration file as described [here](https://docs.python.org/2/library/logging.config.html#configuration-file-format).
By default, the service looks for the configuration file as `./config/logging.config` in its working directory. Note
that this file can be omitted.

### Configuration

By default the Historian service looks for its necessary configuration files in the chosen working directory. Configuration files and certificates are expected to be in the `config` sub directory. Do note that this behaviour can be configured using command line arguments. See the below table for further information about configuration options.

Configuration block     | Keyword           | Comment
------------------------|-------------------|---------
`Application`			| 					| Configuration block that should contain program level configuration
						| `SubscribeTo` 	| Comma separated list of topics the Historian should subscribe to
						| `Recorder`		| One of: `STDOUT`, `Elasticsearch`. The recording driver, `STDOUT` is provided for reference purposes
`Elasticsearch`		    |					| Configuration settings for the Elasticsearch recording driver
		    			| `Host`			| Host of the Elasticsearch server
						| `Port`			| Port of the Elasticsearch server
						| `Index`			| Elasticsearch index to be used for the data

## Development setup

Dependency and Virtualenv management is provided using [Pipenv](https://pipenv.readthedocs.io/en/latest/).
A Pipfile and its accompanying lockfile are included in the repository. Note that the source of truth for dependencies is the `REQUIRED` packages list in `setup.py`
