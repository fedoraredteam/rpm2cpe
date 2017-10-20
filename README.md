# rpm2cpe
Translates the name of an RPM to the NVD [CPE](https://cpe.mitre.org/specification/) name.  The expectation is that this will support the ELEM tool.

**NOTE:** This isn't perfect, and pull requests are welcome.

## Command Line Interface
```terminal
usage: rpm2cpe.py [-h] (--rpm RPM [RPM ...] | --repo REPO [REPO ...]) [-s]
                  [-t | -j | -c]

Translate an RPM name to CPE.

optional arguments:
  -h, --help            show this help message and exit
  --rpm RPM [RPM ...]   The RPM name to translate. Can be a comma separated
                        list.
  --repo REPO [REPO ...]
                        If specified, rpm2cpe will translate all RPM's to
                        CPE's. Only executeable on an Enterprise Linux Host.
  -s, --strict          Return multiple CPE strings for a given package
                        version with varying version numbers
  -t, --txt
  -j, --json
  -c, --csv
```

## OpenShift S2I
rpm2cpe includes a REST interface that can be deployed into OpenShift via S2I.

