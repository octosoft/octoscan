# octoscan

## [OctoSAM Inventory](https://www.octosoft.ch) scanner for Linux

### What's new

#### Release 1.10.9 - June 2024

- new command-line options to override machine, cluster, virtualization, and host names in clustered container environments.
  These options require OctoSAM server version 1.10.9 or newer.

- for systemd-based systems, detect the virtualization technology using the `systemd-detect-virt` command.
  The improved virtualization recognition requires OctoSAM server version 1.10.9 or newer.

- gracefully handle an exception that os.getlogin() can throw on container platforms

#### Release 1.10.9 - May 2024

- scan of effective user id
- scan of ipcs configuration if present to detect some server products

Requires OctoSAM server version 1.10.7 or newer.

#### Release 1.10.7 - November 2023

Octoscan 1.10.7 no longer depends on the python distro module.
On most Linux variants - even on minimal installs - the scanner should now be able to run directly
without the need to install any additional Linux packages or Python modules.

**_NOTE_** Windows support has been removed from octoscan. 
    Windows support was previously only used for module testing.

Requires OctoSAM server version 1.10.6 or newer.

#### Release 1.10.6 - September 2023

**_NOTE:_** python 2.6 is no longer supported, minimum version is now python 2.7 or python 3.6

**_NOTE:_** macOS support has been removed from this version of the python based scanner.
   Apple does no longer distribute python with the base operating system.

**_NOTE:_** Scan of Linux VMs under Hyper-V requires OctoSAM Server version 1.10.6 or newer to import
produced .scal files. However, import of .scal files produced by older Linux scanners is
still supported in OctoSAM Server 1.10.6.

## Installation and basic operation

The scan module for Linux is a Python script delivered as a Python archive.

### Download octoscan from github

Download the latest version from the github master branch. 
Note that some distros provide curl while others provide wget by default. 
For uploading the produced scan files we recommend
that you install curl if it's not already installed.

**_NOTE:_** The indicated download link is for test and integration only. 
Of course, in production environments you should load the scanner from a controlled location inside your network.

#### Download using curl

```sh
curl -OL https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
chmod +x octoscan.pyz
```

#### Download using wget

```sh
wget https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
chmod +x octoscan.pyz
```

#### Download using git

This includes the source code of the scanner

```sh
mkdir projects
cd projects
git clone https://github.com/octosoft/octoscan
```

### Invocation and collection of generated files

Usually, the scanner is invoked using existing management infrastructure.

On workstations and client systems, it's highly recommended to start the scanner in the user's
context (logon scripts, etc.) as that gives you valuable device affinity information.

On servers, the scanner should be started in the root context. Otherwise, scanned information
may be incomplete.

```bash
FILE=$(./octoscan.pyz -o /tmp)
```

The program emits the generated filename to stdout. Use the variable `${FILE}` to further process the file.
You are completely free on how to transfer the generated files to the OctoSAM Import Service import folder.

A list of all options can be obtained using the help option

```bash
./octoscan.pyz --help
```

### Running octoscan in a container environment
Use your existing container orchestration tools to start the scanner in each container.
Depending on your base image you may have to install Python first.

In your orchestration or management environment, you may already have more information about the settings than the scanner can find out in a platform-independent way.

Octoscan supports several options to reflect this environment information to the OctoSAM inventory:

#### container Option
Specify --container if you run it in a container environment.

#### machine Option
You can specify another machine name than what is returned by `hostname` within the container. 
The specified value (FQDN format) overrides the machine name in OctoSAM. Make sure the value is unique.

#### host Option
You can specify an FQDN for your container host (pod).§
Specify the same FQDN that you get when you scan the host machine from outside the container cluster. 
DNS may be different inside and outside the container environment.

#### cluster Option
Specify the name of your cluster. Cluster names must be unique.

### Common error messages when starting the scanner

```
Unsupported Python2 Version:
Unsupported Python3 Version:
```
Your system does not meet the minimum requirement of either Python 2.7 or 3.6 or newer.

```
-bash: ./octoscan.pyz: Permission denied
```
You probably forgot to set execution permissions on the file octoscan.pyz

```
/usr/bin/env 'python': No such file or directory
```
Your system does not have a python interpreter registered under the name python.
Most likely you are on a more recent Linux system that has python3 as the default
python environment. You need to start the scanner using the python3 command:
```bash
python3 octoscan.pyz
```

### Using an upload server

Octosoft provides a Windows / IIS-based upload server for the generated .scan files. A high-performance Linux-based upload server is also available at [octo-collect](https://github.com/octosoft/octopus-resty), this Open Source server is based on [openresty](https://openresty.org).

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

### Linux Java process scan
Octoscan performs an in-depth scan of running Java processes. If run under root
the scan will read all java processes. Otherwise, it reads processes running under the same user as the scan only.
If not running under root, the scan user must have the permissions to start all detected Java binaries
as detailed version information can typically only be read through the Java binary --version option.
For best Java scan results on servers, it's highly recommended to run the scan with root privileges.

### Linux Java filesystem scan
Octoscan scans common installation filesystem paths for Java versions.
If you have your own conventions for installing software, specify the -J / --java option.
Paths that do not exist or are not accessible are silently ignored.
For best Java scan results on servers, it's highly recommended to run the scan with root privileges.

```bash
octoscan.pyz -java "/app/java:/u00/myapp/lib"
```

### Python Version

octoscan.pyz assumes that it is called using the current system implementation of Python.
Currently, this is Python 2.7 or 3.6 or newer on most systems. 
If called directly it uses the python available using `/usr/bin/env python`.

You can also call python explicitly:

```bash
python3 octoscan.pyz -o /tmp
```

### Why use Python?

We decided that a single dependency on a python-minimal installation is easier to handle than the multiple dependencies
that we would have with a typical shell-based scanner.
The situation is different on macOS, where we can assume certain command-line programs are installed on every machine.

Due to the diversity of Linux implementations, the Linux scanner is quite more complex than the macOS scanner.
Python allows us to implement a complex scan without writing temporary files, this improves performance considerably.
Python programs are generally easier to maintain and debug than shell scripts.

### Open file format

The produced file is a zip archive that contains all information as clear text.
You can unzip the archive to see what got scanned.

```bash
unzip f74ecf32-38b7-4e24-9a7e-f262d7d5e26b.scal
```

### Scanner source license

The source code of the Linux scanner is licensed under the MIT open source license. 

### Network prerequisites

For best results, all machines in your network should have synchronized clocks.
Otherwise, date and time information in the inventory can be unreliable.

### Notes for specific Linux variants

The supported Linux variants are tested with their standard installs. 
If you use a minimal install, some required modules may not be installed by default.

#### RHEL 8, Centos 8, Rocky Linux 8, minimal install

The python3 command may not be installed by default. The standard system Python is Python 3.6.

```shell
sudo yum update
sudo yum install python3
curl -OL https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
sudo python3 octoscan.pyz
```

#### RHEL 9, Centos 9, Rocky Linux 9, Alma Linux 9, minimal install

The `python` or `python3` commands are installed by default and point to Python 3.9. 

```shell
curl -OL https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
chmod +x octoscan.pyz
sudo python3 ./octoscan.pyz
```

#### Ubuntu minimal install 

Some minimum Ubuntu installs do not include Python by default. In that case, you need to first install python-minimal.

```bash
sudo apt-get update
sudo apt-get install python-minimal
curl -OL https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
sudo python octoscan.pyz
```

#### Debian 12 minimal network install (with standard utilities)

The `python` command is installed and points to Python 3.10.
Note that curl may not be installed by default. We recommend using curl to upload the generated .scan files to the
OctoSAM upload server.

```bash
wget https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
sudo python3 ./octoscan.pyz
# optionally install curl:
# sudo apt update
# sudo apt install curl
```

#### SLES 15 minimal install

The `python3` command points to Python 3.6. Execute the scanner with root permissions. Note that the `sudo` command may not be installed on SLES 15 minimal

```shell
curl -OL https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
python3 octoscan.pyz
```

#### Alpine 3

**_NOTE:_** Calling the scanner without root permission is not supported on Alpine.

Alpine uses [BusyBox](https://busybox.net), some commands may differ slightly from their GNU pendants.

```shell
apk update
apk add --update --no-cache python3 
wget https://github.com/octosoft/octoscan/raw/master/octoscan.pyz
python octoscan.pyz
```