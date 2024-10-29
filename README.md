# matsolver_db_api
Python based API client for matoslver database.  


##### installation

``` 
git clone https://github.com/geonda/matsolver_db_api.git
cd matsolver_db_api 
python setup.py install 
````
###### usage
```
from msdb import api
client = api.APIClient()
materials = client.get_database()

# to print out in a nice way
import json
print(json.dumps(materials, indent=4))
```
For more see ```examples.ipynb```