# octoscan

## Linux Scanner for [OctoSAM Inventory](https://www.octosoft.ch)

Release 1.10.6 - September 2023

**_NOTE:_** python 2.6 is no longer supported, minimum version is now python 2.7 or python 3.6

**_NOTE:_** macOS support has been removed from this version of the python based scanner.
   Apple does no longer distribute python with the base operating system.

**_NOTE:_** Scan of Linux VMs under Hyper-V requires OctoSAM Server version 1.10.6 or newer to import
produced .scal files. However, import of .scal files produced by older Linux scanners is
still supported in OctoSAM Server 1.10.6.

## Basic Operation

The scan module for Linux is a Python script delivered as a Python archive (.pyz)
The produced filename ends with .scal on Linux and .zip on Windows


### Invocation and Collection of Generated Files

Usually the scanner is invoked using existing management infrastructure.

On workstations and client systems, it's highly recommended to start the scanner in the user's 
context (logon scripts,) as that gives you valuable device affinity information. 

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

### Using an Upload Server

Octosoft provides a Windows / IIS based upload server for the generated .scan files. A high-performance Linux based upload server is also provided based at [octo-collect](https://github.com/octosoft/octopus-resty), this open source server is based on [openresty](https://openresty.org).

Use the curl utility on Linux and Mac to upload the generated file.

Very simple example:

```bash
FILE=$(./octoscan.pyz -o /tmp)
if curl -F "upload=@${FILE}" http://youruploadserver.yourdomain:8080/upload
then
    rm ${FILE}
fi
```

In practice, you need to add error handling and ideally handle the case that the upload server may not
be available by caching generated .scal files. 

### Linux Java Process Scan
Octoscan performs an in-depth scan of running java processes. If run under root 
the scan will read all java processes. Otherwise, it reads processes running under the same user as the scan only.
If not running under root, the scan user must have permissions to start all detected java binaries 
as detailed version information can typically only be read through the java binary --version option.
For best java scan results on servers it's highly recommended to run the scan with root privileges.

### Linux Java Filesystem Scan
Octoscan scans common installation filesystem paths for java versions. 
If you have own conventions for installing software, specify the -J / --java option.
Paths that do not exist or are not accessible are silently ignored.
For best java scan results on servers it's highly recommended to run the scan with root privileges.

```bash
octoscan.pyz -java "/app/java:/u00/myapp/lib"
```

### Python Version

octoscan.pyz assumes that it is called using the current system implementation of python. 
Currently this is python 2.7 or 3.7 on most systems. 
If called directly it uses the python available using `/usr/bin/env python`.

You can also call python explicitly:

```bash
python3 octoscan.pyz -o /tmp
```

Some minimum debian and ubuntu installs do not include Python by default. 
In that case you need to first install python-minimal.

```bash
sudo apt-get update
sudo apt-get install python-minimal
```
**_NOTE:_** Python 2.6 is no longer supported

### Why is the Scanner dependent on Python

We decided that a single dependency on a python-minimal installation is easier to handle than the multiple dependencies 
that we would have with a typical shell based scanner. 
The situation is different on macOS, where we can assume certain command-line programs are installed on every machine. 

Due to the diversity of Linux implementations, the Linux scanner is quite more complex than the macOS scanner.
Python allows us to implement a complex scan without writing temporary files, this improves performance.
Python programs are generally easier to maintain and debug than shell scripts.

### Running on Windows

octoscan.pyz also runs under Windows for testing only. The produced .zip files cannot be imported into 
OctoSAM Inventory.

### Open File Format

The produced file is a zip archive that contains all information as clear text

### Scanner Source License

The source code of the Linux scanner is licensed under the MIT open source license. 

### Network Prerequisites

For best results, all machines in your network should have synchronized clocks.
Otherwise date and time information in the inventory can be unreliable.

