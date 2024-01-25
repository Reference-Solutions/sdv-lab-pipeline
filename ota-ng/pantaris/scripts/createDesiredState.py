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
    swpkgBlobId = "kopd_test"
    vhpkgBlobId = "kopdd_test"  
    appName = "opd"                     # ID of the uploaded blob (needed for desiredState)
    selfUpdateVersion = "12.2"            # SW version string of the update-bundle 
    swpkgFile2Upload = "swpkg"                  # filename (incl. path) to the update-bundle to be uploaded to cloud
    vhpkgFile2Upload = "vhpkg"
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

        parser.add_argument('swpkgBlobId', help="swpkgBlobId")
        parser.add_argument('vhpkgBlobId', help="vhpkgBlobId")
        parser.add_argument('desiredStateName', help="desiredStateName")
        parser.add_argument('appName', help="appName")
        parser.add_argument('selfUpdateVersion', help="selfUpdateVersion")
        parser.add_argument('swpkgFile2Upload', help="swpkgFile2Upload")
        parser.add_argument('vhpkgFile2Upload', help="vhpkgFile2Upload")

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
        self.swpkgBlobId = sys.argv[3]
        if (self.swpkgBlobId == "NA"):
            print(Fore.RED + "Exit due to missing swpkgBlobId" + Fore.WHITE)
        self.vhpkgBlobId = sys.argv[4]
        if (self.vhpkgBlobId == "NA"):
            print(Fore.RED + "Exit due to missing vhpkgBlobId" + Fore.WHITE)
        self.desiredStateName = sys.argv[5]
        if (self.desiredStateName == "NA"):
            print(Fore.RED + "Exit due to missing desiredStateName" + Fore.WHITE)
        self.appName = sys.argv[6]
        if (self.appName == "NA"):
            print(Fore.RED + "Exit due to missing appName" + Fore.WHITE)
        self.selfUpdateVersion = sys.argv[7]
        if (self.selfUpdateVersion == "NA"):
            print(Fore.RED + "Exit due to missing selfUpdateVersion" + Fore.WHITE)
        self.swpkgFile2Upload = sys.argv[8]
        if (self.swpkgFile2Upload == "NA"):
            print(Fore.RED + "Exit due to missing swpkgFile2Upload" + Fore.WHITE)
        self.vhpkgFile2Upload = sys.argv[9]
        if (self.vhpkgFile2Upload == "NA"):
            print(Fore.RED + "Exit due to missing vhpkgFile2Upload" + Fore.WHITE)        
                                 






    ###########################################
    # Read configuration file                 #
    ###########################################
    def readConfigFile(self, json_file_path):
        """Reads the inputs ."""


 
        if (self.swpkgBlobId != "NA" and self.selfUpdateVersion != "NA" and self.swpkgFile2Upload != "NA" and
            self.vhpkgBlobId != "" and self.selfUpdateVersion != "" and self.vhpkgFile2Upload != ""):
            print("\nswpkgBlobId:  \t\t" + self.swpkgBlobId + 
                  "\nvhpkgBlobId:  \t" + self.vhpkgBlobId +
                  "\nselfUpdateVersion:  \t" + self.selfUpdateVersion + 
                  "\nswpkgFile2Upload:  \t\t" + self.swpkgFile2Upload +
                  "\nvhpkgFile2Upload:  \t\t" + self.vhpkgFile2Upload +
                  "\ndesiredStateName:  \t" + self.desiredStateName +
                  "\nblobLifeTime:  \t\t" + str(self.blobLifeTime))
            
            # check if file to upload is available
            if(os.path.isfile(self.swpkgFile2Upload) == False):
                print(Fore.RED + "File to upload " + self.swpkgFile2Upload + " not found in working directory!" + Fore.WHITE)
                return False
                
            return True
        else:
            print(Fore.RED + "blobId: " + self.blobId + 
                  "\nor selfUpdateVersion: " + self.selfUpdateVersion + 
                  "\nor swpkgFile2Upload: " + self.swpkgFile2Upload + "are not set!" + Fore.WHITE)
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

        swpkgImageValue = "https://api.devices.eu.bosch-mobility-cloud.com/v3/device/blobs/"+self.swpkgBlobId+"?token="+token1
        vhpkgImageValue = "https://api.devices.eu.bosch-mobility-cloud.com/v3/device/blobs/"+self.vhpkgBlobId+"?token="+token2
        if (self.verbosity == True):
            print("swpkgImageValue: " + swpkgImageValue)
            print("vhpkgImageValue: " + vhpkgImageValue)

        body = '{"name": "##name##","specification": {"domains": [{"id": "safety-domain","components": [{"id": "app_1","version": "##version##","config": [{"key": "image","value": "##swpkgImageValue##"}]}],"config": [{"key": "image-##appname##-app","value": "##vhpkgImageValue##"}]}],"baselines": [{"components": ["safety-domain:app_1"],"title": "##appname##-app"}]} }'
        body = body.replace("##name##",self.desiredStateName)
        body = body.replace("##version##",self.selfUpdateVersion)
        body = body.replace("##appname##",self.appName)
        body = body.replace("##swpkgImageValue##",swpkgImageValue)
        body = body.replace("##vhpkgImageValue##",vhpkgImageValue)
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
            self.uploadBlob(self.swpkgBlobId,self.swpkgFile2Upload)
            self.getBlobMetadata(self.swpkgBlobId)
            accessToken1 = self.createAccessToken(self.swpkgBlobId)
            self.uploadBlob(self.vhpkgBlobId,self.vhpkgFile2Upload)
            accessToken2 = self.createAccessToken(self.vhpkgBlobId)
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
