Docker build/run commands and how to run test scripts.


To build the docker image:
docker build -t smartbite .


To run the docker image:
docker run --rm -it -v smartbite_data_vol_2:/smartbite/data -e FERNET_SECRET_KEY="vYTFX1ni17MptleqMTz1hCspMZEaqlaLPG91boo55-Q=" smartbite


To run the tests:
docker run --rm smartbite python -m unittest discover -s tests -t . -v
