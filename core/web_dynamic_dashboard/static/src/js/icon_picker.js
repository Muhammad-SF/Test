$( document ).ready(function() {
    console.log('Icon Picker');
    $('body').on('mouseover', 'input.icon_picker:not(.iconpicker-input)', function() {
        // Handler for .load() called.
        console.log('Icon Picker Loaded');
        $('input.icon_picker').iconpicker(
            {
                fullClassFormatter: function(val) {
                    return 'fa ' + val;
                },
                placement:'topRight'
            }
        );
    });
});