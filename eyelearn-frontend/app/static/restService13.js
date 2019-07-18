function postHandwrittenImage() {
                console.log("in post");
	   			var canvasObj = document.getElementById("mycanvas");
	   			var img = canvasObj.toDataURL();
	   			console.log(img);
	   			$.ajax({
	   				type: "POST",
	   				url: "https://handwriting.eyelearn.club/predictCharacter",
	   				data: img,
	   				success: function(data){
	   				    console.log(data);
	   					$('#result').append(data.prediction);
	   					var canvas  = document.getElementById('mycanvas');
                        var context = canvas.getContext("2d");
                        context.fillStyle = "#ffffff";
                        context.rect(0, 0, 300, 300);
                        context.fill();
	   				},
	   				error: function(xhr, status, error) {
                         console.log(status);
                    }
	   			});
}

function postNumbersImage() {
                console.log("in post");
	   			var canvasObj = document.getElementById("mycanvas");
	   			var img = canvasObj.toDataURL();
	   			console.log(img);
	   			$.ajax({
	   				type: "POST",
	   				url: "https://handwriting.eyelearn.club/predictNumber",
	   				data: img,
	   				success: function(data){
	   				    console.log(data);
	   					$('#result').append(data.prediction);
	   					var canvas  = document.getElementById('mycanvas');
                        var context = canvas.getContext("2d");
                        context.fillStyle = "#ffffff";
                        context.rect(0, 0, 300, 300);
                        context.fill();
	   				},
	   				error: function(xhr, status, error) {
                         console.log(status);
                    }
	   			});
}

function postAnswer() {
                console.log("in post");
                var answer = $('#result').text();
                $.ajax({
	   				type: "POST",
	   				url: "http://192.168.0.241:5000/checkWord",
	   				data: answer
	   			});

}

function getJson() {
                console.log("getting JSon");
                var answer = $('#result').text();
                console.log(answer);
                var formInfo = document.forms['send'];
                formInfo.guess.value = answer;
}