import json
import requests
import math
import numpy as np

class APIClient:
    def __init__(self, base_url='http://10.30.16.179/api/', token=None):
        self.username = None
        self.password = None
        self.access_token = token
        self.base_url = base_url
        self.headers = {}

    def get_token(self, username=None, password=None):
        if username and password:
            self.username = username
            self.password = password
        
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = requests.post(f"{self.base_url}/token/", data=auth_data)
        
        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get("access")
            print(f"Access Token: {self.access_token}")
            self.headers = {"Authorization": f"JWT {self.access_token}"}
        else:
            print(f"Failed to obtain token. Status code: {response.status_code}, Response: {response.text}")

    def _make_get_request(self, endpoint):
        """Helper method to make GET requests."""
        response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to access resource at {endpoint}. Status code: {response.status_code}, Response: {response.text}")
            return None
    
    def download_structure_file(self,id=None, filename='msdb.cif'):
        """Download a CIF file from a given URL and save it locally."""
        url=self.get_compound_by_id(id)["cif_file"]

        try:
            # Send a GET request to the URL
            response = requests.get(url, stream=True)

            # Check if the request was successful
            if response.status_code == 200:
                # Open a local file for writing in binary mode
                with open(filename, 'wb') as f:
                    # Write the content in chunks
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"File downloaded successfully: {filename}")
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_database(self):
        """Retrieve the database of chemicals compounds."""
        return self._make_get_request("chemicals_compounds/chemical_cards/")

    def get_compound_by_id(self, id):
        """Retrieve a compound by its ID."""
        return self._make_get_request(f"chemicals_compounds/chemicals_compounds/{id}/")
    
    def _format(self,value):
        if isinstance(value, str):
            return value  # Do nothing for strings
        elif isinstance(value, float):
            return str(value)  # Convert float to string
        elif isinstance(value, (np.float64, float)) and math.isnan(value):
            return None  # Return None for NaN
        else:
            return None  # Handle any other unexpected types

        # return None if math.isnan(np.round(value, 4)) else str(np.round(value, 4))
    def _tmp_fix(self,dict):
        for k,v in dict.items():
            if 'reaction' in k:
                if v==None:
                    dict[k]="-"
        return dict
    
    def _check_fields(self,input_dict=None, ):
        self.valid_keys = {
                            'file',
                            'total_energy_per_atom',
                            'mp_id',
                            'E_1D',
                            'E_2D',
                            'E_3D',
                            'band_gap',
                            'band_gap_mlhse',
                            'band_gap_mlexp',
                            'band_gap_exp',
                            'e_above_hull',
                            'reduction_limit',
                            'oxidation_limit',
                            'reduction_reaction',
                            'oxidation_reaction',
                            'reduction_limit_corrected',
                            'oxidation_limit_corrected'
                        }
        self.default_data = dict.fromkeys(self.valid_keys, None)
        return {k: input_dict[k] if k in input_dict else None for k in self.default_data.keys()}
        

    def post_structure(self, data={}):
        data=self._check_fields(input_dict=data)
        for k,v in data.items():
            data[k]=self._format(v)
    
        data=self._tmp_fix(data)     
        """Upload a chemical structure."""
         # Default to an empty dictionary if not provided
        if mp_id:=data.get('mp_id'):
            data['matproject_id']=mp_id
            response = requests.post(
                f"{self.base_url}/chemicals_compounds/chemical_cards/",
                headers=self.headers,
                data=data,)
        elif file_path := data.get('file'):
            print(file_path)
            with open(file_path, 'rb') as f:
                files = {'file': (f.name, f)}
                response = requests.post(
                    f"{self.base_url}/chemicals_compounds/chemical_cards/",
                    headers=self.headers,
                    data=data,
                    files=files
                )
            
        if response.status_code == 201:  # HTTP status code for created
            print("Chemical card created successfully:", json.dumps(response.json(), indent=4))
        else:
            print("Failed to create chemical card:", response.status_code, response.text)
        
        return response.status_code

