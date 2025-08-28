# matsolver_db_api
Python based API client for matoslver database.  


##### installation

``` 
git clone https://github.com/geonda/matsolver_db_api.git
cd matsolver_db_api 
python setup.py install 
````

###### Alternatively use poetry to install package&dependences
inside the package folder with poetry.lock file
```
poetry install 
```

###### usage
```
from msdb import api
wiht api.APIClient(token='') as client:
    materials = client.get_database()

# to print out in a nice way
import json
print(json.dumps(materials, indent=4))
```
For more see ```usage.ipynb```



