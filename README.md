# write_template - read from cloud-config, write to template
This is a very simple script to template out configuration files with
cloud-init. The configuration format is json, it is generally expected that
the files already exist on the system when it is executed, either being placed
in the pristine image or replaced there.

If ansible is installed the ansible facts for the host are included as template
variables and all the filters available in ansible jinja2 templates are also
made available.

In addition there is a filter to decrypt data from KMS.

## Requirements
* `cloud-init` needs to be installed
* Python (tested with Python 3.7, should work with earlier versions)
* (**optional**) ansible installed for using ansible facts and filters
* (**optional**) boto3 installed for KMS decrypter filter

## Configuration Format
The configuration format is YAML, same as cloud-config. An annotated example:

```yaml
#coud-config

# block for templates to write out
write_template:
  # Templates to write
  templates:
    # this template is written to /etc/example.conf, can also be set in global context
    '/etc/example.conf.j2':
      backup: true  # backup original if it exists
      # These variables are only available to this template
      vars:
        localvalue: test
        # this is what a string in KMS would look like
        secretvalue: 'AQICAHgA+nz0K7DdvRAxwGcrzljTmTCnhJW3f1keusnjcXJgEgFf072A/rzmxLbsXD/uiMjDAAAAaDBmBgkqhkiG9w0BBwagWTBXAgEAMFIGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMz40CgwfRnfscgublAgEQgCXjiJhleY/+IkVsQ2rrly41AD6IFZf6x2gBdHIXNpKHORWB8jXG'
    # This
    '/etc/garbage.j2': {}

  # these variables are available to all templates      
  vars:
    globalvalue: test
 
  # do not fail when a template does not exist
  ignore_missing: true
```

## Using the KMS filter to decrypt value
The filter is pretty straightforward to use, here is an example template:
```jinja2
[config]
user=pychael
password={{ secretvalue|aws_kms_decrypt }}
```

This requires the CiphertextBlob from `aws kms encrypt`, encoded as Base64 as
input. The instance obviously needs to have (decrypt) access to this particular
key.
