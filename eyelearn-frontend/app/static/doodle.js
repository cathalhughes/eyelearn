/*
variables
*/
var model;
var canvas;
var classNames = [];
var canvas;
var coords = [];
var mousePressed = false;
var mode;
var word;
var modelNo;
var language;
var incorrect;
var answer;

/*
prepare the drawing canvas
*/
$(function() {
    canvas = window._canvas = new fabric.Canvas('canvas');
    canvas.backgroundColor = '#ffffff';
    canvas.setHeight(window.innerHeight -  200);
    canvas.setWidth(window.innerWidth);
    canvas.isDrawingMode = 0;
    canvas.freeDrawingBrush.color = "black";
    canvas.freeDrawingBrush.width = 10;
    canvas.renderAll();
    //setup listeners
    canvas.on('mouse:up', function(e) {
        getFrame();
        mousePressed = false
    });
    canvas.on('mouse:down', function(e) {
        mousePressed = true
    });
    canvas.on('mouse:move', function(e) {
        recordCoor(e)
    });
})

/*
set the table of the predictions
*/
function setTable(top5, probs) {
    //loop over the predictions
    for (var i = 0; i < top5.length; i++) {
        let sym = document.getElementById('sym' + (i + 1))
        let prob = document.getElementById('prob' + (i + 1))
        sym.innerHTML = top5[i]
        prob.innerHTML = Math.round(probs[i] * 100)
    }
    //create the pie
    createPie(".pieID.legend", ".pieID.pie");

}

function sendIncorrectGuess() {
    if(typeof incorrect === 'undefined') {
        incorrect = "Nothing Doodled";
    }
    saveDoodle(incorrect); //new
    var formInfo = document.forms['send'];
    formInfo.guess.value = incorrect;
    $('#send').trigger('submit');
}

function saveDoodle(guess) {
    console.log("in post");
    var canvasObj = document.getElementById("canvas");
    var img = canvasObj.toDataURL();
    console.log(img);
    data = {'doodle':img, "answer":answer, "guess":guess};
    data = JSON.stringify(data);
    $.ajax({
        type: "POST",
        url: "/saveDoodle",
        data: data,
        success: function(data){
            console.log(data);

        },
        error: function(xhr, status, error) {
             console.log(status);
        }
    });
}

function speak(top5, probs) {
    responsiveVoice.cancel();
    var words = []
    for (var i = 0; i < top5.length; i++) {
        words.push(top5[i].split("_").join(" "));

    }

    if(isWordInList(words, word)) {
        if(language === "fr") {
            var correct = "Oh, je sais, c'est  " + word;
            document.getElementById('machine-speechbubble-primary').innerHTML = correct;
            responsiveVoice.speak(correct, "French Female");
        }
        else if(language === "es") {
            var correct = "Oh, lo sé  " + word;
            document.getElementById('machine-speechbubble-primary').innerHTML = correct;
            responsiveVoice.speak(correct, "Spanish Male");
        }
        var formInfo = document.forms['send'];
        formInfo.guess.value = answer;
        saveDoodle(word);
        $('#send').trigger('submit');
    }
    else {
        incorrect = words[0];
        if(language === "fr") {

            var string = "Je vois ";
            wordsString = words.join(",");
            string += words;
            document.getElementById('machine-speechbubble-primary').innerHTML = string;
            responsiveVoice.speak(string, "French Female");
        }
        else if(language === "es") {

            var string = "Veo ";
            wordsString = words.join(",");
            string += words;
            document.getElementById('machine-speechbubble-primary').innerHTML = string;
            responsiveVoice.speak(string, "Spanish Male");
        }
    }
}

function isWordInList(words, word) {
    for(i = 0; i < words.length; i ++) {
        if(words[i].trim() === word.trim()) {
            return true;
        }
    }
    return false;
}

/*
record the current drawing coordinates
*/
function recordCoor(event) {
    var pointer = canvas.getPointer(event.e);
    var posX = pointer.x;
    var posY = pointer.y;

    if (posX >= 0 && posY >= 0 && mousePressed) {
        coords.push(pointer)
    }
}

/*
get the best bounding box by trimming around the drawing
*/
function getMinBox() {
    //get coordinates
    var coorX = coords.map(function(p) {
        return p.x
    });
    var coorY = coords.map(function(p) {
        return p.y
    });

    //find top left and bottom right corners
    var min_coords = {
        x: Math.min.apply(null, coorX),
        y: Math.min.apply(null, coorY)
    }
    var max_coords = {
        x: Math.max.apply(null, coorX),
        y: Math.max.apply(null, coorY)
    }

    //return as strucut
    return {
        min: min_coords,
        max: max_coords
    }
}

/*
get the current image data
*/
function getImageData() {
        //get the minimum bounding box around the drawing
        const mbb = getMinBox()

        //get image data according to dpi
        const dpi = window.devicePixelRatio
        const imgData = canvas.contextContainer.getImageData(mbb.min.x * dpi, mbb.min.y * dpi,
                                                      (mbb.max.x - mbb.min.x) * dpi, (mbb.max.y - mbb.min.y) * dpi);
        return imgData
    }

/*
get the prediction
*/
function getFrame() {
    //make sure we have at least two recorded coordinates
    if (coords.length >= 2) {

        //get the image data from the canvas
        const imgData = getImageData()

        //get the prediction
        const pred = model.predict(preprocess(imgData)).dataSync()

        //find the top 5 predictions
        const indices = findIndicesOfMax(pred, 5)
        const probs = findTopValues(pred, 5)
        const names = getClassNames(indices)

        //Display and speak the results
        speak(names, probs)
    }

}

/*
get the the class names
*/
function getClassNames(indices) {
    var outp = []
    for (var i = 0; i < indices.length; i++)
        outp[i] = classNames[indices[i]]
    return outp
}

/*
load the class names
*/
async function loadDict(modelNo, language) {
    if (mode == 'ar')
        loc = 'static/model/class_names_ar.txt'
    else
        loc = 'static/model' + modelNo + '/class_names_' + language + '.txt'

    await $.ajax({
        url: loc,
        dataType: 'text',
    }).done(success);
}

/*
load the class names
*/
function success(data) {
    const lst = data.split(/\n/)
    for (var i = 0; i < lst.length - 1; i++) {
        let symbol = lst[i]
        classNames[i] = symbol
    }
}

/*
get indices of the top probs
*/
function findIndicesOfMax(inp, count) {
    var outp = [];
    for (var i = 0; i < inp.length; i++) {
        outp.push(i); // add index to output array
        if (outp.length > count) {
            outp.sort(function(a, b) {
                return inp[b] - inp[a];
            }); // descending sort the output array
            outp.pop(); // remove the last index (index of smallest element in output array)
        }
    }
    return outp;
}

/*
find the top 5 predictions
*/
function findTopValues(inp, count) {
    var outp = [];
    let indices = findIndicesOfMax(inp, count)
    // show 5 greatest scores
    for (var i = 0; i < indices.length; i++)
        outp[i] = inp[indices[i]]
    return outp
}

/*
preprocess the data
*/
function preprocess(imgData) {
    return tf.tidy(() => {
        //convert to a tensor
        let tensor = tf.fromPixels(imgData, numChannels = 1)

        //resize
        const resized = tf.image.resizeBilinear(tensor, [28, 28]).toFloat()

        //normalize
        const offset = tf.scalar(255.0);
        const normalized = tf.scalar(1.0).sub(resized.div(offset));

        //We add a dimension to get a batch shape
        const batched = normalized.expandDims(0)
        return batched
    })
}

/*
load the model
*/
async function start(cur_mode, word1, modelNo1, language1, answer1) {
    //arabic or english
    mode = cur_mode
    modelNo = modelNo1
    language = language1
    answer = answer1


    word = word1

    //load the model
    model = await tf.loadModel('static/model' + modelNo + '/model.json')

    //warm up
    model.predict(tf.zeros([1, 28, 28, 1]))

    //allow drawing on the canvas
    allowDrawing()

    //load the class names
    await loadDict(modelNo, language)
}

/*
allow drawing on canvas
*/
function allowDrawing() {
    canvas.isDrawingMode = 1;
//    if (mode == 'en')
//        document.getElementById('status').innerHTML = 'Model Loaded';
//    else
//        document.getElementById('status').innerHTML = 'تم التحميل';
//    $('button').prop('disabled', false);
//    var slider = document.getElementById('myRange');
//    slider.oninput = function() {
//        canvas.freeDrawingBrush.width = this.value;
//    };
}

/*
clear the canvs
*/
function erase() {
    canvas.clear();
    canvas.backgroundColor = '#ffffff';
    coords = [];
}

module.exports = {
    isWordInList: isWordInList,
    getClassNames: getClassNames,
    loadDict: loadDict,
    start: start

}