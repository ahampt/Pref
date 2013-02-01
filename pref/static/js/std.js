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

jQuery(document).ready(function() {
	if(jQuery("input[name='imdb_possibilities']").length > 0) {
		jQuery("input[name='imdb_possibilities']").click(function() {
			jQuery('#imdb_url').val(jQuery(this).attr('value'));
			jQuery('#imdb_url').keypress(function() {
				jQuery("input[name='imdb_possibilities']").removeAttr('checked');
			});
		});
		jQuery("input[name='netflix_possibilities']").click(function() {
			jQuery('#netflix_url').val(jQuery(this).attr('value'));
			jQuery('#netflix_url').keypress(function() {
				jQuery("input[name='netflix_possibilities']").removeAttr('checked');
			});
		});
		jQuery("input[name='rottentomatoes_possibilities']").click(function() {
			jQuery('#rottentomatoes_id').val(jQuery(this).attr('value'));
			jQuery('#rottentomatoes_id').keypress(function() {
				jQuery("input[name='rottentomatoes_possibilities']").removeAttr('checked');
			});
		});
		jQuery("input[name='wikipedia_possibilities']").click(function() {
			jQuery('#wikipedia_id').val(jQuery(this).attr('value'));
			jQuery('#wikipedia_id').keypress(function() {
				jQuery("input[name='wikipedia_possibilities']").removeAttr('checked');
			});
		});
	}
});
