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
**wsl -e bash -c 'docker run -it --rm -e DISPLAY=$DISPLAY -e FERNET_SECRET_KEY="GET THE KEY FROM secret.key IN THE SUBMISSION ZIP" -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg -v smartbite_data_vol_2:/smartbite/data smartbite2'**


To run the tests:
**docker run --rm -e SMARTBITE_REQUIRE_GUI_TESTS=1 smartbite2 timeout 90s xvfb-run -a python -u -m unittest discover -s tests -t . -v**









Refer to the guide below for other Operating Systems or more detailed information.


## Running with Docker

Because **SmartBite** uses a desktop GUI (`tkinter`), the Docker container must be linked to your computer's display server to render the application window.

### Prerequisites
* **Docker** installed and running (Docker Desktop on Windows/macOS, or Docker Engine on Linux).
* **Windows Users:** Windows 11 (or Windows 10 build 19044+) with **WSL2 / WSLg** enabled and Docker Desktop configured to use the WSL2 engine.
* **macOS Users:** [XQuartz](https://xquartz.org) installed with **Allow connections from network clients** enabled under **Settings > Security**.

---

### 1. Build the Docker Image
From the root directory of the project, build the image:

```bash
docker build -t smartbite2 .
```

---

### 2. Run the Application

Choose the command for your operating system below. Your application data will be saved automatically in the `smartbite_data_vol_2` Docker volume.

#### Windows (PowerShell)
Run the following command to launch the container through WSLg:

```powershell
wsl -e bash -c 'docker run -it --rm -e DISPLAY=\$DISPLAY -e FERNET_SECRET_KEY="GET THE KEY FROM secret.key IN THE SUBMISSION ZIP" -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg -v smartbite_data_vol_2:/smartbite/data smartbite2'
```

*(Note: If you are already inside a WSL/Ubuntu terminal, run the `docker run ...` part directly without `wsl -e bash -c`).*

#### Linux (Bash)
Grant local Docker access to your X11 display, then start the container:

```bash
xhost +local:docker

docker run -it --rm \
  -e DISPLAY=\$DISPLAY \
  -e FERNET_SECRET_KEY="GET THE KEY FROM secret.key IN THE SUBMISSION ZIP" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v smartbite_data_vol_2:/smartbite/data \
  smartbite2
```

#### macOS (Terminal)
Start XQuartz, allow localhost connections, and run the container:

```bash
open -a XQuartz
xhost +127.0.0.1

lsof -iTCP:6000 -sTCP:LISTEN

docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -e FERNET_SECRET_KEY="GET THE KEY FROM secret.key IN THE SUBMISSION ZIP" \
  -v smartbite_data_vol_2:/smartbite/data \
  smartbite2
```

---

### Troubleshooting
* **`couldn't connect to display` on Windows:** Ensure WSLg is active by running `wsl --update` in PowerShell, restarting WSL (`wsl --shutdown`), and confirming Docker Desktop has **Use the WSL 2 based engine** enabled.
* **Permission denied on Linux:** Re-run `xhost +local:docker` in your host terminal before starting the container.