$(document).ready(function() {
    // Activate tooltip for navbar items
    $('[data-toggle="tooltip"]').tooltip();

    // Scroll effect for navbar links
    $('.nav-link').on('click', function(event) {
        if (this.hash !== "") {
            event.preventDefault();
            const hash = this.hash;
            $('html, body').animate({ scrollTop: $(hash).offset().top }, 800);
        }
    });
});
