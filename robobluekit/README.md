# Roboblue kit

The Roboblue service development kit is a small collection of helpful components used to develop OpenDXL services as
part of the Roboblue project

What's included?

* `Application` - a convenience wrapper to wrap applications in order to assist with monitoring and OS signal handling + lifecycle
* `Monitor` - a simplistic universal monitoring interface with a configurable HTTP status endpoint
    * Additional facilities for configuring the monitoring. NB: The configuration is not dynamically reloadable
* `Kit` - Utility functions that can be used throughout (unified formatting, validation)

## Usage

For development purposes the package must be installed as editable using `pipenv` in the appropriate service's virtual
environment.

In order to understand what the kit can do for you, it would be best to just have a look at one of the available
services.

## Installation

Due to the in-development nature of this project, users are expected to install the package on any systems before
installing any Roboblue services. Additionally, the monorepo nature of the project expects that all services must 
continue working on updates to the kit.

## Development

Create a new virtualenv using the included Pipfile or use the kit as part of another service's virtualenv
