window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                classes,
                colorscale,
                style,
                colorProp
            } = context.hideout; // get props from hideout
            const value = feature.properties[colorProp]; // get the value that determines the color

            if (value == 0) {
                style.fillColor = colorscale[0]; // Assign color for zero values
                return style;
            }

            for (let i = 0; i < classes.length - 1; ++i) {
                if (value > classes[i] && value <= classes[i + 1]) {
                    style.fillColor = colorscale[i];
                    break;
                }
            }
            return style;
        },
        function1: function(feature, layer, context) {
            layer.bindTooltip(
                `<table>
                <tr><th>Region</th><td>${feature.properties.cluster}</td></tr>
                <tr><th>Flow (in thou. tons)</th><td>${feature.properties.Transload_Flow}</td></tr>
            </table>`, {
                    permanent: false,
                    direction: "center",
                    className: "leaflet-tooltip-top"
                }
            );
        },
        function2: function(feature, context) {
            const {
                style,
                colorProp
            } = context.hideout; // get props from hideout
            const value = feature.properties[colorProp]; // get the value that determines the color

            if (value == 0) {
                style.fillColor = colorscale[0]; // Assign color for zero values
                return style;
            }

            for (let i = 0; i < classes.length - 1; ++i) {
                if (value > classes[i] && value <= classes[i + 1]) {
                    style.fillColor = colorscale[i];
                    break;
                }
            }
            return style;
        },
        function3: function(feature, context) {
            const {
                classes,
                colorscale,
                style,
                colorProp
            } = context.hideout; // get props from hideout
            const value = feature.properties[colorProp]; // get the value that determines the color

            if (value == 0) {
                style.fillColor = colorscale[0]; // Assign color for zero values
                style.fillOpacity = 0.8;
                return style;
            }

            for (let i = 0; i < classes.length - 1; ++i) {
                if (value > classes[i] && value <= classes[i + 1]) {
                    style.fillColor = colorscale[i];
                    style.fillOpacity = 0.8;
                    break;
                }
            }
            return style;
        },
        function4: function(feature, layer, context) {
            // Create a table for the selected properties
            let table = '<table style="width:100%">';
            table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">DESTINATION COUNTY INFO</th></tr>'; // Add a title row
            table += `<tr><td><strong>Name</strong></td><td>${feature.properties.name}</td></tr>`;
            table += `<tr><td><strong>State</strong></td><td>${feature.properties.state_name}</td></tr>`;
            table += `<tr><td><strong>Tons</strong></td><td>${feature.properties.Filtered_flow} (in thousand tons)</td></tr>`;
            table += '</table>';

            // Bind the tooltip with the table
            layer.bindTooltip(table, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        },
        function5: function(feature, latlng, context) {
            const {
                colorProp,
                colorMap,
                circleOptions
            } = context.hideout;
            const icon = L.divIcon({
                className: 'custom-icon',
                html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                   <polygon points="12,4 4,20 20,20" 
                            style="fill:${feature.properties[colorProp]};stroke:black;stroke-width:0.5" />
               </svg>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
            return L.marker(latlng, {
                icon: icon
            });
        },
        function6: function(feature, layer, context) {
            // Specify the properties you want to display
            let selectedProperties = ['Location', 'ServiceRR']; // Replace with your column names

            // Create a table for the selected properties
            let table = '<table style="width:100%">';
            table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">TRANSLOAD TERMINAL INFO</th></tr>'; // Add a title row
            selectedProperties.forEach(function(property) {
                if (feature.properties[property]) {
                    table += `<tr><td><strong><i>${property}</i></strong></td><td> ${feature.properties[property]}</td></tr>`;
                }
            });
            table += '</table>';

            // Bind the tooltip with the table
            layer.bindTooltip(table, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        },
        function7: function(feature, layer, context) {
            layer.bindTooltip(`${feature.properties.Company}`, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        },
        function8: function(feature, latlng, context) {
                const {
                    colorProp,
                    colorMap
                } = context.hideout;
                const icon = L.divIcon({
                    className: 'custom-icon',
                    html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                   <rect x="4" y="4" width="8" height="8" 
                         style="fill:${colorMap[feature.properties[colorProp]]};stroke:black;stroke-width:0.5" />
               </svg>`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });
                return L.marker(latlng, {
                    icon: icon
                });
            }

            ,
        function9: function(feature, context) {
            const {
                colorProp,
                style,
                colorMap
            } = context.hideout;
            value = feature.properties[colorProp];
            style.color = colorMap[value];
            return style;
        },
        function10: function(feature, layer, context) {
            // Specify the properties you want to display
            let selectedProperties = ['RROWNER1', 'DIVISION', 'MILES']; // Replace with your column names

            // Create a table for the selected properties
            let table = '<table style="width:100%">';
            table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">CLASS 1 RAILROAD INFO</th></tr>'; // Add a title row
            selectedProperties.forEach(function(property) {
                if (feature.properties[property]) {
                    table += `<tr><td><strong>${property}</strong></td><td> ${feature.properties[property]}</td></tr>`;
                }
            });
            table += '</table>';

            // Bind the tooltip with the table
            layer.bindTooltip(table, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        },
        function11: function(feature, context) {
            const {
                colorProp,
                style,
                colorMap
            } = context.hideout;
            value = feature.properties[colorProp];
            style.color = 'black' //colorMap[value];
            return style;
        },
        function12: function(feature, layer, context) {
            // Specify the properties you want to display
            let selectedProperties = ['RROWNER1', 'DIVISION', 'MILES']; // Replace with your column names

            // Create a table for the selected properties
            let table = '<table style="width:100%">';
            table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">CLASS 3 RAILROAD INFO</th></tr>'; // Add a title row
            selectedProperties.forEach(function(property) {
                if (feature.properties[property]) {
                    table += `<tr><td><strong>${property}</strong></td><td> ${feature.properties[property]}</td></tr>`;
                }
            });
            table += '</table>';

            // Bind the tooltip with the table
            layer.bindTooltip(table, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        },
        function13: function(feature, context) {
            const {
                weightProp,
                opacityProp,
                style
            } = context.hideout;
            style.weight = feature.properties[weightProp];
            style.opacity = feature.properties[opacityProp] || 0.8;
            return style;
        },
        function14: function(feature, layer, context) {
            let origin = feature.properties.orig_cnty_name ? feature.properties.orig_cnty_name : `Region ${feature.properties.orig_reg}`;
            let table = '<table style="width:100%">';
            table += '<tr><th colspan="2" style="text-align:center; font-weight:bold;">FLOW LINE INFO</th></tr>'; // Add a title row
            table += `<tr><td><strong>Origin</strong></td><td>${origin}</td></tr>`;
            table += `<tr><td><strong>Destination</strong></td><td> ${feature.properties.dest_cnty_name} </td></tr>`;
            table += `<tr><td><strong>Tons</strong></td><td><b>${feature.properties.tons}</b></td></tr>`;
            table += '</table>';

            layer.bindTooltip(table, {
                permanent: false,
                direction: "center",
                className: "leaflet-tooltip-top"
            });
        }
    }
});