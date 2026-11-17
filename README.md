Docker build/run commands and how to run test scripts.



To build the docker image:
docker build -t smartbite2 .



To run the docker image:
docker run --rm -it -v smartbite\_data\_vol\_2:/smartbite/data -e FERNET\_SECRET\_KEY="REFER TO secret.key IN SUBMISSION ZIP" smartbite2



To run the tests:
docker run --rm -e SMARTBITE\_REQUIRE\_GUI\_TESTS=1 smartbite2 timeout 90s xvfb-run -a python -u -m unittest discover -s tests -t . -v



Phase 2 started with the creation of the Conversion branch.

First phase 2 commit was on Oct 14, 2026.
The first commit was "Added gitignore and removed secrets."
Commit 6df9b02

