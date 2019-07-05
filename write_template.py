import base64
import json
import subprocess

from jinja2 import Environment
from os import path, rename
from ruamel import yaml
from shutil import copyfile
from sys import exit

try:
    import boto3
    from ansible.plugins.filter import core, ipaddr, json_query, k8s, \
        mathstuff, \
        network, urlsplit, urls
except ImportError as e:
    pass


def aws_kms_decrypt_filter(value):
    session = boto3.session.Session()
    kms = session.client('kms')
    decr = kms.decrypt(CiphertextBlob=base64.b64decode(value))
    return decr['Plaintext'].decode('utf-8')


def get_ansible_facts():
    if 'ansible' not in globals():
        return {}

    try:
        sp = subprocess.run(['ansible', '-o', '-m', 'setup',
                             '--connection=local', '-i', 'localhost,', 'all'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            encoding='utf-8')
        stdout_json = sp.stdout[sp.stdout.find('{'):sp.stdout.rfind('}')+1]
        return json.loads(stdout_json)["ansible_facts"]

    except subprocess.CalledProcessError as e:
        print("Failed to invoke ansible setup module\n{]".format(e.stderr))
        return {}


def get_cloud_facts():
    try:
        sp = subprocess.run(['cloud-init', 'query', '--all'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(sp.stdout)

    except subprocess.CalledProcessError as e:
        print("Failed to invoke cloud-init query\n{]".format(e.stderr))
        exit(1)


def prep_jenv(jenv):
    for filterplugin in 'core', 'ipaddr', 'json_query', 'k8s', 'mathstuff',\
            'network', 'urlsplit', 'urls':
        filterobject = globals()[filterplugin].FilterModule()
        filters = filterobject.filters()
        for filtername in filters:
            jenv.filters[filtername] = filters[filtername]

    if 'boto3' in globals():
        jenv.filters['aws_kms_decrypt'] = aws_kms_decrypt_filter


def write_template(filename, template_data, context, jenv):
    dest = ''

    if 'dest' in template_data:
        dest = template_data['dest']
    else:
        if filename[-3:] == '.j2':
            dest = filename[:-3]
        else:
            print("write_template: /!\\ Warnng, overwriting template file with"
                  "rendered template {}".format(filename))

    with open(filename, "r") as f:
        raw_template = f.read()
        f.close()

    if path.exists(dest) \
            and 'backup' in template_data \
            and template_data['backup']:

        copyfile(dest, '{].bak'.format(dest))

    template = jenv.from_string(raw_template)
    rendered = template.render(context)

    with open(dest, "w") as f:
        f.write(rendered)
        f.close()


def cli():
    cloud_facts = get_cloud_facts()
    userdata = yaml.round_trip_load(cloud_facts['userdata'])

    if 'write_template' in userdata:
        wt = userdata['write_template']
    else:
        print("write_template: no templates to process")
        exit(0)
        return True

    ansible_facts = get_ansible_facts()
    global_context = {}
    global_context.update(cloud_facts)
    global_context.update(ansible_facts)

    if 'vars' in wt:
        global_context.update(userdata['write_template']['vars'])

    if 'templates' not in wt:
        print("write_template: no templates to process")
        exit(0)
        return True

    jenv = Environment(keep_trailing_newline=True)
    prep_jenv(jenv)

    for filename in wt['templates']:
        if not path.isfile(filename):
            if wt['templates'][filename].lc is None:
                lineno = 'Unknown'
            else:
                lineno = wt['templates'][filename].lc.line

            print("write_template: Missing Template {}, line: {}".
                  format(filename, lineno))
            if 'ignore_missing' in wt and wt['ignore_missing']:
                continue
            else:
                exit(1)
                return False

        local_context = global_context
        if 'vars' in wt['templates'][filename]:
            local_context.update(wt['templates'][filename]['vars'])

        if 'backup' in wt['templates'] \
                and 'backup' not in wt['templates'][filename]:

            wt['templates'][filename]['backup'] = wt['templates']['backup']

        write_template(filename, wt['templates'][filename], local_context, jenv)

    return True
