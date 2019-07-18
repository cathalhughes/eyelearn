/**
 * jTinder initialization
 */

 var categories = {"sports": "predictSport",
                  "animals": "predictAnimal",
                  "vehicles": "predictVehicle",
                  "emojis": "predictEmotion"}

//$("#tinderslide").jTinder(options);
var pathname = window.location.pathname.split("/");
var category = pathname[pathname.length-1];
var endpoint = categories[category];

var options = {
// dislike callback
    onDislike: function (item) {
	    // set the status text
        $('#status').html('Dislike image ' + (item.index()+1));
        if(item.index() === 0) {

            addCards(category);
            //item.index() = 5;
        }


    },
	// like callback
    onLike: function (item) {
        sendImage(item);
    },
	animationRevertSpeed: 200,
	animationSpeed: 400,
	threshold: 1,
	likeSelector: '.like',
	dislikeSelector: '.dislike'
};


addCards(category)



/**
 * Set button action to trigger jTinder like & dislike.
 */
$('.actions .like, .actions .dislike').click(function(e){
	e.preventDefault();
	$("#tinderslide").jTinder($(this).attr('class'));
});




function getBase64Image(url) {
  var promise = new Promise(function(resolve, reject) {

    var img = new Image();
    // To prevent: "Uncaught SecurityError: Failed to execute 'toDataURL' on 'HTMLCanvasElement': Tainted canvases may not be exported."
    img.crossOrigin = "Anonymous";
    img.onload = function() {
      var canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      var ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      var dataURL = canvas.toDataURL("image/png");
      resolve(dataURL.replace(/^data:image\/(png|jpg|jpeg|pdf);base64,/, ""));
    };
    img.src = url;
  });

  return promise;
};

function sendImage(item) {
    // set the status text
    console.log(item);
    console.log(item.find('img').attr('src'));
    var image = item.find('img').attr('src');
    var promise = getBase64Image(image);
    promise.then(function (dataURL) {
        console.log(dataURL);
        $.ajax({
            url: 'https://104.196.196.153/' + endpoint,
            type: 'POST',
            data: dataURL,
            success: function (data) {
                console.log("here");
                console.log(data);

                $('#status').html(data);
                var formInfo = document.forms['send'];
                formInfo.guess.value = data;
                $('#send').trigger('submit');

            }
        });
    });

    $('#status').html('Like image ' + (item.index()+1));

}

function addCards(category) {
    var imgs = document.getElementsByTagName("img");
    $("#tinderslide").remove()
    $('.wrap').prepend("<div id='tinderslide'><ul></ul></div>");
    $.ajax({
        url: '/getMorePictures/' + category,
        type: 'GET',
        success: function (data) {
            console.log("here");
            console.log(data.data);

            for(var i = 0; i < data.data.length; i++) {
                //imgs[i].src = data.data[i];
                //console.log(imgs[i].src)
                var temp = i + 1;
                var elem = "<li class='pane" + temp + "'><div class='img'><img src='../" +  data.data[i] + "' style='height:100%;width:300px;max-width:100%;max-height:100%;'></div><div class='like'></div><div class='dislike'></div></li>";
                $('#tinderslide ul').prepend(elem);

            }
            $("#tinderslide").jTinder(options);

        }
    });

    console.log("here");
//    $("#tinderslide").data('plugin_jTinder').destroy();
//        //reinitialize new jTinder event


    console.log("reinitialiseibg");

}
