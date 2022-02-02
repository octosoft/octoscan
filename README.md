# octoscan

## Unified Linux and macOS Scanner for [OctoSAM Inventory](https://www.octosoft.ch)


| :exclamation:  macOS 12.3 beta is currently not supported, due to the fact that Apple no longer distributes python with the OS see new [shell based scanner](https://github.com/octosoft/octoscan-mac)  |
|-----------------------------------------|


## Basic Operation

The scan module for Linux and macOS is a Python script delivered as a Python archive (.pyz)
On macOS the produced file has a .scam extension, on Linux .scal and on Windows .zip

### Invocation and Collection of Generated Files

Typically the scanner is invoked using existing management infrastructure.

On workstations and client systems, it's highly recommended to start the scanner in the user's 
context (logon scripts, macOS Launch Agents etc.) as that gives you valuable device affinity information. 

On servers, the scanner should be started in the root context, otherwise scanned information
may be incomplete.

```bash
FILE=$(./octoscan.pyz -o /tmp)
```

The program emits the generated filename to stdout, use the variable `${FILE}` to further process the file. 
You are completely free on how to transfer the generated files to the OctoSAM Import Service import folder.

A list of all options can be obtained using the help option

```bash
./octoscan.pyz --help
```

#### Using [octo-collect](https://github.com/octosoft/octopus-resty) the Octosoft Web-based Upload Server

Octosoft provides a high-performance upload server based on [openresty](https://openresty.org).
Use the curl utility on Linux and Mac to upload the generated file.

Very simple example:

```bash
FILE=$(./octoscan.pyz -o /tmp)
if curl -F "upload=@${FILE}" http://youruploadserver.yourdomain:8080
then
    rm ${FILE}
fi
```

### Linux Java Process Scan
On Linux, octoscan performs an in-depth scan of running java processes. If run under root 
the scan will read all java processes. Otherwise it reads processes running under the same user as the scan only.
If not running under root, the scan user must have permissions to start all detected java binaries.
For best java scan results on servers it's highly recommended to run the scan with root privileges.

### Linux Java Filesystem Scan
On Linux, octoscan scans common installation filesystem paths for java versions. 
If you have own conventions for installing software, specify the -J / --java option.
Paths that do not exist or are not accessible are silently ignored.
For best java scan results on servers it's highly recommended to run the scan with root privileges.

```bash
octoscan -java "/app/java:/u00/myapp/lib"
```

### Python Version

octoscan.pyz assumes that it is called using the current system implementation of python. 
Currently this is python 2.7 on most systems. 
If called directly it uses the python available using `/usr/bin/env python`.

You can also call python explicitly:

```bash
python2 octoscan.pyz -o /tmp
```

Some minimum debian and ubuntu installs do not include Python by default. 
In that case you need to first install python-minimal.

```bash
sudo apt-get update
sudo apt-get install python-minimal
```

### Running on Windows

octoscan.pyz also runs under Windows for testing only. The produced .zip files cannot be imported into 
OctoSAM Inventory.

### Open File Format

The produced file is a zip archive that contains all information as clear text

### Scanner Source License

The source code of the macOS/Linux scanner is licensed under the MIT open source license. 

### Network Prerequisites

For best results, all machines in your network should have synchronized clocks.
Otherwise date and time information in the inventory can be unreliable.


