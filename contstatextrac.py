import docker
import pprint
import json
import os
import threading
import sys

#TODO parametrize the file name
FILE_NAME = "test.csv"
full_filename = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME
#TODO parametrize the container id
CONTAINER_ID = 'bea3ea3e3ddb'

def get_container_stats2():
    statsObj = container.stats(decode=False, stream=True)
    stats = statsObj
    myData = dict()
    myData["name"] = stats["name"] 
    myData["read"] = stats["read"] 
    myData["preread"] = stats["preread"] 
    myData["cpu"] = stats["cpu_stats"]["cpu_usage"]["total_usage"] / 1024.0 / 1024.0 
    myData["memory_usage"] = stats["memory_stats"]["usage"] / 1024.0 / 1024.0 
    myData["memory_limit"] = stats["memory_stats"]["limit"] / 1024.0 / 1024.0 
    myData["network_in"] = stats["networks"]["eth0"]["rx_bytes"] / 1024.0 
    myData["network_out"] = stats["networks"]["eth0"]["tx_bytes"] / 1024.0 
    #TODO get disk io
    #myData["disk_io_read"] = stats["blkio_stats"]["io_service_bytes_recursive"].first["value"] / 1024.0 / 1024.0 
    return myData


def append_data_to_file(data_to_store):
    #print (full_filename)
    with open(full_filename, "a") as f:
        if os.stat(full_filename).st_size == 0:
            columns_title = ";".join(data_to_store.keys())
            f.write("{}\n".format(columns_title))
        
        vls = []
        for value in data_to_store.values():
            #print(value)
            if not isinstance(value, str):
                #print("not str")
                value = "{}".format(value)
            vls.append(value)
        print(vls)
        s = ";".join(vls)
        f.write("{}\n".format(s))
        f.close()


class ContainerStatsExtractor(threading.Thread):
    __container = None
    __stats = None

    def __init__(self, client, container_id):
        threading.Thread.__init__(self)
        self.__container = client.containers.get(container_id)
        print (self.__container.attrs['Config']['Image'])

    def get_stats_stream(self):
        self.__stats = self.__container.stats(decode=False, stream=True)

    def get_stats(self):
        self.__stats = self.__container.stats(decode=False, stream=False)
    
    def __parse_container_stats(self):
        if not self.__stats:
            #TODO handle this error and return the program flow
            print ("Error: stats data is empty")

        stsObj = json.loads(self.__stats.__next__())
        
        myData = dict()
        myData["name"] = stsObj["name"] 
        myData["read"] = stsObj["read"] 
        myData["preread"] = stsObj["preread"] 
        myData["cpu"] = stsObj["cpu_stats"]["cpu_usage"]["total_usage"] / 1024.0 / 1024.0 
        myData["memory_usage"] = stsObj["memory_stats"]["usage"] / 1024.0 / 1024.0 
        myData["memory_limit"] = stsObj["memory_stats"]["limit"] / 1024.0 / 1024.0 
        myData["network_in"] = stsObj["networks"]["eth0"]["rx_bytes"] / 1024.0 
        myData["network_out"] = stsObj["networks"]["eth0"]["tx_bytes"] / 1024.0 
        #TODO get disk io
        #myData["disk_io_read"] = stsObj["blkio_stats"]["io_service_bytes_recursive"].first["value"] / 1024.0 / 1024.0 
        
        return myData

    def show_container_stats(self):
        return self.__parse_container_stats()

    def persist_container_stats(self):
        #print (full_filename)
        data_to_store = self.__parse_container_stats()
        with open(full_filename, "a") as f:
            if os.stat(full_filename).st_size == 0:
                columns_title = ";".join(data_to_store.keys())
                f.write("{}\n".format(columns_title))
            
            vls = []
            for value in data_to_store.values():
                #print(value)
                if not isinstance(value, str):
                    #print("not str")
                    value = "{}".format(value)
                vls.append(value)
            print(vls)
            s = ";".join(vls)
            f.write("{}\n".format(s))
            f.close()

    def start_monitoring(self):
        #self.__counter = 0
        self.get_stats_stream()
        self.start()

    def run(self):
        while True:
            try:
                #self.__counter = self.__counter+1
                #print(self.__counter)
                self.persist_container_stats()
            except KeyboardInterrupt:
                sys.exit(0)



if __name__ == '__main__':
    client = docker.from_env()
    #container = client.containers.get(CONTAINER_ID)
    cont = ContainerStatsExtractor(client, CONTAINER_ID)
    print ("Application data will be stored at '{}'".format(full_filename))
    #cont_stats = get_container_stats()
    #append_data_to_file(cont_stats)
    #cont.get_stats()
    cont.get_stats_stream()
    cont.persist_container_stats()
    cont.start_monitoring()

