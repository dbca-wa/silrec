import WMSCapabilities from 'ol/format/WMSCapabilities';
import TileWMS from 'ol/source/TileWMS';
import TileLayer from 'ol/layer/Tile';
import GeoJSON from 'ol/format/GeoJSON';
import Feature from 'ol/Feature';
import { Polygon } from 'ol/geom';
import { Style, Fill, Stroke } from 'ol/style';
import { Control } from 'ol/control';
import { utils } from '@/utils/hooks';

// Tile server url
var url = `${env['gis_server_url']}/geoserver/ows/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities`; // KB
// Layer to use as map base layer
// TODO: Update to kb once baselayers are available
export var baselayer_name = 'mapbox-streets'; // KMI
// export var baselayer_name = 'mapbox-dark'

/**
 * Returns layers at map event pixel coordinates
 * @param {Proxy} map_component A map component instance
 * @param {Event} evt An Event object
 * @returns an array of layers
 */
export function layerAtEventPixel(map_component, evt) {
    let layer_at_pixel = [];
    map_component.map.getLayers().forEach((layer) => {
        if (!map_component.informing) {
            return;
        }
        let pixel = map_component.map.getEventPixel(evt.originalEvent);
        let data = layer.getData(pixel);
        // Return if no data or the alpha channel in RGBA is zero (transparent)
        if (!data || data[3] == 0) {
            return;
        }
        layer_at_pixel.push(layer);
    });

    return layer_at_pixel;
}

/**
 * Queries the WMS server for its capabilities and adds optional layers to a map
 * @param {Proxy} map_component A map component instance
 */
export async function addOptionalLayers(map_component) {
    let parser = new WMSCapabilities();

    await fetch(url)
        .then(function (response) {
            return response.text();
        })
        .then(function (text) {
            let result = parser.read(text);
            let layers = result.Capability.Layer.Layer.filter((layer) => {
                return (
                    layer['Name'] ===
                    'kaartdijin-boodja-public:CPT_DBCA_LEGISLATED_TENURE'
                );
            });

            for (let j in layers) {
                let layer = layers[j];

                let l = new TileWMS({
                    url: `${env['gis_server_url']}/geoserver/ows`, // KB
                    crossOrigin: 'anonymous', // Data for a image tiles can only be retrieved if the source's crossOrigin property is set (https://openlayers.org/en/latest/apidoc/module-ol_layer_Tile-TileLayer.html#getData)
                    params: {
                        FORMAT: 'image/png',
                        VERSION: '1.1.1',
                        tiled: true,
                        STYLES: '',
                        LAYERS: `${layer.Name}`,
                    },
                });

                let tileLayer = new TileLayer({
                    name: layer.Name,
                    abstract: layer.Abstract.trim(),
                    title: layer.Title.trim(),
                    visible: false,
                    extent: layer.BoundingBox[0].extent,
                    source: l,
                    invert_xy: true, // Invert the x and y coordinates
                });

                let legend_url = null;
                if (layer.Name == baselayer_name) {
                    // Don't add the baselayer to the optional layer control
                } else {
                    if (typeof layer.Style != 'undefined') {
                        legend_url = layer.Style[0].LegendURL[0].OnlineResource;
                    }
                }

                // Set additional attributes to the layer
                tileLayer.set('columns', []); // []
                tileLayer.set('display_all_columns', true); // true
                tileLayer.set('legend_url', legend_url);

                map_component.optionalLayers.push(tileLayer);
                map_component.map.addLayer(tileLayer);

                tileLayer.on('change:visible', function (e) {
                    if (e.oldValue == false) {
                        $('#legend')
                            .find('img')
                            .attr('src', this.values_.legend_url);
                        $('#legend_title').text(this.values_.title);
                    } else if (e.oldValue == true) {
                        $('#legend_title').text('');
                        $('#legend').find('img').attr('src', '');
                        // Hide any overlays when the optional layer is turned off
                        map_component.overlay(undefined);
                    } else {
                        console.error(
                            'Cannot assess tile layer visibility change.'
                        );
                    }
                });

                // Lets ol display a popup with clicked feature properties
                map_component.map.on('singleclick', function (evt) {
                    if (map_component.mode !== 'info') {
                        return;
                    }
                    let coordinate = evt.coordinate;
                    layerAtEventPixel(map_component, evt).forEach((lyr) => {
                        if (
                            lyr.values_.name === tileLayer.getProperties().name
                        ) {
                            let c = coordinate;
                            if (tileLayer.getProperties().invert_xy) {
                                c = [coordinate[1], coordinate[0]];
                            }
                            let point = `POINT (${c.join(' ')})`;
                            let query_str = _helper.geoserverQuery.bind(this)(
                                point,
                                map_component
                            );

                            _helper
                                .validateFeatureQuery(query_str)
                                .then(async (features) => {
                                    if (features.length === 0) {
                                        console.warn(
                                            'No features found at this location.',
                                            features
                                        );
                                        map_component.overlay(undefined);
                                    } else {
                                        map_component.overlay(
                                            coordinate,
                                            features[0]
                                        );
                                    }
                                    map_component.errorMessageProperty(null);
                                });
                        }
                    });
                });
            }
        })
        .catch((error) => {
            console.error(
                'There was an error fetching additional layers',
                error
            );
        });
}

/**
 * Sets the mode of interaction of the map.
 * @param {string} mode The mode to set the map to (layer, draw, measure)
 */
export function set_mode(mode) {
    // Toggle map mode on/off when the new mode is the old one
    if (this.mode == mode) {
        this.mode = 'layer';
    } else {
        this.mode = mode;
    }

    this.drawing = false;
    this.measuring = false;
    this.informing = false;
    this.transforming = false;
    this.errorMessageProperty(null);
    this.overlay(undefined);
    this.map.getTargetElement().style.cursor = 'default';
    this.transformSetActive(false);

    if (this.mode === 'layer') {
        this.clearMeasurementLayer();
        _helper.toggle_draw_measure_license.bind(this)(false, false);
    } else if (this.mode === 'draw') {
        this.clearMeasurementLayer();
        this.sketchCoordinates = [[]];
        this.sketchCoordinatesHistory = [[]];
        _helper.toggle_draw_measure_license.bind(this)(false, true);
        this.undoredo_forSketch.clear(); // Clear the sketch coordinates undo/redo stack
        this.drawing = true;
    } else if (this.mode === 'transform') {
        this.clearMeasurementLayer();
        this.transformSetActive(true);
        _helper.toggle_draw_measure_license.bind(this)(false, false);
        this.transforming = true;
    } else if (this.mode === 'measure') {
        _helper.toggle_draw_measure_license.bind(this)(true, false);
        this.measuring = true;
    } else if (this.mode === 'info') {
        _helper.toggle_draw_measure_license.bind(this)(false, false);
        this.informing = true;
    } else {
        console.error(`Cannot set mode ${mode}`);
        return false;
    }
    if (this.select) {
        // Call back to the map so selected features can adept their style to the new mode
        this.select.dispatchEvent({
            type: 'map:modeChanged',
            details: {
                new_mode: this.mode,
            },
        });
    }

    return true;
}

/**
 * Defines polygon feature styling depending on whether the polygon source
 * is a Registration of Interest or a Competitive Process
 * @param {object} feature A single geometry feature (e.g. a drawn polygon)
 */
export function polygon_style(feature) {
    let strokecolor = '#3498DB';
    let fillcolor = '#85C1E9';
    if (feature.get('source') === 'registration_of_interest') {
        // yellowish
        strokecolor = [244, 208, 63, 1.0];
        fillcolor = [241, 196, 15, 0.7];
    } else if (feature.get('source') === 'competitive_process') {
        // orangish
        strokecolor = [240, 178, 122, 1.0];
        fillcolor = [230, 126, 34, 0.7];
    }
    return new Style({
        fill: new Fill({
            color: fillcolor,
        }),
        stroke: new Stroke({
            color: strokecolor,
            width: 1,
        }),
    });
}

/**
 * Validate feature callback function. Calls `finnishDrawing` on the map component
 * when the feature is valid. A feature is condidered valid when it intersects with
 * the DBCS legislated land-water layer.
 * @param {string} feature The feature
 * @param {Proxy} component_map The map component
 */
export function validateFeature(feature, component_map) {
    let vm = this;
    let feature_wkt = undefined;
    if (feature === undefined) {
        // Get the WKT representation of the currently drawn polygon sketch
        feature_wkt = _helper.featureToWKT.bind(vm)();
    } else {
        // Get the WKT representation of the provided feature
        feature_wkt = _helper.featureToWKT.bind(component_map)(feature);
    }

    if (component_map === undefined) {
        component_map = vm.$refs.component_map;
    }

    let query = _helper.geoserverQuery(feature_wkt, component_map);

    _helper.validateFeatureQuery(query).then(async (features) => {
        if (features.length === 0) {
            console.warn('New feature is not valid');
            component_map.errorMessageProperty(
                'The polygon you have drawn does not intersect with any DBCA lands or water.'
            );
        } else {
            component_map.finishDrawing();
        }
    });
}

export let owsQuery = {
    version: '2.0.0',
    landwater: {
        typeName: 'kaartdijin-boodja-public:CPT_DBCA_LEGISLATED_TENURE',
        srsName: 'urn:x-ogc:def:crs:EPSG:4326',
        propertyName:
            'LEG_PIN,LEG_POLY_AREA,LEG_CLASS,LEG_IDENTIFIER,LEG_PURPOSE,LEG_VESTING,LEG_NAME,LEG_NAME_STATUS,LEG_IUCN,LEG_TENURE,LEG_ACT,LEG_CATEGORY,LEG_NOTES,LEG_AGREEMENT_PARTY,LEG_CLASSIFICATION,LEG_REGNO,SHAPE_Length,SHAPE_Area',
        geometry: 'SHAPE',
    },
};

export class FeatureAutoSaveControl extends Control {
    /** A checkbox control to toggle auto-save after changes to the map on or off
     * @param {Object} component_map The map component
     * @param {Object} [opt_options] Control option
     */
    constructor(component_map, opt_options) {
        const options = opt_options || {};
        const checked =
            component_map.autoSave != undefined ? component_map.autoSave : true;

        const checkBox = document.createElement('input');
        checkBox.type = 'checkbox';
        checkBox.checked = checked;
        checkBox.title = 'Toggle auto-save';
        checkBox.className = 'custom-ol-control';

        const element = document.createElement('div');
        element.className = 'ol-control ol-unselectable feature-auto-save';
        element.appendChild(checkBox);

        super({
            element: element,
            target: options.target,
        });

        this.component_map = component_map || {};

        checkBox.addEventListener(
            'click',
            this.handleAutoSaveToggle.bind(this),
            false
        );
    }

    handleAutoSaveToggle() {
        this.component_map.autoSave = !this.component_map.autoSave;
    }
}

/**
 * Module with map related helper functions
 */
const _helper = {
    /**
     * Toggles measure and polygon layer active or inactive
     * @param {boolean} drawForMeasure Whether to set the measure layer active or inactive
     * @param {boolean} drawForModel Whether to set the model's polygon layer active or inactive
     */
    toggle_draw_measure_license: function (drawForMeasure, drawForModel) {
        if (this.drawForMeasure) {
            this.drawForMeasure.setActive(drawForMeasure);
        }
        if (this.drawForModel) {
            this.drawForModel.setActive(drawForModel);
        }
    },
    isInvertXy: function (layerName) {
        let map_obj = null;
        if (this.$options.name === 'MapComponentWithFiltersV2') {
            map_obj = this;
        } else {
            map_obj = this.$refs.component_map;
        }
        const typeName = map_obj.queryParamsDict(layerName).typeName;
        const invert_xy = map_obj.optionalLayers.map((layer) => {
            if (layer.get('name') === typeName) {
                return layer.getProperties().invert_xy;
            }
        })[0];

        return invert_xy;
    },
    /**
     * Returns a Well-known-text (WKT) representation of a feature
     * @param {Feature} feature A feature to validate
     */
    featureToWKT: function (feature) {
        let vm = this;
        const invert_xy = _helper.isInvertXy.bind(this)('landwater');
        let flatCoordinates = [];

        // Prepare a WFS feature intersection request
        if (feature === undefined) {
            // If no feature is provided, create a feature from the current sketch
            const sketchCoordinates =
                vm.$refs.component_map.sketchCoordinates.slice();
            const coordinates = [];
            if (invert_xy) {
                // Invert the x and y coordinates
                sketchCoordinates.map((coord) => {
                    coordinates.push(coord.toReversed());
                });
            }
            coordinates.push(coordinates[0]);
            feature = new Feature({
                id: -1,
                geometry: new Polygon([coordinates]),
                label: 'validation',
                color: vm.defaultColor,
                polygon_source: 'validation',
            });

            flatCoordinates = feature.getGeometry().flatCoordinates;
        } else {
            feature
                .getGeometry()
                .getCoordinates()[0]
                .map((coord) => {
                    if (invert_xy) {
                        // Invert the x and y coordinates
                        flatCoordinates.push(coord[1], coord[0]);
                    } else {
                        flatCoordinates.push(coord[0], coord[1]);
                    }
                });
        }

        // Transform list of flat coordinates into a list of coordinate pairs,
        // e.g. ['x1 y1', 'x2 y2', 'x3 y3']
        let flatCoordinateStringPairs = flatCoordinates
            .map((coord, index) =>
                index % 2 == 0
                    ? [flatCoordinates[index], flatCoordinates[index + 1]].join(
                          ' '
                      )
                    : ''
            )
            .filter((item) => item != '');

        // Create a Well-Known-Text polygon string from the coordinate pairs
        return `POLYGON ((${flatCoordinateStringPairs.join(', ')}))`;
    },
    /**
     * Builds a query string for the geoserver based on the provided WKT
     * @param {str} wkt A geometry in Well-known-text (WKT) format
     * @param {Object} map_component The map component
     * @returns A query string for the geoserver
     */
    geoserverQuery: function (wkt, map_component) {
        let vm = this;
        if (wkt === undefined) {
            console.warn('No WKT provided');
            return;
        }
        if (map_component === undefined) {
            map_component = vm.$refs.component_map;
        }
        // The geoserver url

        let owsUrl = `${env['gis_server_url']}/geoserver/ows/?`;
        // Create a params dict for the WFS request to the land-water layer
        let paramsDict = map_component.queryParamsDict('landwater');
        let geometry_name = map_component.owsQuery.landwater.geometry;
        paramsDict['CQL_FILTER'] = `INTERSECTS(${geometry_name},${wkt})`;

        // Turn params dict into a param query string
        let params = new URLSearchParams(paramsDict).toString();
        let query = `${owsUrl}${params}`;

        return query;
    },
    /**
     * Validates an openlayers feature against a geoserver `url`.
     * @param {Feature} feature A feature to validate
     * @returns {Promise} A promise that resolves to a list of intersected features
     */
    validateFeatureQuery: async function (query) {
        let vm = this;

        let features = [];
        // Query the WFS
        vm.queryingGeoserver = true;
        let urls = [query];

        let requests = urls.map((url) =>
            utils.fetchUrl(url).then((response) => response)
        );
        await Promise.all(requests)
            .then((data) => {
                features = new GeoJSON().readFeatures(data[0]);
            })
            .catch((error) => {
                console.error(error.message);
                vm.errorMessage = error.message;
            });

        return features;
    },
};
