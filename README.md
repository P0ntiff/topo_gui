

# Usage

1/ Run Floodlight with REST API running (assumed at localhost:8080)

2/ Run python script with a poll rate, to request data and format necessary JSON. (optional) Add a parameter to specify whether to ignore the controller in the GUI (default is false).

```
    python buildGraph.py <poll-time-in-seconds> [<ignore-controller>]{true|false}
```

3/ Check ```networkElements.json``` and ```networkLinkData.json``` have been created in the local directory.

4/ Open index.html in Firefox. Click on-screen to toggle debug output.

5/ Stop python script with ```ctrl+c```.

# Interpreting the Graph

## Colours
* A green link indicates a verified status, where TopoGuard++ has verified the link successfully with HPV.
* A yellow link indicates a non-verified status where TopoGuard++ has not verified the link yet.
* A red link indicates a non-verified status where the link has been flagged as suspicious.

## Edge Style
* A solid line indicates the link has been verified within the last 500ms
* A dashed line indicates the link has been verified between 500ms and 1000ms ago
* A dotted line indicates the link has not been verified in the last 1000ms

# Notes:
* Chrome by default prevents local files from being queried by the browser, as a security feature. This can be disabled however. If Firefox also prevents the GUI from loading, try launching as root user as a possible fix.
* **Script only supports <=10 switches** (can be increased but hardcoded limit for now)

