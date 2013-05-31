function confirmAction(str) {
	return confirm(str)
}

function ajaxGetSeenWant(movieId, movieUrl) {
	jQuery('#seen-' + movieId).parent().html(jQuery('#seen-' + movieId).parent().html().replace(/&nbsp;/g, ''));
	jQuery('#seen-' + movieId).after('<a class="btn btn-small btn-block btn-success" href="' + movieUrl + '">Options</a>');
	jQuery('#seen-' + movieId).remove();
	jQuery('#want-' + movieId).remove();
	jQuery('#loading-' + movieId).remove();
}

function ajaxSeenWant(movieId, movieUrl, staticUrl, str) {
	jQuery('#seen-' + movieId).hide();
	jQuery('#want-' + movieId).hide();
	jQuery('#seen-' + movieId).after('<img id="loading-' + movieId + '" src="' + staticUrl + 'img/loading.gif"/>');
	if(str == 'seen') {
		jQuery.get(movieUrl, { assoc : 1, add : 1, seen : 1 }, ajaxGetSeenWant(movieId, movieUrl));
	}
	else if(str == 'want') {
		jQuery.get(movieUrl, { assoc : 1, add : 1 }, ajaxGetSeenWant(movieId, movieUrl));
	}
	else {
		alert('Wrong invokation of ajaxSeenWant() in std.js');
	}
}

var timeout;

jQuery('.bt-popover').hover(function() { }, function() {
	this.show();
});

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
	if(jQuery('input')
	    .filter(function() {
		return this.name.match(/possibilities/);
	    }).length > 0) {
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
