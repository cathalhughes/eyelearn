/**
 * jTinder initialization
 */

var modelLoc;
var answer;

async function loadModel() {
    model = await tf.loadFrozenModel(modelLoc + '/tensorflowjs_model.pb', modelLoc + '/weights_manifest.json');
    //model = await tf.loadFrozenModel('/modelData', '/manifestData');

}

function dispose() {
    if(model) {
        model.dispose();
    }
}

function modelPredict(input) {
    const preprocessedInput = tf.div(
        tf.sub(input.asType('float32'),  tf.scalar(255 / 2)),
        tf.scalar(255 / 2));
    const reshapedInput =
        preprocessedInput.reshape([1, ...preprocessedInput.shape]);
    const dict =  {};
    dict['input'] = reshapedInput;
    return model.execute(dict, 'final_result');
}

function getTopKClasses(predictions, topK) {
    const values = predictions.dataSync();
    predictions.dispose();

    let predictionList = [];
    for (let i = 0; i < values.length; i++) {
      predictionList.push({value: values[i], index: i});
    }
    predictionList = predictionList.sort((a, b) => {
      return b.value - a.value;
    }).slice(0, topK);

    return predictionList.map(x => {
      return {label: CLASSES[x.index], value: x.value};
    });
}

function warmUpModel() {
    modelPredict(
        tf.zeros([224, 224, 3]));
}

async function predict(imgElement) {

      const result = tf.tidy(() => {

          var img = tf.fromPixels(imgElement);
          const width = img.shape[0];
          const height = img.shape[1];
          console.log(width);
          console.log(height);
          // use the shorter side as the size to which we will crop
          const shorterSide = Math.min(img.shape[0], img.shape[1]);

          // calculate beginning and ending crop points
          const startingHeight = (height - shorterSide) / 2;
          const startingWidth = (width - shorterSide) / 2;
          const endingHeight = startingHeight + shorterSide;
          const endingWidth = startingWidth + shorterSide;
          var imageSliced = img.slice([startingWidth, startingHeight, 0], [endingWidth, endingHeight, 3])
          imageSliced = tf.image.resizeBilinear(imageSliced, [224, 224]);
          return modelPredict(imageSliced);
      });
      const topK = await getTopKClasses(result, Object.keys(CLASSES).length);

      console.log(topK[0].label);
      console.log(topK[1].label);
      return [topK[0].label, topK[1].label];
}

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
        //sendImage(item);
        console.log(item);
        //console.log(item.find('img'))
        var image = item.find('img')[0];
        predict(image).then(x => {
            if(x.includes(answer)) {
                var formInfo = document.forms['send'];
                formInfo.guess.value = answer;
                $('#send').trigger('submit');
            } else {
                var formInfo = document.forms['send'];
                formInfo.guess.value = x[0];
                $('#send').trigger('submit');
            }
        });
        //console.log(top);


    },
	animationRevertSpeed: 200,
	animationSpeed: 400,
	threshold: 1,
	likeSelector: '.like',
	dislikeSelector: '.dislike'
};






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

function startGame(loc, wrd) {
    modelLoc = loc;
    answer = wrd;
    Promise.all([
        loadModel().then(() => warmUpModel())
      ]).then(() => {

        addCards(category)

      }).catch(error => {
        console.log(error.message);
        console.log("Error in initilaising");

      });

    /**
     * Set button action to trigger jTinder like & dislike.
     */
    $('.actions .like, .actions .dislike').click(function(e){
        e.preventDefault();
        $("#tinderslide").jTinder($(this).attr('class'));
    });

}
