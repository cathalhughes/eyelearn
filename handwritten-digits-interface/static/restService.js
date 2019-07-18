function postHandwrittenImage() {
                console.log("in post");
	   			var canvasObj = document.getElementById("mycanvas");
	   			var img = canvasObj.toDataURL();
	   			console.log(img);
	   			$.ajax({
	   				type: "POST",
	   				url: "/predictCharacter",
	   				data: img,
	   				success: function(data){
	   				    console.log(data);
	   					$('#result').text(' Predicted Output: '+data.prediction + '\nConfidence: ' + data.confidence);
	   				},
	   				error: function(xhr, status, error) {
                         console.log(status);
                    }
	   			});
}