# Alerta OpenDXL connector

`alerta_opendxl` is an [alerta](https://alerta.io/) plugin that enables broadcast of incoming alerts to the configured
OpenDXL topic.

## Installation

Obtain the `alerta-opendxl` package by installing the repository sub directory with pip. Another trivial way would be
to clone the Roboblue repository and work with the `alerta_opendxl` directory inside. 

If installing from a clone of the Roboblue repository, navigate to the directory and run `pip install .`. 
In order to activate the plugin, ppdate the Alerta configuration to load the `opendxl` plugin.

The plugin itself can be configured with either configuration options or environment variables.
Note that at the current stage, the plugin accepts the location of the OpenDXL client configuration file and expects
certificates to be stored in the same directory as the configuration (essentially the result of a `dxlclient` 
configuration provisioning). For further information on configuring the plugin, see below.

### Configuration

The following configuration properties are available:

* `DXL_CLIENT_CONFIG_FILE` - Location of the DXL Client configuration file
* `DXL_PUB_TOPIC` - Topic to which the incoming alerts will be posted
