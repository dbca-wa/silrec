/**
 * Changes (i-tag) tooltip appearance to the style of bs alert classes
 */
export function initTooltipStyling() {
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    $('i[data-bs-toggle="tooltip"]').off(); // Remove all previous handlers to not invoke them additionally
    $('i[data-bs-toggle="tooltip"]').on(
        'mouseenter',
        _callback_functions.tooltipColorize
    );
}

const _callback_functions = {
    tooltipColorize: function () {
        let color = $(this).data('color');
        $('.tooltip-inner').css({
            'background-color': `var(--bs-${color})`,
        });
    },
};
