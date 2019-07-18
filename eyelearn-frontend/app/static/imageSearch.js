
function cells(count) {
  if (typeof count !== 'number' || count > 99) return false;

  var html = '',
      imageNum;

  for (i = 0; i < count; i++) {
    imageNum = Math.floor(Math.random() * 9) + 1;
    html += '<article class="image__cell is-collapsed">' +
	    '<div class="image--basic">' +
		        '<img id="expand-jump-'+i+'" class="basic__img" src="http://lorempixel.com/250/250/fashion/'+ imageNum +'" alt="Fashion '+ imageNum +'" />' +
	      '<div class="arrow--up"></div>' +
	  '</article>';
  }
  return html;
}

function updateImages(urls) {
  var html = '';

  for (i = 0; i < urls.length; i++) {
    html += '<article class="image__cell is-collapsed">' +
	    '<div class="image--basic">' +
		        '<img id="expand-jump-'+i+'" onclick="chooseImage(this.src)" class="basic__img" src=' + urls[i] +'>' +
	      '</a>' +
	      '<div class="arrow--up"></div>' +
	  '</article>';
  }
  return html;
}

function shuffle(a) {
    var j, x, i;
    for (i = a.length - 1; i > 0; i--) {
        j = Math.floor(Math.random() * (i + 1));
        x = a[i];
        a[i] = a[j];
        a[j] = x;
    }
    return a;
}

function displayFindMeConfig(urls) {
  var html = '';
  shuffle(urls);
  for (i = 0; i < urls.length; i++) {
    html += '<article class="image__cell is-collapsed"  style="width:20%;height:33%;">' +
	    '<div class="image--basic" >' +
		        '<img id="expand-jump-'+i+'" class="basic__img" style="width:100%;height:95%;" src=' + urls[i] +'>' +

	      '<div class="arrow--up"></div>' + '</div></div>' +
	  '</article>';
  }
   $('.image-grid').empty().html(html);
}

function chooseImage(src) {
    var item = $("#sel1").find(":selected").text().trim();
    game_data[item] = src;
    console.log(game_data);
    var keys = Object.keys(game_data);
    var strKeys = [];
        for(i = 0; i < keys.length; i++) {
            strKeys.push("<a href='#' onclick='removeItem(this)'>" + keys[i] + "</a>");
        }
        strKeys = strKeys.join(",")
    var size = Object.keys(game_data).length;
    $('.image-grid').empty().html("<h1>You currently have chosen " + size + " (" + strKeys + ") items!</h1><h1>Click on an item to remove it.</h1><button id='submit' class='btn btn-success' onclick='submitConfig()'>Submit</button><button id='submit' class='btn btn-danger' onclick='clearConfig()'>Clear Configuration</button>");


}

function submitConfig() {

    var formInfo = document.forms['configForm'];
    formInfo.config.value = JSON.stringify(game_data);
    $('#configForm').trigger('submit');
}

function loadPageFromPreviousConfig(config) {

    if($.isEmptyObject(config) === false) {
        game_data = config;
        var keys = Object.keys(game_data);
        var strKeys = [];
        for(i = 0; i < keys.length; i++) {
            strKeys.push("<a href='#' onclick='removeItem(this)'>" + keys[i] + "</a>");
        }
        strKeys = strKeys.join(",")


        var size = Object.keys(game_data).length;
        $('.image-grid').empty().html("<h1>Here is your previous configuration:</h1><h1>You currently have chosen " + size + " (" + strKeys + ") items!</h1><h1>Click on an item to remove it.</h1><button id='submit' class='btn btn-success' onclick='submitConfig()'>Submit</button><button id='submit' class='btn btn-danger' onclick='clearConfig()'>Clear Configuration</button>");
    }

}

function removeItem(obj) {
     var category = $(obj).text();
     delete game_data[category];
     console.log(game_data)
     if($.isEmptyObject(game_data) === true) {
        $('.image-grid').empty().html("<h1>Your configuration is empty!</h1>");
     }
     else {
        var keys = Object.keys(game_data);
        var strKeys = [];
        for(i = 0; i < keys.length; i++) {
            strKeys.push("<a href='#' onclick='removeItem(this)'>" + keys[i] + "</a>");
        }
        strKeys = strKeys.join(",")
        var size = Object.keys(game_data).length;
        $('.image-grid').empty().html("<h1>You currently have chosen " + size + " (" + strKeys + ") items!</h1><h1>Click on an item to remove it.</h1><button id='submit' class='btn btn-success' onclick='submitConfig()'>Submit</button><button id='submit' class='btn btn-danger' onclick='clearConfig()'>Clear Configuration</button>");
    }
}


function clearConfig() {
    game_data = {};
    $('.image-grid').empty().html("<h1>You have successfully cleared your configuration!</h1>");

}

function getImagesForSelection(selection) {
    console.log("in post");
    data = {'search_term':selection};
    data = JSON.stringify(data);
    $.ajax({
        type: "POST",
        url: "/searchForImages",
        data: data,
        success: function(data){
            var urls = data["image_urls"];
            $('.image-grid').empty().html(updateImages(urls));


        },
        error: function(xhr, status, error) {
             console.log(status);
        }
    });

}

function httpGet(url, callback) {
    // this function gets the contents of the URL. Once the
    // content is present it runs the callback function.
    var xmlhttp=new XMLHttpRequest();
    xmlhttp.onreadystatechange=function() {
        if (xmlhttp.readyState==4 && xmlhttp.status==200) {
            callback(xmlhttp.responseText);
        }
    }
    xmlhttp.open("GET", url, false );
    xmlhttp.send();
}

var array;

var game_data = {};

httpGet("../static/find_model/classes.txt", function(textFile){
    // this calls the httpGet function with the URL of your text
    // file. It then runs a function that turns the file into an
    // array.
    array = textFile.split("\n");
    console.log(array);
});


$.each(array, function(key, value) {
     $('#sel1')
         .append($("<option></option>")
                    .attr("value",key)
                    .text(value));
});

$('#sel1').change(function() {
   getImagesForSelection($(this).find(":selected").text());


});






