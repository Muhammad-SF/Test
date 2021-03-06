odoo.define('web.config', function (require) {
"use strict";

var bus = require('web.core').bus;
var medias = [
    window.matchMedia('(max-width: 768px)'),
    window.matchMedia('(min-width: 768px) and (max-width: 991px)'),
    window.matchMedia('(min-width: 992px) and (max-width: 1199px)'),
    window.matchMedia('(min-width: 1200px)')
];
_.each(medias, function(m) {
    m.addListener(set_size_class);
});

var config = {
    debug: ($.deparam($.param.querystring()).debug !== undefined),
    device: {
        touch: 'ontouchstart' in window || 'onmsgesturechange' in window,
        size_class: size_class(),
        isMobile: null,
        SIZES: { XS: 0, SM: 1, MD: 2, LG: 3 },
    },
};

function size_class() {
    for(var i = 0 ; i < medias.length ; i++) {
        if(medias[i].matches) {
            return i;
        }
    }
}
function set_size_class() {
    var sc = size_class();
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        config.device.isMobile = true;
        config.device.size_class = sc;
        bus.trigger('size_class', sc);
    } else {
        if (sc !== config.device.size_class) {
            config.device.size_class = sc;
            config.device.isMobile = config.device.size_class <= config.device.SIZES.XS;
            bus.trigger('size_class', sc);
        }
    }
    if (sc !== config.device.size_class) {
        config.device.size_class = sc;
        bus.trigger('size_class', sc);
    }
}

return config;

});
