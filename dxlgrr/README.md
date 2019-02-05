# DXL GRR

DXL GRR is a OpenDXL service providing a wrapper around the [GRR](https://github.com/google/grr) API. The service targets `Python 2.7.*` series. The usual under development disclaimer applies.
Note that this service depends on [Robobluekit](https://github.com/ccdcoe/roboblue/tree/master/robobluekit).

## Understanding the service

The service is a lightweight wrapper around the raw HTTP API. Documentation will not be reproduced at this point. Integrators are advised to refer to the following sources for more information on how to use the API:  

* The Protobuf definitions published [on Github](https://github.com/google/grr/tree/master/grr/proto/grr_response_proto)
* The service specific endpoint listing available with the [`ListApiMethods` endpoint](https://github.com/google/grr/blob/38fb9f91937896e063ae7cd301dc46bdabced7d0/grr/server/grr_response_server/gui/api_call_router.py#L1283).

Those endpoints that do not accept input, will not check the payload and will accept an empty payload. Other endpoints
require JSON encoded payload. Similarly, those endpoints that do not provide a response will return an empty payload.

## Installation & operation

### Installation

Note that the service depends on Robobluekit. The utility script installs it beforehand, when performing manual installation 
the operator is expected to install it themselves.
The DXL GRR service is distributed as a Python package. The recommended installation method at this time is to install the package using [pip](https://pip.pypa.io/en/stable/). The software is currently only distributed in this way and not available from any package repository.

To install the package globally, invoke the following in the project root directory: `pip install .` This will install the `dxlgrr` package globally. The service can then be invoked by calling `python -m dxlgrr ...`. For further information about command line configuration and usage call `python -m dxlgrr -h`.

Note that two utility scripts `./infra/scripts/install.sh` and `./infra/scripts/uninstall.sh` are included along with the distribution that can be used to install and uninstall the service. Note that these scripts work system wide and as such will require superuser privileges.

#### Installation with utility script

* Ensure that [Robobluekit](https://github.com/ccdcoe/roboblue/tree/master/robobluekit) is available as a directory in the parent directory or git is available on the installing machine
* Run `./infra/scripts/install.sh` from the distribution root as a superuser
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `/etc/dxlgrr/config/dxlclient.config` would be available
* Modify configuration in `/etc/dxlgrr/config/dxlgrr.config` to match your environment
* The `dxlgrr` service will be available to manage with `systemctl`

#### Uninstallation with utility script

* Stop the service
* Disable the service (optional)
* Run `./infra/scripts/uninstall.sh` from the distribution root as a superuser

#### Upgrading an existing installation

No ready-made upgrade scripts are provided at this time. Manual upgrades using `pip` are advised. The general idea is to
first install the newer version of the `robobluekit` package and then update the `dxlgrr`.

If any new configuration was added, the configuration files are required to be edited manually.

### Operation

After installation the DXL GRR service requires configuration for the DXL client & itself. The DXL client configuration can be obtained in the [traditional way](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) not covered here.  

An example DXL GRR configuration file is included in the `./config` directory as `./config/dxlgrr.config`. The configuration syntax is same as the one used by the DXLClient.

The following example illustrates operation using the default settings:

* Create a new directory to act as the working directory for the DXL GRR service
* Create a sub directory in the working directory called `config`
* Perform [DXLClient provisioning](https://opendxl.github.io/opendxl-client-python/pydoc/provisioningoverview.html) so that `./config/dxlclient.config` will be available in the working directory
* Create the service config file `dxlgrr.config` based on the example found in the project directory (`<root>/config/dxlgrr.config`)
* Edit the configuration file to reflect your environment
* Start the service with `python -m dxlgrr` in the working directory.

During startup the service will notify of failures to start. For use with Debian based systems an installation script has been included in `infra/scripts/install.sh`. The service is managed using systemd and the unit file is installed to `/etc/systemd/system` as `/etc/systemd/system/dxlgrr.service`.
The service is capable of running as a non privileged user given that the configuration directory has proper privileges.


#### Logging

The DXL GRR service logs using the standard Python logging library. Behaviour of the logger can be configured using
the logging configuration file as described [here](https://docs.python.org/2/library/logging.config.html#configuration-file-format).
By default, the service looks for the configuration file as `./config/logging.config` in its working directory. Note
that this file can be omitted.

An example of a debug logging configuration has been included in the repository as `./config/logging.config`.

### Configuration

By default the DXL GRR service looks for its necessary configuration files in the chosen working directory. Configuration files and certificates are expected to be in the `config` sub directory. Do note that this behaviour can be configured using command line arguments. See the below table for further information about configuration options.

Configuration block     | Keyword               | Comment
------------------------|-----------------------|---------
`Service`			    | 					    | Configuration block that contains service level configuration
						| `Type` 	            | Service type name
`GRR`		            |					    | Configuration settings for GRR Rapid Response connectivity
		      	 	    | `Endpoint`			| GRR API endpoint
						| `Username`			| Username to be used for authentication with GRR
						| `Password`			| Password to be used for authentication with GRR

## Development setup

Dependency and Virtualenv management is provided using [Pipenv](https://pipenv.readthedocs.io/en/latest/).
A Pipfile and its accompanying lockfile are included in the repository. Note that the source of truth for dependencies is the `REQUIRED` packages list in `setup.py`
