var model;
var topWord = "hello";
var answer = "test";
var language;
var loop;
var find;
var stop = false;

async function loadModel() {
    model = await tf.loadFrozenModel('static/find_model/tensorflowjs_model.pb', 'static/find_model/weights_manifest.json');

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

const cameraView = document.querySelector("#camera--view"),
    cameraOutput = document.querySelector("#camera--output"),
    cameraSensor = document.querySelector("#camera--sensor"),
    cameraTrigger = document.querySelector("#camera--trigger");

async function setupCamera() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      const stream = await navigator.mediaDevices.getUserMedia({
        'audio': false,
        'video': {facingMode: 'environment'}
      });
      //(<any>window).stream = stream;
      console.log("setUpCamera");
      cameraView.srcObject = stream;
      return new Promise(resolve => {
        cameraView.onloadedmetadata = () => {
          resolve([cameraView.videoWidth,
              cameraView.videoHeight]);
        };
      });
    }
    return null;
}

function setupVideoDimensions(width, height) {
    aspectRatio = width / height;
    console.log("dims");
    if (width >= height) {
      cameraView.height = 224;
      cameraView.width = aspectRatio * 224;
    } else {
      cameraView.width = 224;
      cameraView.height = 224 / aspectRatio;
    }
}

function snapshot() {
    cameraSensor.width = cameraView.videoWidth;
    cameraSensor.height = cameraView.videoHeight;
    cameraSensor.getContext("2d").drawImage(cameraView, 0, 0);
    cameraOutput.src = cameraSensor.toDataURL("image/webp");
    cameraOutput.classList.add("taken");
}

async function predict() {

      const result = tf.tidy(() => {

        // For UX reasons we spread the video element to 100% of the screen
        // but our traning data is trained against 244px images. Before we
        // send image data from the camera to the predict engine we slice a
        // 244 pixel area out of the center of the camera screen to ensure
        // better matching against our model.
        const pixels = tf.fromPixels(cameraView);
        const centerHeight = pixels.shape[0] / 2;
        const beginHeight = centerHeight - (224 / 2);
        const centerWidth = pixels.shape[1] / 2;
        const beginWidth = centerWidth - (224 / 2);
        const pixelsCropped =
              pixels.slice([beginHeight, beginWidth, 0],
                           [224, 224, 3]);

        return modelPredict(pixelsCropped);
      });

      if(stop == false) {
          const topK =
              await getTopKClasses(result, 10);
          speak(topK);



          loop = requestAnimationFrame(() => predict());
      }
}

function checkAnswer(answer, items) {
    for(i = 0; i < items.length; i++) {
    console.log(typeof answer);
        if(answer.trim() === items[i].label.trim()) {
            return true;
        }
    }
    return false;
}

//function speak(items) {
//    console.log(topWord);
//
//    if(isWordInList(topWord, items)) {
//        return null;
//    }
//    topWord = items[0].label;
//    var string = "I See ";
//    var labels = [];
//    for(i = 0; i < 5; i ++) {
//        labels.push(items[i].label);
//    }
//    responsiveVoice.cancel();
//    labels = labels.join(", ");
//    string += labels;
//    document.getElementById('machine-speechbubble-primary').innerHTML = string;
//    responsiveVoice.speak(string);
//}

function sendIncorrectGuess() {
    if(typeof incorrect !== 'undefined') {
        incorrect = "Nothing Found";
    }
    var formInfo = document.forms['send'];
    formInfo.guess.value = topWord;
    $('#send').trigger('submit');
}

function speak(items) {
    console.log(find);
    if(checkAnswer(find, items.slice(0, 5))) {
        if(language === "fr") {
            var correct = "Oh, je sais, c'est  " + find;
            responsiveVoice.cancel();
            responsiveVoice.speak(correct, "French Female");
        }
        else if(language === "es") {
            var correct = "Oh, lo sé, es  " + find;
            responsiveVoice.cancel();
            responsiveVoice.speak(correct, "Spanish Male");
        }
        cancelAnimationFrame(loop);
        stop = true;
        document.getElementById('machine-speechbubble-primary').innerHTML = correct;
        var formInfo = document.forms['send'];
        formInfo.guess.value = answer;
        $('#send').trigger('submit');
    }
    else {
        if(isWordInList(topWord, items)) {
            return null;
        }
        topWord = items[0].label;
        var labels = [];
        for(i = 0; i < 5; i ++) {
            labels.push(items[i].label);
        }
        responsiveVoice.cancel();
        if(language === "fr") {

            var string = "Je vois ";
            labels = labels.join(", ");
            string += labels;
            responsiveVoice.speak(string, "French Female");
        }

        else if(language === "es") {

            var string = "Veo ";
            labels = labels.join(", ");
            string += labels;
            responsiveVoice.speak(string, "Spanish Male");
        }
        document.getElementById('machine-speechbubble-primary').innerHTML = string;
    }
}

function isWordInList(word, items) {
    for(i = 0; i < items.length; i++) {
        if(items[i].label === word) {
            return true;
        }
    }
    return false;
}

//async function loadDict(modelNo, language) {
//    loc = 'static/find_model/class_names_' + language + '.txt'
//
//    await $.ajax({
//        url: loc,
//        dataType: 'text',
//    }).done(success);
//}
//
//function success(data) {
//    const lst = data.split(/\n/)
//    for (var i = 0; i < lst.length - 1; i++) {
//        let symbol = lst[i]
//        classNames[i] = symbol
//    }
//}

 function startGame(scramble, val, lang) {
      find = scramble;
      answer = val;
      language = lang;
      Promise.all([
        loadModel().then(() => warmUpModel()),
        setupCamera().then((value) => {
          setupVideoDimensions(value[0], value[1]);
        }),
      ]).then(values => {

        predict();

      }).catch(error => {
        console.log(error.message);
        console.log("Error in initilaising");

      });

}

