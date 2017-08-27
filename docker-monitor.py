#!/usr/bin/env /usr/bin/python

import re
import json
import logging
import optparse
import subprocess

logging.basicConfig(filename="/var/log/docker-monitor.log", level=logging.INFO)

ZABBIX_HOST = "10.1.7.6"
SERVER_NAME = "cloudclass.h3c.com"
KEY_PREFIX = "docker.gaojian"

FUNCTIONS = ["list_container", "get_metric"]

DOCKER_LIST_COMMAND = "sudo docker ps -a|grep -v 'CONTAINER ID'|awk '{print $NF}'"
DOCKER_STATUS_COMMAND = "sudo docker ps -a|grep -v 'CONTAINER ID'|awk '{print $NF}' | xargs sudo docker stats --no-stream | grep -v 'CONTAINER'"
CONTAINER_STATUS_COMMAND = "sudo docker stats --no-stream {} | grep -v 'CONTAINER'"
DOCKER_STATS_REG = """(?P<name>\S+) \s+ (?P<cpu>\S+) \s+ (?P<memory_used>\S+) / (?P<memory_total>\S+) \s+ (?P<memory_percent>\S+) \s+ (?P<network_input>\S+) / (?P<network_output>\S+) \s+ (?P<block_input>\S+) / (?P<block_output>\S+)"""


def exec_command(command_line):
    process = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return_code = process.wait()
    logging.info("args: {}".format(command_line))
    logging.info("out: {}".format(out))
    logging.info("err: {}".format(err))
    logging.info("return_code: {}".format(return_code))
    return return_code, out


class Docker(object):

    def list_container(self):
        _ , result = exec_command(DOCKER_LIST_COMMAND)
        result = result.split("\n")[:-1]
        return result

    def memory_used(self, docker_name):
        _, res = exec_command(CONTAINER_STATUS_COMMAND.format(docker_name))
        res = res.split("\n")[:-1]
        result = []
        for r in res:
            r = re.match(DOCKER_STATS_REG, r)
            r = r.groupdict()
            if r["name"] == docker_name:
                result = self.unit_convert(r["memory_used"])
                break
        return result

    def send_data(self, key, value):
        command_line = "zabbix_sender -z {} -s {} -k {} -o '{}' -vv".format(ZABBIX_HOST, SERVER_NAME, key, value)
        return_code, _ = exec_command(command_line)
        return return_code

    def unit_convert(self, value):
        """Convert To MiB"""
        if len(value) < 4:
            logging.error("string length not enough, string = {}".format(value))
            raise ValueError
        i, unit = float(value[:-3]), value[-3:]
        if unit == "GiB":
            i = i*1024
        elif unit == "KiB":
            i = i / 1024
        return i



def main():
    '''Command-line parameters and decoding for Zabbix use/consumption.'''
    parser = optparse.OptionParser()
    parser.add_option('--func', help='What to do', default='get_metric')
    parser.add_option('--metric', help='Which metric to evaluate', default='')
    parser.add_option('--name', help='Docker name', default='')
    (options, args) = parser.parse_args()
    func = options.func
    if func not in FUNCTIONS:
        return
    docker = Docker()
    if func == "list_container":
        containers = docker.list_container()
        containers = [{"{#CONTAINERNAME}":c} for c in containers]
        result = json.dumps({"data":containers})
        print(result)
        docker.send_data("docker.gaojian.discovery", result)
        return
    metric = options.metric
    name = options.name

    if metric == "memory_used":
        value = docker.memory_used(name)
        key = "{}.{}[{}]".format(KEY_PREFIX, metric, name)
        print(key, value)
        docker.send_data(key, value)
    else:
        pass



if __name__ == "__main__":
    main()

