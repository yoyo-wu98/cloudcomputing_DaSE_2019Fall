$(document).ready(function() {
    $.ajax({
        url: 'http://10.24.9.203:8080/start',
        type: 'post',
        data: {}
    });
});

var redUrl = "./png/red.png";
var blueUrl = "./png/map-marker.png";
var trickUrl = "./png/wx_trick_1.png"
var LeafIcon = L.Icon.extend({
    options: {
        iconSize: [25, 25],
    }
});

var blueIcon = new LeafIcon({
    iconUrl: blueUrl
});

var redIcon = new LeafIcon({
    iconUrl: redUrl
});

var trickIcon = new LeafIcon({
    iconSize: [50, 50],
    iconUrl: trickUrl
});


var map = L.map('map').fitWorld()
    .setView([30.26685, -97.75206], 16);

L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var preview_node;
var cnt = 0;
var trick_cnt = 0;
var popup = L.popup();

var control = L.Routing.control(L.extend(window.lrmConfig, {
    waypoints: [
        // L.latLng(preview_node[0], preview_node[1]),
        // L.latLng(e.latlng.lat, e.latlng.lng)
    ],
    geocoder: L.Control.Geocoder.nominatim(),
    routeWhileDragging: true,
    reverseWaypoints: true,
    showAlternatives: true,
    altLineOptions: {
        styles: [{
                color: 'black',
                opacity: 0.15,
                weight: 9
            },
            {
                color: 'white',
                opacity: 0.8,
                weight: 6
            },
            {
                color: 'blue',
                opacity: 0.5,
                weight: 2
            }
        ]
    }
})).addTo(map);

function myFunction() {
    $.ajax({
        url: 'http://10.24.9.203:8080/cal',
        type: 'post',
        data: {},
        success: function(response) {
            console.log(response);
            if (!preview_node) {} else {
                entries = [response.Latitude, response.Longitude];
                L.marker(entries, {
                    icon: redIcon
                }).addTo(map).bindPopup("<b>We recommend for you the node:" + response.Latitude + "," + response.Longitude + ".</b>").openPopup();
            }
        }
    });
    console.log("wtf");

}
L.Routing.errorControl(control).addTo(map);

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("You clicked the map at " + e.latlng.toString())
        .openOn(map);
    // if (!preview_node) {
    //     console.log("the start point is" + e.latlng.toString());
    //     preview_node = e.latlng;
    //     control.spliceWaypoints(0, 1, {
    //         "lat": e.latlng.lat,
    //         "lng": e.latlng.lng
    //     });
    // } else {
    //     console.log(preview_node);
    //     control.spliceWaypoints(cnt, cnt + 1, {
    //         "lat": e.latlng.lat,
    //         "lng": e.latlng.lng
    //     });
    //     preview_node = e.latlng;
    // }
    // cnt++;
    // console.log(typeof(e.latlng["lat"].toString()));
    $.ajax({
        url: 'http://10.24.9.203:8080/send',
        type: 'post',
        dataType: 'json',
        data: {
            "lati": e.latlng["lat"].toString(),
            "longi": e.latlng["lng"].toString()
        },
        success: function(response) {
            console.log(response);
            entries = [response.Latitude, response.Longitude];
            if (trick_cnt == 4) {
                L.marker(entries, {
                    icon: trickIcon
                }).addTo(map).bindPopup("<b>node:" + response.Latitude + "," + response.Longitude + "</b>").openPopup();
            } else {
                // L.marker(entries, {
                //     icon: redIcon
                // }).addTo(map).bindPopup("<b>Lucky dog</b>");
            }

            if (cnt < -1) {
                var control1 = L.Routing.control(L.extend(window.lrmConfig, {
                    waypoints: [
                        L.latLng(preview_node[0], preview_node[1]),
                        L.latLng(response.Latitude, response.Longitude)
                    ],
                    geocoder: L.Control.Geocoder.nominatim(),
                    routeWhileDragging: true,
                    reverseWaypoints: true,
                    showAlternatives: true,
                    altLineOptions: {
                        styles: [{
                                color: 'black',
                                opacity: 0.15,
                                weight: 9
                            },
                            {
                                color: 'white',
                                opacity: 0.8,
                                weight: 6
                            },
                            {
                                color: 'blue',
                                opacity: 0.5,
                                weight: 2
                            }
                        ]
                    }
                })).addTo(map);
                L.Routing.errorControl(control1).addTo(map);
            } else {
                if (!preview_node) {
                    console.log("the start point is" + response.toString());
                    preview_node = entries;
                    control.spliceWaypoints(0, 1, {
                        "lat": response.Latitude,
                        "lng": response.Longitude
                    });
                } else {
                    console.log(preview_node);
                    control.spliceWaypoints(cnt, cnt + 1, {
                        "lat": response.Latitude,
                        "lng": response.Longitude
                    });

                    preview_node = entries;
                }
            }



            L.Routing.errorControl(control).addTo(map);
            cnt++;
            trick_cnt++;

        }
    });
    //TODO： bind pop
}

map.on('click', onMapClick);