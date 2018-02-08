import docker
import pprint
import json
import os
import threading
import sys
import argparse

CONTAINER_ID = 'bea3ea3e3ddb'
FILE_NAME = "{}.csv".format(CONTAINER_ID)
full_filename = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME


class ContainerStatsExtractor(threading.Thread):
    __client = None
    __container = None
    __stats = None

    def __init__(self, container_id):
        threading.Thread.__init__(self)
        try:
            self.__client = docker.from_env()
            self.__container = self.__client.containers.get(container_id)
        except Exception:
            print ("An error ocurred when trying to access this container with the id '{}'.".format(container_id))
            self.__container = None

    def is_valid(self):
        return self.__container != None
    
    def get_container_attrs(self):
        if not self.is_valid:
            return None
        return self.__container.attrs

    def get_stats_stream(self):
        self.__stats = self.__container.stats(decode=False, stream=True)

    def get_stats(self):
        self.__stats = self.__container.stats(decode=False, stream=False)
    
    def __parse_container_stats(self):

        def calculateCPUPercent(statData):
            """
            calculating the CPU pecent utilization as suggested 
            by @shabbirkagalwala in https://github.com/docker/docker-py/issues/1795
            """
            cpuPercent = 0.0
            previousCPU = statData['precpu_stats']['cpu_usage']['total_usage']
            cpuDelta = statData['cpu_stats']['cpu_usage']['total_usage'] - previousCPU
            if 'system_cpu_usage' in statData['precpu_stats']:
                previousSystem = statData['precpu_stats']['system_cpu_usage']
            else:
                previousSystem = 0
            systemDelta = statData['cpu_stats']['system_cpu_usage'] - previousSystem
            if systemDelta > 0.0 and cpuDelta > 0.0:
                cpuPercent = (cpuDelta / systemDelta) * len(statData['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                return "{0:.2f}".format(cpuPercent)
            else:
                return cpuPercent

        if not self.__stats:
            #TODO handle this error and return the program flow
            print ("Error: stats data is empty")
            return

        stsObj = json.loads(self.__stats.__next__())
        
        myData = dict()
        myData["name"] = stsObj["name"] 
        myData["read"] = stsObj["read"] 
        myData["preread"] = stsObj["preread"] 
        myData["cpu"] = calculateCPUPercent(stsObj)
        myData["memory_usage"] = stsObj["memory_stats"]["usage"] / 1024.0 / 1024.0 
        myData["memory_limit"] = stsObj["memory_stats"]["limit"] / 1024.0 / 1024.0 
        memoryPercent = myData["memory_usage"] / myData["memory_limit"] * 100
        myData["memory_percent"] = "{0:.2f}".format(memoryPercent)
        myData["network_in"] = stsObj["networks"]["eth0"]["rx_bytes"] / 1024.0 
        myData["network_out"] = stsObj["networks"]["eth0"]["tx_bytes"] / 1024.0 
        #TODO get disk io
        #myData["disk_io_read"] = stsObj["blkio_stats"]["io_service_bytes_recursive"].first["value"] / 1024.0 / 1024.0 
        
        return myData

    def pretty_resume_data(self, data):
        return "CPU {}%, Memory {}% (usage {} MB / limit {} MB), Network in {}, out {}".format(
                data["cpu"], 
                data["memory_percent"],
                data["memory_usage"], 
                data["memory_limit"], 
                data["network_in"], 
                data["network_out"], 
            )

    def show_container_stats(self):
        return self.__parse_container_stats()

    def persist_container_stats(self):
        data_to_store = self.__parse_container_stats()
        with open(full_filename, "a") as f:
            if os.stat(full_filename).st_size == 0:
                columns_title = ";".join(data_to_store.keys())
                f.write("{}\n".format(columns_title))
            
            vls = []
            for value in data_to_store.values():
                if not isinstance(value, str):
                    value = "{}".format(value)
                vls.append(value)
            s = ";".join(vls)
            f.write("{}\n".format(s))
            print("Stat stored: {}".format(self.pretty_resume_data(data_to_store)))
            f.close()

    def start_monitoring(self):
        #self.__counter = 0
        self.get_stats_stream()
        self.start()

    def run(self):
        while True:
            self.persist_container_stats()



if __name__ == '__main__':

    # configuring the parameters parser and storing parameters in global vars
    parser = argparse.ArgumentParser(description='"API Servidor" to provide/handle employee\'s data.')

    parser.add_argument("-c", "--container", metavar='container_id', 
                        help='Container ID')
    parser.add_argument("-o", "--output", 
                        help="Output filename", metavar="output_filename")
    args = parser.parse_args()

    if args.container:
        CONTAINER_ID = args.container
    if args.output:
        FILE_NAME = args.output
        full_filename = os.path.abspath(FILE_NAME)


    cont = ContainerStatsExtractor(CONTAINER_ID)
    if not cont.is_valid():
        print ("Error: the extractor could not connect to the container with the id {}.\nExiting now.".format(CONTAINER_ID))
        sys.exit(0)

    print ("Initiating the extraction of stats data from the Docker container '{}'".format(CONTAINER_ID))
    print ("      Container ID: '{}'".format(cont.get_container_attrs()['Id']))
    print ("  Container status: '{}' (started at {})".format(cont.get_container_attrs()['State']['Status'],
                                                             cont.get_container_attrs()['State']['StartedAt']))
    print ("    Container name: '{}' (from the image '{}')".format(cont.get_container_attrs()['Name'],
                                                                 cont.get_container_attrs()['Config']['Image']))
    
    print ("Storing data in the file '{}'\n".format(full_filename))
    
    cont.start_monitoring()
    while True:
        try:
            pass
        except KeyboardInterrupt:
            sys.exit(0)
