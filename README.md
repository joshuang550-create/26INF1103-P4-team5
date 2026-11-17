Docker build/run commands and how to run test scripts.


To build the docker image:
docker build -t smartbite .


To run the docker image:
docker run --rm -it -v smartbite_data_vol_2:/smartbite/data -e FERNET_SECRET_KEY="vYTFX1ni17MptleqMTz1hCspMZEaqlaLPG91boo55-Q=" smartbite


To run the tests:
docker run --rm -e SMARTBITE_REQUIRE_GUI_TESTS=1 smartbite timeout 90s xvfb-run -a python -u -m unittest discover -s tests -t . -v



Phase 2 started with the creation of the Conversion branch.

First phase 2 commit was on Oct 14, 2026.
The first commit was "Added gitignore and removed secrets." 
Commit 6df9b02
