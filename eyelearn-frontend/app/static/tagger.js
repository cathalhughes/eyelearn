// default options
var options = {
    'text': 'Franz jagt im komplett verwahrlosten Taxi quer durch Bayern.'
}


// initialize page (bind events etc.)
function init() {
    $('#tagTipContainer').hide();

    $('#submit').bind('click', tag);
    $('#edit').bind('click', edit);
    $(window).bind('resize', function() { $('#tagTipContainer').hide(); });
    $('#tagTipContainer').bind('click', function() { $('#tagTipContainer').hide(); });

}

// Start editing
function edit() {
    $('#form').removeClass('mode-view').addClass('mode-edit');
    $('#tagTipContainer').hide();
}

// Start tagging
function tag() {
    $('#spinner').show();
    var text = $('#text').val();
    text = text.replace('»', '"');
    text = text.replace('«', '"');

    // No proxy when developing (.*local.* in host)
    var url = "https://postagger.eyelearn.club/getPhraseTranslation1"
    console.log(language);
    $.ajax({
        url: url,
        type: "POST",
        data: {"phrase": text, "language": language},
        success: callback
    });
    return false;
}

// Tagging finished - process response
function callback(data) {

    var tagMap = appData.tagMap;
    var color = appData.colors;

    $('#form').removeClass('mode-edit').addClass('mode-view');
    $('#tagTipContainer').hide();

    var words = data.taggedText;
    var taggedHTML = "";
    var lastWord = "";
    $.each(words, function(index, taggedWord) {
        var tag = taggedWord.substring(taggedWord.lastIndexOf("_") + 1);
        var word = taggedWord.substring(0, taggedWord.lastIndexOf("_"));
        word = word.replace("\\/", "/");
        word = word.replace("-LRB-", "(");
        word = word.replace("-RRB-", ")");
        // TODO: are there other symbols?
        if (tag != '$,' && tag != '$.' && lastWord != '``' && word != '\'\'' && word != ')' && lastWord != '(') {
            taggedHTML += ' ';
        }
        lastWord = word;
        word = word.replace('``', '"');
        word = word.replace('\'\'', '"');
        if (word == '"') {
            tag = '';
        }
	// TODO: escape html
        if (tagMap[tag] != undefined && color[tagMap[tag][0]] != undefined) {
            taggedHTML += '<span class="taggedWord" style="background-color: ' + color[tagMap[tag][0]] + '">' + word + '<span>' + tag + '</span></span>';
        }
        else if(tag === "NEWLINE") {
            taggedHTML += '<br/>';
        }
        else {
            taggedHTML += '<span class="taggedWord">' + word + '<span>' + tag + '</span></span>';
        }
    });
    $('#textTagged').html(taggedHTML);

    $('.taggedWord').bind('click mouseover', function(ev) {
        var word = $(ev.target);
        var tagName = word.find('span').first().html();
        if (tagName == "" || tagMap[tagName] == undefined) {
            return; // cancel if tag not defined
        }
        $('#tagTipContainer').show();
        if (tagMap[tagName][0] != "" ) {
	    // TODO: translate
	    var infoHtml = '<b>' + tagMap[tagName][0] + '</b>, ' + tagName;
	    if (tagMap[tagName][1] != '') {
	        infoHtml += '<br />(' + tagMap[tagName][1] + ')';
	    }
	    if (tagMap[tagName][2] != '') {
	        infoHtml += "<br />" + appData.clientStrings['label_examples'] + " " + tagMap[tagName][2];
            }
            $('#tagTip').html(infoHtml);
        }
        else {
            $('#tagTip').html(tagName + ': ' + tagMap[tagName][1]);
        }
        $('#tagTipContainer').css('background-color', color[tagMap[tagName][0]] != undefined ? color[tagMap[tagName][0]] : '#fff');
        $('#tagTipContainer').offset({'left': word.offset().left});
        $('#tagTipContainer').offset({'top': word.offset().top + word.outerHeight()});
        $('#tagTipContainer .up').offset({'left': word.offset().left + word.outerWidth() / 2 - $('#tagTipContainer .up').outerWidth() / 2});
    });
    $('.taggedWord').bind('mouseout', function(ev) {
        $('#tagTipContainer').hide();
    });

}

function showTags() {
    $('.taggedWord span').show();
}

function hideTags() {
    $('.taggedWord span').hide();
}

function refreshHref() {
    document.location.href = "#" + $.toJSON(options);
}

$(window).on('load', init);

