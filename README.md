Phase 2 started with the creation of the Conversion branch.

First phase 2 commit was on Oct 14, 2026.
The first commit was "Added gitignore and removed secrets."
Commit 6df9b02





Because SmartBite now has a GUI using Tkinter, the Docker container must be linked to your computer's display server to render the application window.
Using Windows 11 or Windows 10 build 19044+, make sure WSL2 / WSLg are enabled and Docker Desktop is configured to use the WSL2 engine.

To verify these Docker Desktop settings, open Docker Desktop, click the Settings (gear) icon > General, and make sure Use the WSL 2 based engine is checked.
Enable WSL integration. Go to Settings > Resources > WSL Integration and make sure integration is turned on for your default WSL distribution (such as Ubuntu).

Initialize WSLg by running this command in PowerShell: **wsl -e true**

You can now run the docker image once it has been built.





To build the docker image:
**docker build -t smartbite2 .**


To run the docker image:
**wsl -e bash -c 'docker run -it --rm -e DISPLAY=$DISPLAY -e FERNET_SECRET_KEY="vYTFX1ni17MptleqMTz1hCspMZEaqlaLPG91boo55-Q=" -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg -v smartbite_data_vol_2:/smartbite/data smartbite2'**


To run the tests:
**docker run --rm -e SMARTBITE_REQUIRE_GUI_TESTS=1 smartbite2 timeout 90s xvfb-run -a python -u -m unittest discover -s tests -t . -v**
