
    $('input[name="foto"]').change(function () {
        var input = this;
        if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                $('#imagen-preview').attr('src', e.target.result);
            };

            reader.readAsDataURL(input.files[0]);
        }
    });
