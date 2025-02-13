import json
import requests
import math
import numpy as np
import jsonpickle

class APIClient:
    def __init__(self, base_url='http://10.30.16.179/api/', token=None):
        self.username = None
        self.password = None
        self.access_token = token
        self.base_url = base_url
        self.headers = {"Authorization": f"JWT {self.access_token}"}

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
        return self._make_get_request("chemicals_compounds/database/")

    def get_compound_by_id(self, id):
        """Retrieve a compound by its ID."""
        return self._make_get_request(f"chemicals_compounds/chemicals_compounds/{id}/")
    
    def _format(self, value):
        if isinstance(value, dict):
            return value # Skip dictionaries by returning None
        elif isinstance(value, str):
            return value  # Do nothing for strings
        elif isinstance(value, float):
            return str(value)  # Convert float to string
        elif isinstance(value, (np.float64, float)) and math.isnan(value):
            return None  # Return None for NaN
        else:
            return None

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
                            'oxidation_limit_corrected',
                            'data',
                            'siman_obj',
                            '_tags'
                        }
        self.default_data = dict.fromkeys(self.valid_keys, None)
        # print(input_dict)
        out={}
        for k in self.default_data.keys():
            out[k]=input_dict.get(k, None)
        # print(out)

        return out
        

    def post_structure(self, data={},extra_info=None):
        data=self._check_fields(input_dict=data)
        extra_info = json.dumps(extra_info) if extra_info else None
        for k,v in data.items():
            data[k]=self._format(v)
    
        data=self._tmp_fix(data)     
        # print(data)
        """Upload a chemical structure."""
        #  Default to an empty dictionary if not provided
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
                    data={**data,**dict(extra_info=extra_info)},
                    files=files,
                )
            
        if response.status_code == 201:  # HTTP status code for created
            print("Chemical card created successfully:", json.dumps(response.json(), indent=4))
        else:
            print("Failed to create chemical card:", response.status_code, response.text)
        
        return response.status_code



    def handle_siman(self, calc_obj=None, file=None, extra_info=None, main_info=None):
        """Uploads a chemical structure."""

        main_info = self._check_fields(input_dict=main_info)
        for k, v in main_info.items():
            main_info[k] = self._format(v)
        main_info = self._tmp_fix(main_info)

        # Serialize extra_info to JSON if it exists
        extra_info = json.dumps(extra_info) if extra_info else None

        # Serialize calc_obj to JSON using jsonpickle if it exists
        calc_obj = jsonpickle.encode(calc_obj) if calc_obj else None

        data = {} # Initialize data dictionary

    
        data = {**main_info, **dict(extra_info=extra_info, siman_calc=calc_obj)}

        print("Data being sent to API:", data)  # Debugging

        try:
            # Make API request
            if file:
                
                with open(file, 'rb') as f:
                    files = {'file': (f.name, f)}
                    response = requests.post(
                        f"{self.base_url}/chemicals_compounds/chemical_cards/",
                        headers=self.headers,
                        data=data,
                        files=files
                    )
            response.raise_for_status()
            # Process successful response
            print("Chemical card created successfully:", json.dumps(response.json(), indent=4))

        except requests.exceptions.RequestException as e:
            # Handle request errors
            print(f"Failed to create chemical card: {e}")
            if response is not None:  # Check if response is defined
                print(f"Status Code: {response.status_code}, Response Text: {response.text}")
            else:
                print("No response received from the server.")
            return None # Return None to indicate failure

        return response.status_code
    
    def get_siman_calc_obj(self, chemical_card_id):
        """
        Retrieves the 'siman_obj' data from a chemical card by its ID.
        Assumes the API endpoint returns the entire chemical card data.

        Args:
            chemical_card_id: The ID of the chemical card to retrieve.

        Returns:
            The unpickled 'siman_obj' if successful, None otherwise.
        """
        try:
            response = requests.get(
                f"{self.base_url}/chemicals_compounds/chemical_cards/{chemical_card_id}/",  # Adjust endpoint if needed
                headers=self.headers,
            )
            response.raise_for_status()

            card_data = response.json()
            siman_obj_encoded = card_data['provided'].get('siman_calc')

            if siman_obj_encoded:
                # Decode JSON, then unpickle the object
                siman_obj = jsonpickle.decode(siman_obj_encoded)  #Unpickle it after it has been retrieved from JSON.
                return siman_obj
            else:
                print(f"No 'siman_calc' found for chemical card ID: {chemical_card_id}")
                return card_data

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving chemical card: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None
        except Exception as e:
            print(f"Error unpickling siman_obj: {e}")  # Specific exception for unpickling
            return None