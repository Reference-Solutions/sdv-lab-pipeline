#!/usr/bin/python3

##############################################################################
#Script          :  pantaris_api.py
#Description     :  Script can perform certain API calls defined as per
#                   https://api.devices.eu.bosch-mobility-cloud.com/api-docs/?urls.primaryName=Cloud%20Store%20%28v3%29#/Blobs%20-%20Version%203/getBlobs
#                   Implemeneted command :
#                        1. Upload_Blob    : Upload blob
#                        2. Blob_Meta_Info : Get blob meta data
#                        3. Download_Blob  : Download blob
#                        4. Delete_Blob    : Delete blob
#                        5. Blob_Page_Info : Get blobs page by page for tennat
#                        6. Get_Device_List: Get Device online info in json format
#                        7. Get_Device_Token: Get device token for specific blobID
#                   Use of command :
#                        ./pantaris_api.py -c Upload_Blob -b_id -ttl -f (specify Blob Id , time-to-live for blob , file to be uploaded )
#                        ./pantaris_api.py -c Blob_Meta_Info -b_id      (specify Blob Id to get meta info for )
#                        ./pantaris_api.py -c Download_Blob -b_id -f    (specify Blob Id , Downloaded file will be saved with this name)
#                        ./pantaris_api.py -c Delete_Blob -b_id         (specify Blob Id to get deleted )
#                        ./pantaris_api.py -c Blob_Page_Info -p -p_s    (specify page and page size))
#                        ./pantaris_api.py -c Get_Device_List -d_id      (specify device ID(filter) to get device info for )
#                        ./pantaris_api.py -c Get_Device_Token -b_id -ttls -otp  (specify Blob Id , time-to-live for token , token use onetime/multiple )
#                   Exit code:
#                         Following exit code emitted incase of specified status code repsonses.
#                         (As exit code only possible in the range of 0-255.)
#                         (status_code,exit_code):  (206,11), (400,12),(401,13),(403,14),(404,15),(206,11)
#                                                   (409,16), (413,17),(415,18),(416,19),(500,20),(xxx,50)
#                         Exit code (30) emitted incase of specified command not found.
#Note            :  Secret and user credentials -  Coming from workflow secrets - During manual run that must be supplied
##############################################################################

import os
import sys
import argparse
import requests
import time
from datetime import datetime
import json


class PANTARIS_APIS:
    def __init__(self):
        #Configuring client , urls , secret , tenant
        #Getting client , secret and user credentials -  Coming from workflow secrets
        self.client_id = ""
        self.client_secret = ""
        self.user_name = ""
        self.password = ""
        self.baseUrl = "https://p2.authz.bosch.com"
        self.serverUrl = "https://api.devices.eu.bosch-mobility-cloud.com/v3/blobs"
        # Using "device managemnet" endpoint
        self.serverUrl_device = "https://api.devices.eu.bosch-mobility-cloud.com/v2beta/devices"
        # Using "cloud store" endpoint
        self.serverUrl_device_blobs = "https://api.devices.eu.bosch-mobility-cloud.com/v3/device/blobs"
        self.realm = "EU_RB_FLEATEST"
        self.accessTokenUrl = self.baseUrl + "/auth/realms/" + self.realm + "/protocol/openid-connect/token"
        self.scope = "openid"
        self.grant_type =  "client_credentials"

    def get_access_token(self , Id):
        print("...Fetching access token...")
        # Only Proxy require not user credential required to get access token
        #_proxies = {'http' : 'http://127.0.0.1:3128' , 'https' : 'http://127.0.0.1:3128' }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in Id or "A10001-ec" in Id:
            print("Found Qemu token")
            response = requests.post(url = self.accessTokenUrl, data = {"grant_type": self.grant_type}, auth = (self.client_id, self.client_secret) )
        else:
            response = requests.post(url = self.accessTokenUrl, data = {"grant_type": self.grant_type}, auth = (self.client_id, self.client_secret) , proxies=_proxies )
        print("Access_token : HTTP  response status code : ", response.status_code)
        if response.status_code != 200 and response.status_code != 201  :
            print("# Generating auth token Failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            print("Generated auth token with success /n")
        return response.json()["access_token"] 

    def get_blob_info(self , Task , page, pagesize , blobId):
        print("Task : Performing Blob info...")
        token = self.get_access_token(blobId)
        #Providing user credentials - Proxy Authentication Required - Getting from workflow secrets
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : 'application/json' , 'Authorization' : 'Bearer {}'.format(token) }
        if Task == "Blob_Page_Info" :
           _url     = self.serverUrl + "?page=" + str(page) + "&pageSize=" + str(pagesize)
        if Task == "Blob_Meta_Info" :
           _url     = self.serverUrl +  '/' + str(blobId) + "/metadata"
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in blobId:
            response = requests.get(url=_url, headers=_headers )
        else:
            response = requests.get(url=_url, headers=_headers , proxies=_proxies)
        print("Blob_info : HTTP response status code : ", response.status_code)
        if response.status_code != 200 and response.status_code != 201  :
            print("Task-Error: Getting blob info failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            jsonResponse = response.json()
            # Formatting for pretty print json messages
            json_formatted_str = json.dumps(jsonResponse, indent=2)
            print(json_formatted_str)
            print("Task-Finish : Got required Blob info with sucess")           
      
    def upload_blob(self , blobId, time_to_live_days , file_path ):
        print("Task : Performing Blob Upload...")
        token = self.get_access_token(blobId)
        _file_path = file_path
        print(_file_path)
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : '*/*' , 'Authorization' : 'Bearer {}'.format(token) }
        _params = { 'blobId': str(blobId) , 'ttlDays': str(time_to_live_days)}
        _files = {'file': open(_file_path,'rb')}
        _url = self.serverUrl 
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in blobId:
            response = requests.post(url=_url, params=_params ,  headers=_headers , files=_files )
        else:
            response = requests.post(url=_url, params=_params ,  headers=_headers , proxies=_proxies , files=_files )
        print("upload_blob : HTTP response status code : ", response.status_code)
        if response.status_code != 201  :
            print("Task-Error: Upload blob failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            jsonResponse = response.json()
            # Formatting for pretty print json messages
            json_formatted_str = json.dumps(jsonResponse, indent=2)
            print(json_formatted_str)
            print("Task-Finish : Successfully uploaded blob")

    def download_blob(self , blobId , file_path):
        print("Task : Performing Blob Download...")
        token = self.get_access_token(blobId)
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : 'application/octet-stream' , 'Authorization' : 'Bearer {}'.format(token) }
        _file_path = file_path
        _url = self.serverUrl + "/" + str(blobId)
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in blobId:
            response = requests.get(url=_url,  headers=_headers  )
        else:
            response = requests.get(url=_url,  headers=_headers , proxies=_proxies )
        # response.content used to access payload data in raw bytes format
        print("Download_blob : HTTP response status code : ", response.status_code)
        if response.status_code != 200  :
            print("Task-Error: Download blob failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            open(_file_path, 'wb').write(response.content)
            print("Task-Finish : Successfully Downloaded blob")

    def delete_blob(self , blobId ):
        print("Task : Performing Blob delete...")
        token = self.get_access_token(blobId)
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : '*/*' , 'Authorization' : 'Bearer {}'.format(token)  }
        _url     = self.serverUrl + '/' + str(blobId)
        print(_url)
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in blobId:
            response = requests.delete(url=_url, headers=_headers )
        else:
            response = requests.delete(url=_url, headers=_headers , proxies=_proxies )
        print("Delete_blob : HTTP response status code : ", response.status_code)
        #Server is not sending any json responses. So no need to print json response
        if response.status_code != 204 :
            print("Task-Error: Delete blob failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            print("Task-Finish : Successfully deleted blob")

    def device_list(self , deviceId):
        print("Task : Getting online device list...")
        token = self.get_access_token(deviceId)
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : 'application/json' , 'Authorization' : 'Bearer {}'.format(token)  }
        _url = self.serverUrl_device
        _deviceId = deviceId
        # The size of the page to be returned- we limited to 20 - as at max six devices are available for now to get info for
        _params = { 'page': '0' , 'size': '20' , 'query': 'deviceId==*{}*'.format(_deviceId)}
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "A10001-ec" in _deviceId:
           response = requests.get(url=_url, params=_params ,  headers=_headers )
        else:
           response = requests.get(url=_url, params=_params ,  headers=_headers , proxies=_proxies )
        print("Get_Device_List : HTTP response status code : ", response.status_code)
        if response.status_code != 200  :
            print("Task-Error: Device list failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else: 
            jsonResponse = response.json()
            #creating empty dictionary to store device online informaiton
            key = ''
            value = 'Device not found'
            online_info = {}
            for device in jsonResponse['_embedded']['devices'] :
              #formatted_str = device['deviceId'] + ':'+ device['onlineStatus']['state'] + '\n'
              #outfile.write(formatted_str)
              online_info[device['deviceId']] = device['onlineStatus']['state']
              #print(online_info) 
            if len(online_info) == 0:
               online_info = {key: value}
            # Creating json file which has "device online info" - cna be used in robot tests for online device availibility   
            json_formatted_str = json.dumps(online_info, indent=2)
            with open("online_info.json", "w") as outfile:
                outfile.write(json_formatted_str)
            print("Task-Finish : Successfully getting online device info - json file generated")

    def device_token(self, blobId, time_to_live_secs, oneTimePass):
        print("...Fetching access token for device...")
        token = self.get_access_token(blobId)
        #print(token)
        #Providing user credentials - Proxy Authentication Required - Getting from workflow secrets
        #_proxies = {'http' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name,self.password), 'https' : 'http://{}:{}@127.0.0.1:3128'.format(self.user_name, self.password) }
        _proxies = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' :  'http://rb-proxy-de.bosch.com:8080' }
        _headers = { 'accept' : '*/*', 'Authorization' : 'Bearer {}'.format(token) , 'Content-Type' : 'application/json' }
        _url     = self.serverUrl +  '/' + str(blobId) + "/access-tokens"
        print(_url)
        _data = {"ttlSeconds": time_to_live_secs , 'oneTimePass' : oneTimePass}
        print(_data)
        #In case if no proxy required for example runner is running on private personal machine for qemu
        if "qemux86-64" in blobId:
            response = requests.post(url=_url,  headers=_headers , json=_data )
        else:
            response = requests.post(url=_url,  headers=_headers , proxies=_proxies , json=_data )
        print("Device Access_token : HTTP  response status code : ", response.status_code)
        if response.status_code != 200 and response.status_code != 201  :
            print("# Generating device token Failure\n\t*")
            print("HTTP", response.status_code)
            self.sys_exit(response.status_code)
        else:
            jsonResponse = response.json()
            #creating empty dictionary to store device token , URL and blockID informaiton
            token_info = {}
            token_info["TOKEN_ID"] = jsonResponse["tokenId"]
            #token_info["TOKEN_ID"] = "token will be placed here"
            token_info["BLOB_ID"] = jsonResponse["blobId"]
            token_info["URL_ID"] = self.serverUrl_device_blobs
            # Creating json file which has "token info" - can be used in robot tests for sua module  
            json_formatted_str = json.dumps(token_info, indent=2)
            with open("token_info.json", "w") as outfile:
                outfile.write(json_formatted_str)
            print("Generated device token with success /n")
    

    def sys_exit(self,status_code): 
         if status_code == 206:
            exit_code = 11
         elif status_code == 400:
            exit_code = 12
         elif status_code == 401:
            exit_code = 13
         elif status_code == 403:
            exit_code = 14
         elif status_code == 404:
            exit_code = 15  
         elif status_code == 409:
            exit_code = 16
         elif status_code == 413:
            exit_code = 17
         elif status_code == 415:
            exit_code = 18
         elif status_code == 416:
            exit_code = 19
         elif status_code == 500:
            exit_code = 20
         else:
            exit_code = 50
         sys.exit(exit_code)  


def args_menu():
    # -- START -- Args read and script config -- #
    parser = argparse.ArgumentParser(description="Help section")
    parser.add_argument('-c', '--command', type=str, help="Get Blob page by page, Blob Upload, Delete , Download for tenant, Get_Device_List, Get_Access_Token", required=True)
    parser.add_argument('-p', '--page', type=str, help="Get Blob page by page for tenant", required=False, default='2' )
    parser.add_argument('-p_s', '--page_size', type=str, help="Get Blob page by page for tenant", required=False , default='3')
    parser.add_argument('-b_id', '--blob_id', type=str, help="Specific Blob ID to upload,download,delete or metadate_read for  specific blob", required=False , default='xyzblob')
    parser.add_argument('-ttl', '--ttl_days', type=str, help="Specify time to live days for blob", required=False , default='1')
    parser.add_argument('-ttls', '--ttl_secs', type=str, help="Specify time to live seconds for token", required=False , default='60')
    parser.add_argument('-otp', '--onetimeuse', type=str, help="One time use use or multipletime use ", required=False , default='true')
    parser.add_argument('-f', '--f_path', type=str, help="Specify file to upload", required=False , default='xyz.raucb')
    parser.add_argument('-d_id', '--device_id', type=str, help="Specify device ID to get online info for", required=False , default='owa5x-A11LWA')
    parser.add_argument('-c_id', '--client_id', type=str, help="Specify client ID to authorize on Pantaris", required=False, default='')
    parser.add_argument('-c_s', '--client_secret', type=str, help="Specify client secret to authorize on Pantaris", required=False, default='')
    # parser.add_argument('-u', '--user', type=str, help="Client user name ", required=True)
    # parser.add_argument('-s', '--secret', type=str, help="Client password ", required=True)
    return parser.parse_args()

def main():
        # Getting arguments
        arg_parsed = args_menu()
        #Initialize to configure client , urls , secret , tenant
        Pantaris = PANTARIS_APIS()
        Task = arg_parsed.command
        if arg_parsed.client_id:
            Pantaris.client_id = arg_parsed.client_id
        if arg_parsed.client_secret:
            Pantaris.client_secret = arg_parsed.client_secret
        if Task == "Blob_Page_Info" or Task ==  "Blob_Meta_Info" :
           Page = arg_parsed.page
           Page_Size = arg_parsed.page_size
           blobId = arg_parsed.blob_id
           # Get blob info
           Pantaris.get_blob_info(Task ,Page,Page_Size , blobId )
        elif Task == "Upload_Blob" :
           blobId = arg_parsed.blob_id
           time_to_live_days = arg_parsed.ttl_days
           file_path = arg_parsed.f_path
           # Upload blob
           Pantaris.upload_blob(blobId, time_to_live_days , file_path)
        elif Task == "Delete_Blob" :
           blobId = arg_parsed.blob_id
           # Delete blob
           Pantaris.delete_blob(blobId)
        elif Task == "Download_Blob":
           blobId = arg_parsed.blob_id
           file_path = arg_parsed.f_path
           #Download blob
           Pantaris.download_blob(blobId , file_path)
        elif Task == "Get_Device_List":
           deviceId = arg_parsed.device_id
           #Get device list in json format
           Pantaris.device_list(deviceId)
        elif Task == "Get_Device_Token":
           blobId = arg_parsed.blob_id
           time_to_live_secs = arg_parsed.ttl_secs
           oneTimePass = arg_parsed.onetimeuse
           # Get device token along with URL and respected Blob ID in json form
           Pantaris.device_token(blobId, time_to_live_secs, oneTimePass)
        elif Task == "Get_Access_Token":
            device_id = arg_parsed.device_id
            Pantaris.get_access_token(device_id)
        else :
           print("Please specify correct command to perform certain tasks")
           # Incase of command not found exit code will be 30
           sys.exit(30)

 
if __name__ == "__main__":
       main()
