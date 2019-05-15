# octoscan

## Unified Linux and macos Scanner for OctoSAM Inventory

## Basic Operation

The scan module for Linux and macOS is a Python script delivered as a Python archive (.pyz)
On macOS the produced file has a .scam extension, on Linux .scal and on Windows .zip

### Invocation and Collection of Generated Files

Typically the scanner is invoked using existing management infrastructure.

On workstations and client systems, it's highly recommended to start the scanner in the user's 
context (logon scripts etc.) as that gives you valuable device affinity information.

```bash
FILE=$(./octoscan.pyz -o /tmp)
```

The program emits the generated filename to stdout, use the variable `${FILE}` to further process the file. 
You are completely free on how to transfer the generated files to the OctoSAM Import Service import folder.

#### Using octo-collect the Octosoft Web-based Upload Server

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

Depending on your setup, you will want to save the file if it cannot be uploaded and re-try to upload saved files.

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
