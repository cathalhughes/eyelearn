function postImage() {
	   			var img = document.getElementById("sportsImage").value;
	   			console.log(img);
	   			$.ajax({
	   				type: "POST",
	   				url: "/predictSport",
	   				data: img,
	   				success: function(data){
	   				    console.log(data);
	   					$('#result').text(' Predicted Output: '+data.prediction);
	   				},
	   				error: function(xhr, status, error) {
                         console.log(status);
                    }
	   			});
}