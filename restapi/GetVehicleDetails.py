import requests

def get_vehicle_details(api_url, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Failed to get vehicle details. Status code: {response.status_code}')
            return None

    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None
    


def check_vehicle_availability(vehicle_details, desired_vehicle_id):
    # Check if the desired vehicle ID is available in the details
    if any(vehicle['vehicleId'] == desired_vehicle_id for vehicle in vehicle_details.get('_embedded', {}).get('vehicles', [])):
    # if any(vehicle['vehicleId'] == desired_vehicle_id for vehicle in vehicle_details.get('content', [])):
        print(f'VehicleId {desired_vehicle_id} is available.')
    else:
        print(f'VehicleId {desired_vehicle_id} is not available.')


vehicle_url = 'https://rc.ota.eu.bosch-mobility-cloud.com/api/applications/fleet-management/vehicles?page=0&size=20'
access_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJwX3ZSenRWT3NRWlB4THp4bDdxQkViUUthMFVoSml5bkxLRW1ZWnJ6OTBZIn0.eyJleHAiOjE3MDU0MTcwMjMsImlhdCI6MTcwNTQxNjQyMywianRpIjoiNmRjNDU3OTktMDIwYS00ZDE5LWI3MzYtODI0MGY3Y2UwNWI5IiwiaXNzIjoiaHR0cHM6Ly9wMi5hdXRoei5ib3NjaC5jb20vYXV0aC9yZWFsbXMvRVVfUkJfRkxFQVRFU1QiLCJhdWQiOlsicm9sZXMtY29ubmVjdGl2aXR5Iiwicm9sZXMtbWVyY3VyIiwicm9sZXMtYmV0cyIsImFjY291bnQiLCJyb2xlcy1iZTEiXSwic3ViIjoiMzNlZTU1ZGQtMWVjMC00N2M4LWEwNTItZGVhZThjMzJiN2Q4IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoidGVjaC1jbGllbnQtMDMiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJkZWZhdWx0LXJvbGVzLWV1X3JiX2ZsZWF0ZXN0IiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJyb2xlcy1jb25uZWN0aXZpdHkiOnsicm9sZXMiOlsiQ09OTjpjYS1jZXJ0aWZpY2F0ZV9yZWFkIiwiQ09OTkVDVElWSVRZX0FETUlOIiwiQ09OTjpjZXJ0aWZpY2F0ZV9yZWFkIiwiQ09OTjpjbG91ZHN0b3JlLWJsb2JfcmVhZCIsIkNPTk46Y2xvdWRzdG9yZS1jb25maWdfZGVsZXRlIiwiQ09OTjpvcGVyYXRpb25fcmVhZCIsIkNPTk46c3Vic2NyaXB0aW9uX2RlbGV0ZSIsIkNPTk46Y2xvdWRzdG9yZS1ibG9iX2RlbGV0ZSIsIkNPTk46Y2xvdWRzdG9yZS1jb25maWdfd3JpdGUiLCJDT05OOmNsb3Vkc3RvcmUtYWNjZXNzdG9rZW5fZGVsZXRlIiwiQ09OTjpzdWJzY3JpcHRpb25fd3JpdGUiLCJDT05OOmRldmljZV93cml0ZSIsIkNPTk46b3BlcmF0aW9uX3dyaXRlIiwiQ09OTjpjbG91ZHN0b3JlLWJsb2Jfd3JpdGUiLCJDT05OOmNhLWNlcnRpZmljYXRlX2RlbGV0ZSIsIkNPTk46Y2xvdWRzdG9yZS1hY2Nlc3N0b2tlbl93cml0ZSIsIkNPTk46Y2EtY2VydGlmaWNhdGVfd3JpdGUiLCJDTE9VRF9TVE9SRV9BRE1JTiIsIkNPTk46c3Vic2NyaXB0aW9uX3JlYWQiLCJDTE9VRF9TVE9SRV9WSUVXRVIiLCJDT05OOmRldmljZV9yZWFkIiwiQ09OTjpkZXZpY2VfZGVsZXRlIiwiQ09OTjpjbG91ZHN0b3JlLWNvbmZpZ19yZWFkIl19LCJyb2xlcy1tZXJjdXIiOnsicm9sZXMiOlsiRk9UQV9BU1NJR05NRU5UX0NSRUFURSIsIkZPVEFfVVBEQVRFX1BBQ0tBR0VfUkVBRCIsIlZNU19BU1NJR05NRU5UX1NJR05PRkYiLCJWTVNfQ0FNUEFJR05fREVMRVRFIiwiRk9UQV9WRUhJQ0xFX0VDVV9BU1NJR05NRU5UX1JFQUQiLCJGb3RhT3BlcmF0b3IiLCJGT1RBX0FTU0lHTk1FTlRfVVBEQVRFIiwiVk1TX0NBTVBBSUdOX1JFQUQiLCJGT1RBX0RJU1RSSUJVVElPTl9QQUNLQUdFX1JFQUQiLCJGT1RBX1VQREFURV9QQUNLQUdFX0RFTEVURSIsIkZPVEFfRElTVFJJQlVUSU9OX1BBQ0tBR0VfVVBEQVRFIiwiRk9UQV9BU1NJR05NRU5UX0RFTEVURSIsIlZNU19DQU1QQUlHTl9DUkVBVEUiLCJGT1RBX0FTU0lHTk1FTlRfUkVBRCIsIkZPVEFfVVBEQVRFX1BBQ0tBR0VfVVBEQVRFIiwiRk9UQV9ESVNUUklCVVRJT05fUEFDS0FHRV9ERUxFVEUiLCJGT1RBX0RJU1RSSUJVVElPTl9QQUNLQUdFX0NSRUFURSIsIkZPVEFfVVBEQVRFX1BBQ0tBR0VfQ1JFQVRFIl19LCJyb2xlcy1iZXRzIjp7InJvbGVzIjpbIk9GQ19WU0NfREVGSU5JVElPTl9QUk9WSURFUiIsIk9GQ19DQUxMRVIiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfSwicm9sZXMtYmUxIjp7InJvbGVzIjpbIkZNX0NIQU5HRV9BTEwiLCJEQV9DSEFOR0VfQUxMIiwiUk1fQ0hBTkdFX0FMTCIsIkFDVFVBVE9SIiwiRk1fREVWSUNFX1VORElTUEFUQ0giLCJSRF9SRUFEX0FMTCIsIlJEX0NIQU5HRV9BTEwiLCJEQV9SRUFEX0FMTCIsIkZNX1JFQURfQUxMIiwiRENfUkVBRF9BTEwiLCJSTV9SRUFEX0FMTCIsIkFDQ0VTUyIsIkZNX0RFVklDRV9SRUdJU1RSQVRJT04iXX19LCJzY29wZSI6Im9wZW5pZCBzeXN0ZW0gY2xvdWQtc3RvcmUiLCJjbGllbnRJZCI6InRlY2gtY2xpZW50LTAzIiwiY2xpZW50SG9zdCI6IjE5NC4zOS4yMTguMjMiLCJjbGllbnRBZGRyZXNzIjoiMTk0LjM5LjIxOC4yMyIsInRpZCI6IkVVX1JCX0ZMRUFURVNUIn0.OPUt_bjYbw38H9-TbPLB2AFmCxEjuXv6ZNwu6gW4WivBZ6J7EmshElnJsQUWMUO-aKyu59t4yFcq5ChBjPJnmSLIBmEO5b1z0xaxIYOS-4fByEK9zyFoDdshEq--H9kdcoAYSIcNR0w67ek3_0XFmc6hC_Ey392VnHriP5XY6a16h5eP9MERhPhltDZV_pnXRvYAxzrVtKBuAv_NP-wG7oooAeL3JXO8Jo-SI4PVj2dzMMVNDAFXaNcqtg1uhVQ0AiFxcO7zEJZzj2D-IgH_H0tmHS-93TdqXuZL9d9fgx26sD5udDRT6b5WOG3mKMMIud0VfFHjxqCZl9RkHw6YoQ'
desired_vehicle_id = '43717197-bc95-49bf-b82f-1505d33c14b2'

vehicle_details = get_vehicle_details(vehicle_url, access_token)

if vehicle_details:
    print('Vehicle Details:')
    print(vehicle_details)
    check_vehicle_availability(vehicle_details, desired_vehicle_id)
else:
    print('Failed to retrieve vehicle details.')



