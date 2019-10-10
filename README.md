

# Usage

First run Floodlight with REST API running (assumed at localhost:8080)

Then run python script with a poll rate, to request data and format necessary JSON.

Can also add an optional parameter to specify whether to ignore the controller in the GUI (default is false).

```
    python buildGraph.py <poll-time-in-seconds> [<ignore-controller>]{true|false}
```

Open index.html in Firefox (chrome currently bugged).

To stop python script, use ```Ctrl+c```