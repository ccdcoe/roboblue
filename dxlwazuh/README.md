# DXL Wazuh

DXL Wazuh is a OpenDXL service providing a wrapper around the [Wazuh](https://wazuh.com/) API. The service targets `Python 2.7.*` series. The usual under development disclaimer applies.

## Understanding the service

The service is a lightweight wrapper around the raw HTTP API. Documentation will not be reproduced at this point. Integrators are advised to refer to the following sources for more information on how to use the API:  

* The official API documentation available [here](https://documentation.wazuh.com/current/user-manual/api/index.html)
* The generated APIDoc output used as part of this service: `./dxlwazuh/api_data.json`

All endpoints except well formed JSON strings as input. When invoking an endpoint through OpenDXL, the URL variables
must be included within the payload as well.

### Updating the service

New functionality of the Wazuh API can be made available by replacing the `./dxlwazuh/api_data.json` file with a 
newly generated one.

The updating process is as follows:
* Clone the Wazuh API repository: https://github.com/wazuh/wazuh-api
* Navigate to the `doc` directory of the repository
* Run [APIDoc CLI](http://apidocjs.com/#install) similarly to the example: `apidoc -i ../ -e node_modules`

## Installation & operation

### Installation

The DXL Wazuh service is distributed as a Python package. The recommended installation method at this time is to install the package using [pip](https://pip.pypa.io/en/stable/). The software is currently only distributed in this way and not available from any package repository.

To install the package globally, invoke the following in the project root directory: `pip install .` 
This will install the `dxlwazuh` package globally. The service can then be invoked by calling `python -m dxlwazuh ...`. For further information about command line configuration and usage call `python -m dxlwazuh -h`.

Note that two utility scripts `./infra/scripts/install.sh` and `./infra/scripts/uninstall.sh` are included along with the distribution that can be used to install and uninstall the service. Note that these scripts work system wide and as such will require superuser privileges.

#### Installation with utility script

* Run `./infra/scripts/install.sh` from the distribution root as a superuser
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `/etc/dxlwazuh/config/dxlclient.config` would be available
* Modify configuration in `/etc/dxlwazuh/config/dxlwazuh.config` to match your environment
* The `dxlwazuh` service will be available to manage with `systemctl`

#### Uninstallation with utility script

* Stop the service
* Disable the service (optional)
* Run `./infra/scripts/uninstall.sh` from the distribution root as a superuser

#### Upgrading an existing installation

No ready-made upgrade scripts are provided at this time. Manual upgrades using `pip` are advised. The general idea is to
first install the newer version of the `robobluekit` package and then update the `dxlwazuh`.

If any new configuration was added, the configuration files are required to be edited manually.

### Operation

After installation the DXL Wazuh service requires configuration for the DXL client & itself. The DXL client configuration can be obtained in the [traditional way](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) not covered here.  

An example DXL Wazuh configuration file is included in the `./config` directory as `./config/dxlwazuh.config`. The configuration syntax is same as the one used by the DXLClient.

The following example illustrates operation using the default settings:

* Create a new directory to act as the working directory for the DXL Wazuh service
* Create a sub directory in the working directory called `config`
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `./config/dxlclient.config` will be available in the working directory
* Create the service config file `dxlgrr.config` based on the example found in the project directory (`<root>/config/dxlgrr.config`)
* Edit the configuration file to reflect your environment
* Start the service with `python -m dxlgrr` in the working directory.

During startup the service will notify of failures to start. For use with Debian based systems an installation script has been included in `infra/scripts/install.sh`. The service is managed using systemd and the unit file is installed to `/etc/systemd/system` as `/etc/systemd/system/dxlgrr.service`.
The service is capable of running as a non privileged user given that the configuration directory has proper privileges.


#### Logging

The DXL Wazuh service logs using the standard Python logging library. Behaviour of the logger can be configured using
the logging configuration file as described [here](https://docs.python.org/2/library/logging.config.html#configuration-file-format).
By default, the service looks for the configuration file as `./config/logging.config` in its working directory. Note
that this file can be omitted.

An example of a debug logging configuration has been included in the repository as `./config/logging.config`.

### Configuration

By default the DXL Wazuh service looks for its necessary configuration files in the chosen working directory. Configuration files and certificates are expected to be in the `config` sub directory. Do note that this behaviour can be configured using command line arguments. See the below table for further information about configuration options.

Configuration block     | Keyword               | Comment
------------------------|-----------------------|---------
`Service`			    | 					    | Configuration block that contains service level configuration
						| `Type` 	            | Service type name
`Wazuh`		            |					    | Configuration settings for Wazuh API connectivity
		      	 	    | `Endpoint`			| Wazuh API endpoint
						| `Username`			| Username to be used for authentication with Wazuh
						| `Password`			| Password to be used for authentication with Wazuh
						| `VerifySSL`           | 'True' or 'False' whether SSL certificates should be veri

## Development setup

Dependency and Virtualenv management is provided using [Pipenv](https://pipenv.readthedocs.io/en/latest/).
A Pipfile and its accompanying lockfile are included in the repository. Note that the source of truth for dependencies is the `REQUIRED` packages list in `setup.py`
