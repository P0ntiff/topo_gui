
var debugFlag = true;

var linkLabelStyler = function(edge) {
  if (debugFlag) {
    if (edge.data('lastHpvTime') == 0) {
      return 'HPV status: ' + edge.data('hpvStatus') + '\n' + edge.data('delay') + 'ms\n' + 'unverified';
    } else {
      return 'HPV status: ' + edge.data('hpvStatus') + '\n' + edge.data('delay') + 'ms\n' + 'verified ' + edge.data('timeSinceLastHpv') + 'ms ago';
    }
  } else {
    return edge.data('delay') + 'ms';
  }
}

var linkSourceLabelStyler = function(edge) {
  if (debugFlag) {
    return  + edge.data('sourceTransmitBytes') + ' transmitted\n\n'
          //+ edge.data('sourceSwitchPort') + '\n'
          + edge.data('sourceReceiveBytes') + ' received';
  } else {
    //return edge.data('sourceSwitchPort');
    return '';
  }
}

var linkDestLabelStyler = function(edge) {
  if (debugFlag) {
    return  + edge.data('destReceiveBytes') + ' received\n\n'
          //+ edge.data('sourceSwitchPort') + '\n'
          + edge.data('destTransmitBytes') + ' transmitted';
  } else {
    return '';
  }
}

var linkColorManager = function(edge) {
  if ((edge.data('hpvStatus') == 0) && (edge.data('lastHpvTime') == 0)) {
    // unverified yet, should be yellow
    return '#FFD700';
  } else if ((edge.data('hpvStatus') == 0) && (edge.data('lastHpvTime') != 0)) {
    // suspicious link, should be red
    return '#FF0000';
  } else {
    // okay link, should be green
    return '#32CD32';
  }
}

var linkPatternManager = function(edge) {
  if (edge.data('timeSinceLastHpv') > 1000) {
    return 'dotted';
  } else if (edge.data('timeSinceLastHpv') > 500) {
    return 'dashed';
  } else {
    return 'solid';
  }
}


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
          //'background-color': '#0099ff',
          //'line-color': '#32CD32',
          //'source-label': 'data(sourceSwitchPort)',
          //'source-text-offset': '1.5em',
          //'text-outline-opacity': 0.1,
        }
      },
      {
        selector: '.switch-switch-link',
        style: {
          'line-color': linkColorManager,
          'line-style': linkPatternManager,
          'font-size': '0.8em',
          'label': linkLabelStyler,
          'source-label': linkSourceLabelStyler,
          'target-label': linkDestLabelStyler,
          'text-rotation': 'autorotate',
          'source-text-rotation': 'autorotate',
          'target-text-rotation': 'autorotate',
          'text-wrap': 'wrap',
          'source-text-offset': '4em',
          'target-text-offset': '4em',
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 3,
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

var layoutOptionsWithController = {
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

var layoutOptionsWithoutController = {
  name: 'circle',
  directed: false,
  circle: false,
  fit: true, // whether to fit the viewport to the graph
  padding: 30, // padding used on fit
  boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
  avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
  avoidOverlapPadding: 10, // extra spacing around nodes when avoidOverlap: true
  nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
};

var layoutHandler = function() {
  if ((cy.getElementById('controller') != null) && (cy.nodes('.controller').length > 0)) {
    let layout = cy.elements().layout(layoutOptionsWithController);
    layout.run();
  } else {
    let layout = cy.elements().layout(layoutOptionsWithoutController);
    layout.run();
  }
};

var addNetworkElements = function() {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      cy.add(JSON.parse(this.responseText));
      layoutHandler();
    }
  }
  xhr.open("GET", "networkElements.json", true);
  xhr.send();
};

let counter = 0;
let prevTopoData = null;
let currTopoData = null;
let prevLinkData = null;
let currLinkData = null;
var updateNetwork = function() {
  if (counter < 100) {
    // topology request
    // var topoReq = new XMLHttpRequest();
    // topoReq.onreadystatechange = function() {
    //   if (this.readyState == 4 && this.status == 200) {
    //     topoData = JSON.parse(this.responseText);
    //     currTopoData = JSON.stringify(this.responseText);
    //     if (prevTopoData !== currTopoData) {
    //       cy.json(topoData);
    //       console.log('regened');
    //       layoutHandler();
    //     }
    //     prevTopoData = currTopoData;
    //   }
    // }
    // topoReq.open("GET", "networkElements.json", true);
    // topoReq.send();

    // link data request
    var linkDataReq = new XMLHttpRequest();
    linkDataReq.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
        linkData = JSON.parse(this.responseText);
        currLinkData = JSON.stringify(this.responseText);
        if (prevLinkData !== currLinkData) {
          for (var edgeID in linkData) {
            cy.getElementById(edgeID).json(linkData[edgeID]);
            //console.log(cy.getElementById(edgeID).json());
          }
        }
        prevLinkData = currLinkData;
      }
    }
    linkDataReq.open("GET", "networkLinkData.json", true);
    linkDataReq.send();


    // //stats request 
    // var statsReq = new XMLHttpRequest();
    // statsReq.onreadystatechange = function() {
    //   if (this.readyState == 4 && this.status == 200) {
    //     switchData = JSON.parse(this.responseText);
    //     currentData = JSON.stringify(this.responseText);
    //     if (prevData !== currentData) {
    //       for (var switchID in switchData) {
    //         cy.getElementById(switchID).json(switchData[switchID]);
    //         //console.log(cy.getElementById(switchID).json());
    //       }
    //     }
    //     prevData = currentData;
    //   }
    // }
    // statsReq.open("GET", "networkStats.json", true);
    // statsReq.send();
    counter++;
    setTimeout(updateNetwork, 1000);

  }
}

// add controller, routing elements, hosts and links
addNetworkElements();

// kick off fetch loop
updateNetwork()

// layout fix
setTimeout(layoutHandler, 1000);

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
    return '<p><div class="bold-title">' + data.name + '</div></p>'
        // '<div class="stat-label"> Packets: <span class="stat">' + data.packetCount + "</span></div>" +
        // '<div class="stat-label"> Bytes: <span class="stat">' + data.byteCount + "</span></div></p>"
  }

}]);

cy.on('tap', function(event) {
  debugFlag = !debugFlag

});

  


  
// # tags are IDs
// cy.getElementById('#h1')
// cy.style().fromJson([]).update();
//console.log(cy.layout())
