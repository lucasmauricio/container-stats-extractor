import docker
import pprint
import json
import os

#TODO parametrize the file name
FILE_NAME = "test.csv"
full_filename = os.path.dirname(os.path.realpath(__file__)) + "/" + FILE_NAME
#TODO parametrize the container id
CONTAINER_ID = 'bea3ea3e3ddb'

def get_container_stats():
    statsObj = container.stats(decode=False, stream=False)
    stats = statsObj
    meu = dict()
    meu["name"] = stats["name"] 
    meu["read"] = stats["read"] 
    meu["preread"] = stats["preread"] 
    meu["memory_usage"] = stats["memory_stats"]["usage"] / 1024.0 / 1024.0 
    meu["memory_limit"] = stats["memory_stats"]["limit"] / 1024.0 / 1024.0 
    meu["network_in"] = stats["networks"]["eth0"]["rx_bytes"] / 1024.0 
    meu["network_out"] = stats["networks"]["eth0"]["tx_bytes"] / 1024.0 
    meu["cpu"] = stats["cpu_stats"]["cpu_usage"]["total_usage"] / 1024.0 / 1024.0 
    #TODO get disk io
    #meu["disk_io_read"] = stats["blkio_stats"]["io_service_bytes_recursive"].first["value"] / 1024.0 / 1024.0 
    return meu


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


if __name__ == '__main__':
    client = docker.from_env()
    container = client.containers.get(CONTAINER_ID)
    print (container.attrs['Config']['Image'])
    print ("Application data will be stored at '{}'".format(full_filename))
    aa = get_container_stats()
    append_data_to_file(aa)

