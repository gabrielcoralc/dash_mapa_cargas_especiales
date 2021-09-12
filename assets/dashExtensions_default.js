window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng) {
            var flag = L.icon({
                iconUrl: '/assets/pin.png',
                iconSize: [48, 48]
            });
            return L.marker(latlng, {
                icon: flag
            });
        }
    }
});