#coding: utf-8

import re
import json
import optparse
import subprocess

DOCKER_STATUS_COMMAND = "docker ps -a|grep -v 'CONTAINER ID'|awk '{print $NF}' | xargs docker stats --no-stream | grep -v 'CONTAINER'"


class Docker(object):

    def memory_used():
        res = subprocess.check_output(DOCKER_STATUS_COMMAND, shell=True)
        res = result.split("\n")[:-1]
        reg = """(?P<name>\S+) \s+ (?P<cpu>\S+) \s+ (?P<memory_used>\S+) / (?P<memory_total>\S+) \s+ (?P<memory_percent>\S+) \s+ \
        (?P<network_input>\S+) / (?P<network_output>\S+) \s+ (?P<block_input>\S+) / (?P<block_output>\S+)"""
        result = []
        for r in res:
            r = re.match(reg, r)
            r = r.groupdict()
            result.append({"container_name":r["name"], "memory_used":r["memory_used"]})
        return result

    def _send_data(self, tmpfile):
        '''Send the queue data to Zabbix.'''
        args = 'zabbix_sender -vv -c {0} -i {1}'
        if self.senderhostname:
            args = args + " -s " + self.senderhostname
        return_code = 0
        process = subprocess.Popen(args.format(self.conf, tmpfile.name),
                                            shell=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        out, err = process.communicate()
        logging.debug("Finished sending data")
        return_code = process.wait()
        logging.info("Found return code of " + str(return_code))
        if return_code == 1:
            logging.error(out)
            logging.error(err)
        else:
            logging.debug(err)
            logging.debug(out)
        return return_code


def main():
    '''Command-line parameters and decoding for Zabbix use/consumption.'''
    parser = optparse.OptionParser()
    parser.add_option('--metric', help='Which metric to evaluate', default='')
    (options, args) = parser.parse_args()
    metric = options.metric
    print("metric: ",metric)
    docker = Docker()
    if metric == "memory_used":
        result = docker.memory_used()
        print(json.dumps({"data":result}))


