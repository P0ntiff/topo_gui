
var cy = cytoscape({
    container: document.getElementById('cy'),
  
    boxSelectionEnabled: true,
    autounselectify: true,

    style: [ // the stylesheet for the graph
      {
        selector: 'node',
        style: {
          //'label': 'data(id)',
          'font-weight': 'bold',
          'width': '4em',
          'height': '4em'
        }
      },
      {
        selector: '.controller',
        style: {
          'background-image': './assets/controller.png',
          'background-clip': 'none',
          'background-fit': "cover",
          'background-opacity': 0,
        }
      },
      {
        selector: '.switch',
        style: {
          'background-image': './assets/switch.png',
          'background-clip': 'none',
          'background-fit': "cover",
          'background-opacity': 0,
        }
      },
      {
        selector: '.host',
        style: {
          'background-image': './assets/host.png',
          'background-clip': 'none',
          'background-fit': "cover",
          'background-opacity': 0,
        }
      },      
      {
        selector: '.host-switch-link',
        style: {
          'background-color': '#0099ff',
          'source-label': 'data(sourceSwitchPort)',
          'source-text-offset': '1.5em',
          'text-outline-opacity': 0.1,
        }
      },
      {
        selector: '.switch-switch-link',
        style: {
          'background-color': '#0099ff',
          'source-label': 'data(sourceSwitchPort)',
          'target-label': 'data(destSwitchPort)',
          'source-text-offset': '1.5em',
          'target-text-offset': '1.5em',
        }
      },

      {
        selector: 'edge',
        style: {
          'width': 3,
          'line-color': '#C8C7DC',
          'curve-style': 'bezier',
          'target-arrow-color': '#ccc',
          //'target-arrow-shape': 'triangle'
        }
      },
      {
        selector: '.highlighted',
        style: {
          'background-color': '#000000',
          'line-color': '#6B6A9E',
          'transition-property': 'background-color, line-color',
          'transition-duration': '0.5s'
        }
      },
      {
        selector : '.attacker',
        style: {
          'background-color': '#666',
        }
      }
    ],

    // initial viewport state:
    zoom: 1,
    pan: { x: 0, y: 0 },
    // rendering options:
    headless: false,
    styleEnabled: true,
    hideEdgesOnViewport: false,
    hideLabelsOnViewport: false,
    textureOnViewport: false,
    motionBlur: false,
    motionBlurOpacity: 0.2,
    pixelRatio: 'auto'

  });

  var layoutOptions = {
    name: 'breadthfirst',
    directed: false,
    roots: '#controller',
    circle: false,
    fit: true, // whether to fit the viewport to the graph
    padding: 30, // padding used on fit
    boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
    avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
    avoidOverlapPadding: 10, // extra spacing around nodes when avoidOverlap: true
    nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
  };
  
  var initialiseGraphElements = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
        cy.add(JSON.parse(this.responseText));
        var layout = cy.elements().layout(layoutOptions)
        layout.run();
      }
    }
    xhr.open("GET", "networkGraph.json", true);
    xhr.send();
  };

  
  var addHostsAndLinks = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
        cy.add(JSON.parse(this.responseText));
        var layout = cy.elements().layout(layoutOptions)
        layout.run();
      }
    }
    xhr.open("GET", "networkHostsAndLinks.json", true);
    xhr.send();
  };


  
  let counter = 0;
  let prevData = null;
  let currentData = null;
  var updateSwitchStats = function() {
    if (counter < 100) {
      var xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
          switchData = JSON.parse(this.responseText);
          currentData = JSON.stringify(this.responseText);
          if (prevData !== currentData) {
            for (var switchID in switchData) {
              cy.getElementById(switchID).json(switchData[switchID]);
              //console.log(cy.getElementById(switchID).json());
            }
          }
          prevData = currentData;
        }
      }
      xhr.open("GET", "networkStats.json", true);
      xhr.send();
      counter++;
      setTimeout(updateSwitchStats, 1000);
    }
  }

  // initialise graph (controller + switches)
  initialiseGraphElements();

  // add hosts and links
  addHostsAndLinks();

  // kick off stats fetch loop
  updateSwitchStats();


  cy.nodeHtmlLabel([{
    query : '.controller, .host',
    valign: "top",
    halign: "center",
    valignBox: "top",
    halignBox: "center",
    tpl: function(data) {
      return '<p><div class="bold-title">' + data.name + '</div></p>'
    }
  }])

  cy.nodeHtmlLabel([{
    query : '.switch',
    valign: "top",
    halign: "center",
    valignBox: "top",
    halignBox: "center",
    tpl: function(data) {
      return '<p><div class="bold-title">' + data.name + '</div>' + 
          '<div class="stat-label"> Packets: <span class="stat">' + data.packetCount + "</span></div>" +
          '<div class="stat-label"> Bytes: <span class="stat">' + data.byteCount + "</span></div></p>"
    }

  }]);


  


  
// # tags are IDs
// cy.getElementById('#h1')
// cy.style().fromJson([]).update();
//console.log(cy.layout())
