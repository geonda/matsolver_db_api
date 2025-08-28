import json
import logging
import math
import sys

import numpy as np
import requests

import jsonpickle

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Example usage in your class
logger = logging.getLogger(__name__)


class Info:
    def __init__(self) -> None:
        self.valid_keys = {
            "file",
            "total_energy_per_atom",
            "mp_id",
            "E_1D",
            "E_2D",
            "E_3D",
            "band_gap",
            "band_gap_mlhse",
            "band_gap_mlexp",
            "band_gap_exp",
            "e_above_hull",
            "reduction_limit",
            "oxidation_limit",
            "reduction_reaction",
            "oxidation_reaction",
            "reduction_limit_corrected",
            "oxidation_limit_corrected",
            "data",
            "siman_obj",
            "shared",
            "tag",
        }

    def __repr__(self) -> str:
        keys_list = sorted(self.valid_keys)
        info_str = "Valid keys:\n"
        info_str += "\n".join(f" - {key}" for key in keys_list)
        return info_str


class APIClient:
    def __init__(self, base_url="http://10.30.16.179/api/", token=None):
        self.username = None
        self.password = None
        self.access_token = token
        self.base_url = base_url
        self.headers = {"Authorization": f"JWT {self.access_token}"}
        self.valid_keys = Info().valid_keys
        self.default_data = dict.fromkeys(self.valid_keys, None)

    def __enter__(self):
        logger.info("APIClient: Opening session")
        self.session = requests.Session()
        if self.access_token:
            self.session.headers.update({"Authorization": f"JWT {self.access_token}"})
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info("APIClient: Closing session")
        if self.session:
            self.session.close()
            self.session = None
        # Returning False will propagate any exception occurred within the with block
        return False

    def get_token(self, username=None, password=None):
        if username and password:
            self.username = username
            self.password = password

        auth_data = {"username": self.username, "password": self.password}

        response = requests.post(f"{self.base_url}/token/", data=auth_data)

        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get("access")
            logger.info(f"Access Token: {self.access_token}")
            self.headers = {"Authorization": f"JWT {self.access_token}"}
            return self.access_token
        else:
            logger.error(
                f"Failed to obtain token. Status code: {response.status_code}, Response: {response.text}"
            )
            return None

    def _make_get_request(self, endpoint):
        """Helper method to make GET requests."""
        if self.session:
            response = self.session.get(f"{self.base_url}{endpoint}")
        else:
            response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"Failed to access resource at {endpoint}. Status code: {response.status_code}, Response: {response.text}"
            )
            return None

    def download_structure_file(self, id=None, filename="msdb.cif"):
        """Download a CIF file from a given URL and save it locally."""
        url = self.get_compound_by_id(id)["cif_file"]

        try:
            # Send a GET request to the URL
            # response = requests.get(url, stream=True)
            if self.session:
                response = self.session.get(url, stream=True)
            else:
                response = requests.get(url, stream=True)

            # Check if the request was successful
            if response.status_code == 200:
                # Open a local file for writing in binary mode
                with open(filename, "wb") as f:
                    # Write the content in chunks
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"File downloaded successfully: {filename}")
            else:
                logger.error(
                    f"Failed to download file. Status code: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def get_database(self):
        """Retrieve the database of chemicals compounds."""
        return self._make_get_request("chemicals_compounds/database/")

    def get_compound_by_id(self, id):
        """Retrieve a compound by its ID."""
        return self._make_get_request(f"chemicals_compounds/chemicals_compounds/{id}/")

    def _format(self, value):
        if isinstance(value, dict):
            return value  # Skip dictionaries by returning None
        elif isinstance(value, str):
            return value  # Do nothing for strings
        elif isinstance(value, float):
            return str(value)  # Convert float to string
        # elif isinstance(value, (np.float64, float)) and math.isnan(value):
        #     return None  # Return None for NaN
        elif isinstance(value, bool):
            return value
        else:
            return None

        # return None if math.isnan(np.round(value, 4)) else str(np.round(value, 4))

    def _tmp_fix(self, dict):
        for k, v in dict.items():
            if "reaction" in k:
                if v == None:
                    dict[k] = "-"
        return dict

    def _check_fields(
        self,
        input_dict=None,
    ):
        # logger.error(input_dict)
        if not input_dict:
            logger.error("Error: empty input dict")
            return None
        out = {}
        for k in self.default_data.keys():
            if "shared" in k:
                out[k] = input_dict.get(k, False)
            else:
                out[k] = input_dict.get(k, None)

        # logger.error(out)
        return out

    def post_structure(self, structure_file=None, main_info=None, extra_info=None):
        if not structure_file:
            logger.error("Error: no structure file provided")
            return None
        if not main_info:
            logger.error(
                "Error: no info to post (add main_info=dict(something=something))"
            )
            return None
        data = self._check_fields(input_dict=main_info)
        extra_info = json.dumps(extra_info) if extra_info else None
        for k, v in data.items():
            data[k] = self._format(v)

        data = self._tmp_fix(data)

        if mp_id := data.get("mp_id"):
            data["matproject_id"] = mp_id
            if self.session:
                response = self.session.post(
                    f"{self.base_url}/chemicals_compounds/chemical_cards/",
                    data=data,
                    headers=self.session.headers
                    if self.session.headers
                    else self.headers,
                )
            else:
                response = requests.post(
                    f"{self.base_url}/chemicals_compounds/chemical_cards/",
                    data=data,
                    headers=self.headers,
                )
        elif structure_file:
            logger.info(structure_file)
            with open(structure_file, "rb") as f:
                files = {"file": (f.name, f)}
                if self.session:
                    response = self.session.post(
                        f"{self.base_url}/chemicals_compounds/chemical_cards/",
                        data={**data, **dict(extra_info=extra_info)},
                        files=files,
                        headers=self.session.headers
                        if self.session.headers
                        else self.headers,
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}/chemicals_compounds/chemical_cards/",
                        data={**data, **dict(extra_info=extra_info)},
                        files=files,
                        headers=self.headers,
                    )
        else:
            logger.error("No valid mp_id or file path supplied.")
            return None

        if response.status_code == 201:
            logger.info("Chemical card created successfully")
        else:
            logger.error(
                "Failed to create chemical card:", response.status_code, response.text
            )

        return response.status_code

    def handle_siman(
        self, calc_obj=None, structure_file=None, extra_info=None, main_info=None
    ):
        if not structure_file:
            logger.error("Error: no structure file provided")
            return None
        if not main_info:
            main_info = self.default_data
        main_info = self._check_fields(input_dict=main_info)
        for k, v in main_info.items():
            main_info[k] = self._format(v)
        main_info = self._tmp_fix(main_info)

        extra_info = json.dumps(extra_info) if extra_info else None
        calc_obj = jsonpickle.encode(calc_obj) if calc_obj else None

        data = {**main_info, **dict(extra_info=extra_info, siman_calc=calc_obj)}

        logger.info("Data being sent to DB")  # Debugging

        try:
            if structure_file:
                with open(structure_file, "rb") as f:
                    files = {"file": (f.name, f)}
                    if self.session:
                        response = self.session.post(
                            f"{self.base_url}/chemicals_compounds/chemical_cards/",
                            data=data,
                            files=files,
                            headers=self.session.headers
                            if self.session.headers
                            else self.headers,
                        )
                    else:
                        response = requests.post(
                            f"{self.base_url}/chemicals_compounds/chemical_cards/",
                            data=data,
                            files=files,
                            headers=self.headers,
                        )
            else:
                if self.session:
                    response = self.session.post(
                        f"{self.base_url}/chemicals_compounds/chemical_cards/",
                        data=data,
                        headers=self.session.headers
                        if self.session.headers
                        else self.headers,
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}/chemicals_compounds/chemical_cards/",
                        data=data,
                        headers=self.headers,
                    )

            response.raise_for_status()
            logger.info(
                f"Chemical card created successfully with ID {json.loads(response.text)['id']}",
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create chemical card: {e}")
            if response is not None:
                logger.error(
                    f"Status Code: {response.status_code}, Response Text: {response.text}"
                )
            else:
                logger.error("No response received from the server.")
            return None

    def get_siman_calc_obj(self, chemical_card_id=None):
        """
        Retrieves the 'siman_obj' data from a chemical card by its ID.
        Assumes the API endpoint returns the entire chemical card data.

        Args:
            chemical_card_id: The ID of the chemical card to retrieve.

        Returns:
            The unpickled 'siman_obj' if successful, None otherwise.

        """
        if not chemical_card_id:
            return None
        try:
            endpoint = f"{self.base_url}/chemicals_compounds/chemical_cards/{chemical_card_id}/"  # Adjust endpoint if needed
            if self.session:
                response = self.session.get(endpoint)
            else:
                response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()

            card_data = response.json()
            siman_obj_encoded = card_data["provided"].get("siman_calc")

            if siman_obj_encoded:
                # Decode JSON, then unpickle the object
                siman_obj = jsonpickle.decode(
                    siman_obj_encoded
                )  # Unpickle it after it has been retrieved from JSON.
                return siman_obj
            else:
                logger.info(
                    f"No 'siman_calc' found for chemical card ID: {chemical_card_id}"
                )
                return card_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving chemical card: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Error unpickling siman_obj: {e}"
            )  # Specific exception for unpickling
            return None
