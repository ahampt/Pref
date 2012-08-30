function confirmAction(str) {
	return confirm(str)
}

var timeout;

jQuery('div.navbar div.btn-group.pull-right button.dropdown-toggle').hover(
	function() {
		jQuery('div.navbar div.btn-group.pull-right').addClass('open');
		jQuery('div.navbar div.btn-group.pull-right ul.dropdown-menu').addClass('display-dropdown');
	},
	function() {
		timeout = setTimeout(function() {
			jQuery('div.navbar div.btn-group.pull-right').removeClass('open');
			jQuery('div.navbar div.btn-group.pull-right ul.dropdown-menu').removeClass('display-dropdown');
		}, 50);
	}
);

jQuery('div.navbar div.btn-group.pull-right ul.dropdown-menu').hover(
	function() {
		clearTimeout(timeout);
	},
	function() {
		jQuery('div.navbar div.btn-group.pull-right').removeClass('open');
		jQuery('div.navbar div.btn-group.pull-right ul.dropdown-menu').removeClass('display-dropdown');
	}
);
