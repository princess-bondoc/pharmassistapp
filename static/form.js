$(document).ready(function() {
		$('form').on('submit', function(event) {
			$.ajax({
				data: {
					txtMessage : $('#txtMessage').val()
				},
				type: 'POST',
				url: '/process_message'
			})

			.done(function(data) {
				alert('Message inputted.')
				// if (data.error) {
				// 	// $('#').text(data.error).show();
				// 	alert('No message inputted.')
				// }
				// else {
				// 	alert('Message inputted.')
				// }
			})

			event.preventDefault();
		});
	});