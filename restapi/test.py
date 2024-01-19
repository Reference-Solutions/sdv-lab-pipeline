def createDevice(self,deviceId):
        body = '{"deviceId": "deviceIdtest","model": "NATIVE","iccId": 9991101200003204007,"serialNumber": 2774957644,"customAttributes": {"mobileNumber": "0755654555"} }'
        token = self.get_access_token(deviceId)
        print("body: " + body)

        curl_command = ['curl', '-X', 
                        'POST', 'https://api.devices.eu.bosch-mobility-cloud.com/v2/devices',
                        '-H', 'accept: application/hal+json',
                        '-H', 'Authorization: ' + token,
                        '-H', 'Content-Type: application/json',
                        '-d', '' + body 
                    ]


        print("curl_command: " + str(curl_command))

        try:
            print("\n" + Fore.BLUE + "Create device \n" + Fore.WHITE)

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
        
            print(Fore.GREEN + "Send url for 'Create device ' done successfully" + Fore.WHITE)
        except:
            print(Fore.RED + "Send url for 'Create device' failed" + Fore.WHITE)
