import subprocess
import itertools
import threading
import time
import sys, os
import json
from datetime import datetime
from colorama import Fore
import argparse
import requests




class createDesiredState:
    """ implements a tool which creates a desiredState 
        at otaNG Pantaris cloud for self-update of Owasys
        devices.
        """

    secret = ""                         # secret to do requests at otaNG restful API         
    clientId = "" 
    blobId = "NA" 
    file2Upload = "NA"         
    swpkg_blobId = "kopd_test"
    vhpkg_blobId = "kopdd_test"                       # ID of the uploaded blob (needed for desiredState)
    selfUpdateVersion = "12.2"            # SW version string of the update-bundle 
    file2Upload1 = "install_swc_app_opd.swpkg"                  # filename (incl. path) to the update-bundle to be uploaded to cloud
    file2Upload2 = "vehiclepkg_install_swc_app_opd.tar"
    blobLifeTime = 60                    # time in days the blob is kept at backend side
    verbosity = True                   # additional trace output
    tokenId = "NAtokenId" 
    accessToken2 = "NAtokenId"              # tokenID of the uploaded bundle (needed for desiredState)
    accessToken1 = "NAtokenId"
    desiredStateName = "dsIndia_"  # name of the desiredState on the Pantaris backend (needs to be unique)
    default_color = Fore.WHITE
    alert_color = Fore.RED 

    toolVersion = "v1.0.0"              # version of this tool createDesiredState.py

   

    ###########################################
    # Init                                    #
    ###########################################
    def __init__(self, name):
        """Reads in configuration file (json)."""
        
        parser = argparse.ArgumentParser(
            prog='createDesiredState.py',
            description="""The tool createDesiredState.py automatically creates a desiredState 
                            on the otaNG Pantaris backend, which there then can be deployed to a 
                            vehicle with an Owasys device.
                            It is called with a secret as argument from Linux console and is 
                            searching for a configuration file in json format with name 
                            desiredState.json in the working directory. It performs 5 cURL requests
                            necessary to create the desiredState at the Pantaris otaNG backend:\n\n
                            1. Create New Access Token
                            2. Upload Blob (this might take longer ~140 sec)
                            3. Get blob metadata
                            4. Create Access Token
                            5. Create Desired State
                            """,
            add_help=False) 

        parser.add_argument('secret', help="Access token for otaNG API.")
        parser.add_argument('clientID', help="Technical user for otaNG API")
        parser.add_argument('-v', '--version', action='version',
                            version=self.toolVersion, help="Show version number of createDesiredState.py and exit.")
        parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                            help='Show this help message and exit.')    
        parser.parse_args()
        
        if (len(sys.argv) <= 1):
            print(Fore.RED + "Exit due to missing secret!" + Fore.WHITE)
            sys.exit()

        self.secret = sys.argv[1]
        if (self.secret == "NA"):
            print(Fore.RED + "Exit due to missing secret!" + Fore.WHITE)
            sys.exit()
        self.clientId = sys.argv[2]
        if (self.clientId == "NA"):
            print(Fore.RED + "Exit due to missing clientId!" + Fore.WHITE)  






    ###########################################
    # Read configuration file                 #
    ###########################################
    def readConfigFile(self, json_file_path):
        """Reads in configuration file (json)."""

        #json_file_path = "./desiredState.json"  # ToDo

        # open configuration file
        # config_data = "NA"
        # try:
        #     with open(json_file_path, 'r') as j:
        #         config_data = json.loads(j.read())
        # except:
        #     print(Fore.RED + "Could not open " + json_file_path + "in working directory" + Fore.WHITE)
        #     return False

        # # retrieve values
        # if (config_data != "NA"):
        #     try:
        #         self.blobId = config_data["blobID"]
        #     except KeyError as ke:
        #         print(Fore.RED + "Key " + str(ke) + " not found in " + json_file_path + Fore.WHITE)
        #     try:
        #         self.selfUpdateVersion = config_data["selfUpdateVersion"]
        #     except KeyError as ke:
        #         print(Fore.RED + "Key " + str(ke) + " not found in " + json_file_path + Fore.WHITE)
        #     try:
        #         self.file2Upload = config_data["file2Upload"]
        #     except KeyError as ke:
        #         print(Fore.RED + "Key " + str(ke) + " not found in " + json_file_path + Fore.WHITE)
        #     try:
        #         self.verbosity = config_data["verbosity"]
        #     except KeyError as ke:
        #         print(Fore.RED + "Key " + str(ke) + " not found in " + json_file_path + Fore.WHITE)
        #     try:
        #         self.blobLifeTime = config_data["blobLifeTime"]
        #     except KeyError as ke:
        #         print(Fore.RED + "Key " + str(ke) + " not found in " + json_file_path + Fore.WHITE)

        #     # assemble desiredState name
        #     self.desiredStateName += self.blobId
 
        if (self.swpkg_blobId != "NA" and self.selfUpdateVersion != "NA" and self.file2Upload1 != "NA" and
            self.vhpkg_blobId != "" and self.selfUpdateVersion != "" and self.file2Upload2 != ""):
            print("\nblobId:  \t\t" + self.swpkg_blobId + 
                  "\nselfUpdateVersion:  \t" + self.selfUpdateVersion + 
                  "\nfile2Upload1:  \t\t" + self.file2Upload1 +
                  "\nfile2Upload2:  \t\t" + self.file2Upload2 +
                  "\ndesiredStateName:  \t" + self.desiredStateName +
                  "\nblobLifeTime:  \t\t" + str(self.blobLifeTime))
            
            # check if file to upload is available
            if(os.path.isfile(self.file2Upload1) == False):
                print(Fore.RED + "File to upload " + self.file2Upload1 + " not found in working directory!" + Fore.WHITE)
                return False
                
            return True
        else:
            print(Fore.RED + "blobId: " + self.blobId + 
                  "\nor selfUpdateVersion: " + self.selfUpdateVersion + 
                  "\nor file2Upload1: " + self.file2Upload1 + "are not set!" + Fore.WHITE)
            return False


    ###########################################
    # Create New Access Token                 #
    ###########################################
    def createNewAccessToken(self):    

        proxies_value = {'http' : 'http://rb-proxy-de.bosch.com:8080' , 'https' : 'http://rb-proxy-de.bosch.com:8080' }
        response = requests.post(url = 'https://p2.authz.bosch.com/auth/realms/EU_RB_FLEATEST/protocol/openid-connect/token', data = {"grant_type": 'client_credentials'}, auth = (self.clientId, self.secret) , proxies=proxies_value)
        self.token = ""
        output = response.json()

        ddata = json.dumps(output)
        userdata = json.loads(ddata)
        for item in userdata:
            print("\t" + item.ljust(15) + ": \t" + str(userdata[item]))

        # assemble token (needed for further requests)
        access_token = userdata["access_token"]
        token_type = userdata["token_type"]
        self.token = token_type + " " +  access_token

        print(Fore.GREEN + "Send url for 'Create New Access Token' done successfully" + Fore.WHITE)



    ###########################################
    # Upload blob                             #
    ###########################################
    def uploadBlob(self,blobId,file2Upload):
        """Issue cURL request to upload blob (rauc update-bundle)."""

        reqURL = "https://api.devices.eu.bosch-mobility-cloud.com/v3/blobs?blobId=" +blobId + "&ttlDays=" + str(self.blobLifeTime)
        curl_command = ['curl', '-X', 
                        'POST', '' + reqURL,
                        '-H', 'accept: */*',
                        '-H', 'Prefer: respond-async, wait=300',       # timeout to wait for response
                        '-H', 'Authorization: ' + self.token,
                        '-H', 'Content-Type: multipart/form-data',
                        '-F', 'file=@' + file2Upload
                        ]
 
        if (self.verbosity == True):
            print("curl_command: " + str(curl_command))

        animation_done = False
        # small animation
        def animate():
            for c in itertools.cycle(['|', '/', '-', '\\']):
                if animation_done:
                    break
                sys.stdout.write('\rloading ' + Fore.RED + c + c + c + Fore.WHITE + " ")
                sys.stdout.flush()
                time.sleep(0.3)


        animation_thread = threading.Thread(target=animate)
        try:
            print("\n" + Fore.BLUE + "Upload Blob\n" + self.default_color)
            # start animation
            start_time = time.time()
            animation_thread.start()

            # issue curl request
            process = subprocess.run(curl_command, capture_output=True)
            output = process.stdout.decode()

            # stop animation
            animation_done = True

            # calculate time for upload
            elapsed_time = round(time.time() - start_time,2)
            print(Fore.GREEN + "\n\n+++ Upload finished in " + str(elapsed_time) + " sec +++: \n\n" + Fore.WHITE)

            if (self.verbosity == True):
                print("\treceived body: " + Fore.BLUE + output + Fore.WHITE)

            # print received data (error in red)
            userdata = json.loads(output)
            cur_color = self.default_color

            for item in userdata:
                converted_time = ""
                if (item == "error"):
                    cur_color = self.alert_color
                if (item == "created" or item == "expiring"):
                    converted_time += " [" + datetime.utcfromtimestamp(int(userdata[item])/1000).strftime('%Y-%m-%d %H:%M:%S') + "]"
                print(cur_color + "\t" + item.ljust(15) + ": \t" + str(userdata[item]) +
                      converted_time + Fore.WHITE)
                cur_color = self.default_color

            print(Fore.GREEN + "Send url for 'Upload Blob' done successfully" + Fore.WHITE)
        except:
            print(self.alert_color + "Send url for 'Upload Blob' failed" + Fore.WHITE)


    ###########################################
    # Get blob metadata                       #
    ###########################################
    def getBlobMetadata(self,blobId):
        """Issue cURL request to retrieve information 
           about blod with ID = blobId."""

        reqURL = "https://api.devices.eu.bosch-mobility-cloud.com/v3/blobs/"+blobId+"/metadata"
        curl_command = ['curl', '-X', 
                        'GET', '' + reqURL,
                        '-H', 'accept: application/json',
                        '-H', 'Authorization: ' + self.token
                        ]
        if (self.verbosity == True):
            print("curl_command: " + str(curl_command))

        try:
            print("\n" + Fore.BLUE + "Get blob metadata\n" + Fore.WHITE)

            # issue curl request
            process = subprocess.run(curl_command, capture_output=True) 
            output = process.stdout.decode()

            if (self.verbosity == True):
                print("\treceived body: " + Fore.BLUE + output + Fore.WHITE)

            # print received data (error in red)
            cur_color = self.default_color
            userdata = json.loads(output)
            for item in userdata:
                converted_time = ""
                if (item == "error"):
                    cur_color = self.alert_color
                if (item == "created" or item == "expiring"):
                    converted_time += " [" + datetime.utcfromtimestamp(int(userdata[item])/1000).strftime('%Y-%m-%d %H:%M:%S') + "]"
                print(cur_color + "\t" + item.ljust(15) + ": \t" + str(userdata[item]) + 
                      converted_time + Fore.WHITE)
                cur_color = self.default_color

            print(Fore.GREEN + "Send url for 'Get blob metadata' done successfully" + Fore.WHITE)
        except:
            print(Fore.RED + "Send url for 'Get blob metadata' failed" + Fore.WHITE)


    ###########################################
    # Create Access Token                     #
    ###########################################
    def createAccessToken(self,blobId):
        """Issue cURL request to retrieve token 
        for blod with ID = blobId."""

        reqURL = "https://api.devices.eu.bosch-mobility-cloud.com/v3/blobs/"+blobId+"/access-tokens"
        curl_command = ['curl', '-X', 
                        'POST', '' + reqURL,
                        '-H', 'accept: */*',
                        '-H', 'Authorization: ' + self.token,
                        '-H', 'Content-Type: application/json',
                        '-d', '{ "ttlSeconds": 5184000,  "oneTimePass": false}'
                        ]

        if (self.verbosity == True):
            print("curl_command: " + str(curl_command))

        try:
            print("\n" + Fore.BLUE + "Create Access Token\n" + Fore.WHITE)

            # issue curl request
            process = subprocess.run(curl_command, capture_output=True) 
            output = process.stdout.decode()

            if (self.verbosity == True):
                print("\treceived body: " + Fore.BLUE + output + Fore.WHITE)

            # print received data (error in red)
            cur_color = self.default_color
            userdata = json.loads(output)
            for item in userdata:
                converted_time = ""
                if (item == "error"):
                    cur_color = self.alert_color
                if (item == "ttlSeconds"):
                    converted_time += " [" + datetime.utcfromtimestamp(int(userdata[item])/1000).strftime('%Y-%m-%d %H:%M:%S') + "]"
                print(cur_color + "\t" + item.ljust(15) + ": \t" + str(userdata[item]) + 
                      converted_time + Fore.WHITE)
                cur_color = self.default_color

            # retrieve blobID and tokenID (needed to assemble desiredState)
            if (self.blobId == userdata["blobId"]):
                 print(Fore.YELLOW + "WARNING: Received blobID is different to expected one [" + self.blobId + "]" + Fore.WHITE)
            tokenId = userdata["tokenId"]
            return tokenId

            print(Fore.GREEN + "Send url for 'Create Access Token' done successfully" + Fore.WHITE)
        except:
            print(Fore.RED + "Send url for 'Create Access Token' failed" + Fore.WHITE)

    
    ###########################################
    # Create Desired State                    #
    ###########################################
    def createDesiredState(self,token1,token2):
        """Issue cURL request to retrieve token 
        for blod with ID = blobId."""

        swpkg_imageValue = "https://api.devices.eu.bosch-mobility-cloud.com/v3/device/blobs/"+self.swpkg_blobId+"?token="+token1
        vhpkg_imageValue = "https://api.devices.eu.bosch-mobility-cloud.com/v3/device/blobs/"+self.vhpkg_blobId+"?token="+token2
        if (self.verbosity == True):
            print("imageValue1: " + imageValue1)
            print("imageValue2: " + imageValue2)

        body = '{"name": "##name##","specification": {"domains": [{"id": "safety-domain","components": [{"id": "app_1","version": "##version##","config": [{"key": "image","value": "##imageValue1##"}]}],"config": [{"key": "image-opd-app-1","value": "##imageValue2##"}]}],"baselines": [{"components": ["safety-domain:app_1"],"title": "opd-app-1"}]}}'
        body = body.replace("##name##",self.desiredStateName)
        body = body.replace("##version##",self.selfUpdateVersion)
        body = body.replace("##imageValue1##",swpkg_imageValue)
        body = body.replace("##imageValue2##",vhpkg_imageValue)
        body = body.replace("\n", "")

        if (self.verbosity == True):
            print("body: " + body)

        # curl works
        curl_command = ['curl', '-X', 
                        'POST', 'https://ota.eu.bosch-mobility-cloud.com/api/applications/ota/desiredStates',
                        '-H', 'accept: application/hal+json',
                        '-H', 'Authorization: ' + self.token,
                        '-H', 'Content-Type: application/json',
                        '-d', '' + body 
                    ]

        if (self.verbosity == True):
            print("curl_command: " + str(curl_command))

        try:
            print("\n" + Fore.BLUE + "Create Desired State\n" + Fore.WHITE)

            # issue curl request
            process = subprocess.run(curl_command, capture_output=True) 
            output = process.stdout.decode()

            if (self.verbosity == True):    
                print("\n\treceived body: " + Fore.BLUE + output + Fore.WHITE)

            # print received data (error in red)
            cur_color = self.default_color
            userdata = json.loads(output)
            for item in userdata:
                if (item == "error"):
                    cur_color = self.alert_color
                print(cur_color + "\t" + item.ljust(15) + ": \t" + str(userdata[item]) + Fore.WHITE)
                cur_color = self.default_color
        
            print(Fore.GREEN + "Send url for 'Create Desired State' done successfully" + Fore.WHITE)
        except:
            print(Fore.RED + "Send url for 'Create Desired State' failed" + Fore.WHITE)


    def start(self):
        """Runs through all steps to create a desiredState 
        at otaNG platform"""

        if (self.readConfigFile("./desiredState.json")):
            self.createNewAccessToken()
            self.uploadBlob(self.swpkg_blobId,self.file2Upload1)
            self.getBlobMetadata(self.swpkg_blobId)
            accessToken1 = self.createAccessToken(self.swpkg_blobId)
            self.uploadBlob(self.vhpkg_blobId,self.file2Upload2)
            accessToken2 = self.createAccessToken(self.vhpkg_blobId)
            self.createDesiredState(accessToken1,accessToken2)
        else:
            print(Fore.RED + "Exited due to missing parameters!" + Fore.WHITE)


###########################################
# main                                    #
###########################################
def main():
    """Main"""

    createDS = createDesiredState("createDesiredState")
    createDS.start()
    

if __name__ == "__main__":
    main()
    

#EOF

